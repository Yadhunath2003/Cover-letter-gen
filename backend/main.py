import os
import tempfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from prompts import build_cover_letter_prompt
from llm_client_gemini import generate_text
from json_to_md import json_to_md
try:
    from md_to_pdf import md_to_html, md_to_pdf
    PDF_AVAILABLE = True
except ImportError as e:
    print(f"⚠ PDF features disabled: {e}. Run: pip install pdfkit")
    PDF_AVAILABLE = False

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


# ── Request Models ────────────────────────────────────────────────────────────

class GenerateReq(BaseModel):
    profile: str
    company: str
    style: str = "impact"
    model: str = "gemini-2.5-flash"
    temperature: float = 0.35

class PdfReq(BaseModel):
    md_text: str

class PreviewReq(BaseModel):
    md_text: str


# ── Profiles ──────────────────────────────────────────────────────────────────

@app.get("/api/profiles")
def list_profiles():
    if not PROFILES_DIR.exists():
        return {"profiles": []}
    profiles = sorted([p.name for p in PROFILES_DIR.iterdir() if p.is_dir()])
    return {"profiles": profiles}


@app.get("/api/profiles/{profile}")
def get_profile(profile: str):
    profile_dir = _get_profile_dir(profile)
    cl_dir = profile_dir / "cover_letters"

    history = []
    if cl_dir.exists():
        for f in sorted(cl_dir.glob("*.md"), reverse=True):
            history.append({
                "filename": f.name,
                "created":  datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                "size":     f.stat().st_size,
            })

    return {
        "profile":       profile,
        "has_resume":    (profile_dir / "resume.md").exists(),
        "has_jd":        (profile_dir / "job_description.txt").exists(),
        "cover_letters": history,
    }


@app.get("/api/profiles/{profile}/cover_letters/{filename}")
def get_cover_letter(profile: str, filename: str):
    profile_dir = _get_profile_dir(profile)
    cl_path = (profile_dir / "cover_letters" / filename).resolve()

    if not str(cl_path).startswith(str(profile_dir)):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not cl_path.exists():
        raise HTTPException(status_code=404, detail=f"Cover letter not found: {filename}")

    return {"filename": filename, "md": cl_path.read_text(encoding="utf-8")}


@app.delete("/api/profiles/{profile}/cover_letters/{filename}")
def delete_cover_letter(profile: str, filename: str):
    profile_dir = _get_profile_dir(profile)
    cl_path = (profile_dir / "cover_letters" / filename).resolve()

    if not str(cl_path).startswith(str(profile_dir)):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not cl_path.exists():
        raise HTTPException(status_code=404, detail=f"Cover letter not found: {filename}")

    try:
        cl_path.unlink()
        return {"deleted": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


# ── Styles ────────────────────────────────────────────────────────────────────

@app.get("/api/styles")
def styles():
    style_keys = sorted([p.stem.replace("style_", "") for p in TEMPLATES_DIR.glob("style_*.txt")])
    return {"styles": style_keys}


# ── Generate ──────────────────────────────────────────────────────────────────

@app.post("/api/generate")
def generate(req: GenerateReq):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Missing GEMINI_API_KEY (check backend/.env)")

    profile_dir = _get_profile_dir(req.profile)
    resume_md   = _read_file_or_raise(profile_dir / "resume.md")
    jd_text     = _read_file_or_raise(profile_dir / "job_description.txt")

    style_file = (TEMPLATES_DIR / f"style_{req.style}.txt").resolve()
    if not style_file.exists():
        available = sorted([p.stem.replace("style_", "") for p in TEMPLATES_DIR.glob("style_*.txt")])
        raise HTTPException(status_code=400, detail=f"Invalid style. Available: {available}")

    style_hint = style_file.read_text(encoding="utf-8", errors="ignore")
    prompt     = build_cover_letter_prompt(resume_md, jd_text, style_hint)

    print(f"=== GENERATE ===")
    print(f"Profile: {req.profile} | Company: {req.company} | Style: {req.style} | Model: {req.model}")
    print(f"Resume: {len(resume_md)} chars | JD: {len(jd_text)} chars")
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

    # Save timestamped file — never overwrite
    date_str     = datetime.now().strftime("%Y-%m-%d")
    safe_company = req.company.strip().lower().replace(" ", "_")
    filename     = f"{date_str}_{safe_company}.md"

    cl_dir = profile_dir / "cover_letters"
    cl_dir.mkdir(parents=True, exist_ok=True)

    final_path = cl_dir / filename
    counter = 1
    while final_path.exists():
        filename   = f"{date_str}_{safe_company}_{counter}.md"
        final_path = cl_dir / filename
        counter   += 1

    final_path.write_text(md, encoding="utf-8")

    return {
        "md":        md,
        "profile":   req.profile,
        "company":   req.company,
        "filename":  filename,
        "file_path": str(final_path),
    }


# ── Preview (MD → styled HTML) ────────────────────────────────────────────────

@app.post("/api/preview")
def preview(req: PreviewReq):
    """Convert markdown to styled HTML for live iframe preview."""
    if not PDF_AVAILABLE:
        raise HTTPException(status_code=503, detail="pdfkit not installed. Run: pip install pdfkit")
    try:
        html = md_to_html(req.md_text)
        return HTMLResponse(content=html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── PDF ───────────────────────────────────────────────────────────────────────

@app.post("/api/pdf")
def generate_pdf(req: PdfReq):
    """Convert markdown cover letter to styled PDF."""
    if not PDF_AVAILABLE:
        raise HTTPException(status_code=503, detail="pdfkit not installed. Run: pip install pdfkit")
    if not req.md_text.strip():
        raise HTTPException(status_code=400, detail="md_text is empty")

    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name

        md_to_pdf(req.md_text, tmp_path)

        return FileResponse(
            path=tmp_path,
            media_type="application/pdf",
            filename="cover_letter.pdf",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


# ── Debug ─────────────────────────────────────────────────────────────────────

@app.get("/api/debug")
def debug():
    profiles = []
    if PROFILES_DIR.exists():
        for p in sorted(PROFILES_DIR.iterdir()):
            if p.is_dir():
                profiles.append({
                    "name":       p.name,
                    "has_resume": (p / "resume.md").exists(),
                    "has_jd":     (p / "job_description.txt").exists(),
                })
    return {
        "data_dir":     str(DATA_DIR),
        "profiles_dir": str(PROFILES_DIR),
        "profiles":     profiles,
    }