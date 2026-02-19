import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from prompts import build_cover_letter_prompt
from llm_client_gemini import generate_text
from json_to_md import json_to_md

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Project layout:
# Cover-letter-gen/
#   backend/
#   templates/
#   data/
#     profiles/
#       <profile_name>/
#         resume.md
#         job_description.txt
#         cover_letters/
#           2026-02-18_google.md

TEMPLATES_DIR = (Path(__file__).parent.parent / "templates").resolve()
DATA_DIR      = (Path(__file__).parent.parent / "data").resolve()
PROFILES_DIR  = (DATA_DIR / "profiles").resolve()


def _read_file_or_raise(path: Path) -> str:
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Missing file: {path}")
    return path.read_text(encoding="utf-8", errors="ignore")


def _get_profile_dir(profile: str) -> Path:
    profile_dir = (PROFILES_DIR / profile).resolve()
    if not profile_dir.exists() or not profile_dir.is_dir():
        available = [p.name for p in PROFILES_DIR.iterdir() if p.is_dir()] if PROFILES_DIR.exists() else []
        raise HTTPException(
            status_code=400,
            detail=f"Profile '{profile}' not found. Available: {available}"
        )
    return profile_dir


class GenerateReq(BaseModel):
    profile: str                        # folder name under data/profiles/
    company: str                        # used for output filename
    style: str = "impact"
    model: str = "gemini-2.5-flash"
    temperature: float = 0.35


# ── Profiles ────────────────────────────────────────────────────────────────

@app.get("/api/profiles")
def list_profiles():
    """Return all profile names found under data/profiles/"""
    if not PROFILES_DIR.exists():
        return {"profiles": []}
    profiles = sorted([p.name for p in PROFILES_DIR.iterdir() if p.is_dir()])
    return {"profiles": profiles}


@app.get("/api/profiles/{profile}")
def get_profile(profile: str):
    """Return metadata + cover letter history for a profile"""
    profile_dir = _get_profile_dir(profile)
    cl_dir = profile_dir / "cover_letters"

    history = []
    if cl_dir.exists():
        for f in sorted(cl_dir.glob("*.md"), reverse=True):
            history.append({
                "filename": f.name,
                "created": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                "size": f.stat().st_size,
            })

    return {
        "profile": profile,
        "has_resume": (profile_dir / "resume.md").exists(),
        "has_jd": (profile_dir / "job_description.txt").exists(),
        "cover_letters": history,
    }


@app.get("/api/profiles/{profile}/cover_letters/{filename}")
def get_cover_letter(profile: str, filename: str):
    """Fetch the content of a saved cover letter"""
    profile_dir = _get_profile_dir(profile)
    cl_path = (profile_dir / "cover_letters" / filename).resolve()

    # Safety: ensure the resolved path is still inside the profile dir
    if not str(cl_path).startswith(str(profile_dir)):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not cl_path.exists():
        raise HTTPException(status_code=404, detail=f"Cover letter not found: {filename}")

    return {"filename": filename, "md": cl_path.read_text(encoding="utf-8")}


# ── Styles ───────────────────────────────────────────────────────────────────

@app.get("/api/styles")
def styles():
    style_keys = sorted([p.stem.replace("style_", "") for p in TEMPLATES_DIR.glob("style_*.txt")])
    return {"styles": style_keys}


# ── Generate ─────────────────────────────────────────────────────────────────

@app.post("/api/generate")
def generate(req: GenerateReq):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Missing GEMINI_API_KEY (check backend/.env)")

    profile_dir = _get_profile_dir(req.profile)

    resume_md = _read_file_or_raise(profile_dir / "resume.md")
    jd_text   = _read_file_or_raise(profile_dir / "job_description.txt")

    style_file = (TEMPLATES_DIR / f"style_{req.style}.txt").resolve()
    if not style_file.exists():
        available = sorted([p.stem.replace("style_", "") for p in TEMPLATES_DIR.glob("style_*.txt")])
        raise HTTPException(status_code=400, detail=f"Invalid style. Available: {available}")

    style_hint = style_file.read_text(encoding="utf-8", errors="ignore")
    prompt     = build_cover_letter_prompt(resume_md, jd_text, style_hint)

    print(f"=== GENERATE ===")
    print(f"Profile:  {req.profile}")
    print(f"Company:  {req.company}")
    print(f"Style:    {req.style}")
    print(f"Model:    {req.model}")
    print(f"Resume:   {len(resume_md)} chars")
    print(f"JD:       {len(jd_text)} chars")
    print(f"================")

    try:
        json_response = generate_text(prompt, model_name=req.model, temperature=req.temperature)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        md = json_to_md(json_response)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse API response as JSON: {str(e)}. Raw: {json_response[:200]}..."
        )

    # Save to data/profiles/<profile>/cover_letters/<date>_<company>.md
    date_str    = datetime.now().strftime("%Y-%m-%d")
    safe_company = req.company.strip().lower().replace(" ", "_")
    filename    = f"{date_str}_{safe_company}.md"

    cl_dir = profile_dir / "cover_letters"
    cl_dir.mkdir(parents=True, exist_ok=True)

    # If filename already exists, append a counter to avoid overwriting
    final_path = cl_dir / filename
    counter = 1
    while final_path.exists():
        filename   = f"{date_str}_{safe_company}_{counter}.md"
        final_path = cl_dir / filename
        counter   += 1

    final_path.write_text(md, encoding="utf-8")

    return {
        "md":       md,
        "profile":  req.profile,
        "company":  req.company,
        "filename": filename,
        "file_path": str(final_path),
    }


# ── Debug ─────────────────────────────────────────────────────────────────────

@app.get("/api/debug")
def debug():
    profiles = []
    if PROFILES_DIR.exists():
        for p in sorted(PROFILES_DIR.iterdir()):
            if p.is_dir():
                profiles.append({
                    "name": p.name,
                    "has_resume": (p / "resume.md").exists(),
                    "has_jd":     (p / "job_description.txt").exists(),
                })
    return {
        "data_dir":     str(DATA_DIR),
        "profiles_dir": str(PROFILES_DIR),
        "profiles":     profiles,
    }