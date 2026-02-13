import os
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

# Allow local frontend calls (optional but helpful)
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
TEMPLATES_DIR = (Path(__file__).parent.parent / "templates").resolve()
DATA_DIR = (Path(__file__).parent.parent / "data").resolve()


def _read_file_or_raise(path: Path) -> str:
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Missing file: {path}")
    return path.read_text(encoding="utf-8", errors="ignore")


class GenerateReq(BaseModel):
    # Style must match templates/style_<style>.txt
    style: str = "impact"

    # Model + generation
    model: str = "gemini-2.5-flash"
    temperature: float = 0.35

    # Files to read from /data folder
    resume_file: str = "resume.md"
    jd_file: str = "job_description.txt"


@app.get("/api/styles")
def styles():
    files = sorted([p.name for p in TEMPLATES_DIR.glob("style_*.txt")])
    style_keys = sorted([p.stem.replace("style_", "") for p in TEMPLATES_DIR.glob("style_*.txt")])
    return {
        "templates_dir": str(TEMPLATES_DIR),
        "files": files,
        "styles": style_keys,
        "data_dir": str(DATA_DIR),
    }

@app.get("/api/models")
def models():
    from google import genai
    import os

    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    out = []
    for m in client.models.list():
        out.append(m.name)
    return {"models": out}

@app.get("/api/debug-data")
def debug_data():
    """Debug endpoint to verify data files are being read correctly"""
    resume_path = (DATA_DIR / "resume.md").resolve()
    jd_path = (DATA_DIR / "job_description.txt").resolve()

    return {
        "data_dir": str(DATA_DIR),
        "resume_path": str(resume_path),
        "resume_exists": resume_path.exists(),
        "resume_size": resume_path.stat().st_size if resume_path.exists() else 0,
        "resume_preview": resume_path.read_text(encoding="utf-8")[:200] if resume_path.exists() else "",
        "jd_path": str(jd_path),
        "jd_exists": jd_path.exists(),
        "jd_size": jd_path.stat().st_size if jd_path.exists() else 0,
        "jd_preview": jd_path.read_text(encoding="utf-8")[:200] if jd_path.exists() else "",
    }

@app.post("/api/generate")
def generate(req: GenerateReq):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Missing GEMINI_API_KEY (check backend/.env)")

    # Always read from data folder
    resume_md = _read_file_or_raise((DATA_DIR / req.resume_file).resolve())
    jd_text = _read_file_or_raise((DATA_DIR / req.jd_file).resolve())

    # Load style hint
    style_file = (TEMPLATES_DIR / f"style_{req.style}.txt").resolve()
    if not style_file.exists():
        available = sorted([p.stem.replace("style_", "") for p in TEMPLATES_DIR.glob("style_*.txt")])
        raise HTTPException(status_code=400, detail=f"Invalid style. Available: {available}")

    style_hint = style_file.read_text(encoding="utf-8", errors="ignore")

    # Build prompt
    prompt = build_cover_letter_prompt(resume_md, jd_text, style_hint)

    # Debug: Print to console to verify data is being used
    print(f"=== DEBUG INFO ===")
    print(f"Resume length: {len(resume_md)} chars")
    print(f"JD length: {len(jd_text)} chars")
    print(f"Style: {req.style}")
    print(f"Model: {req.model}")
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Resume preview: {resume_md[:100]}...")
    print(f"==================")

    # Generate
    try:
        json_response = generate_text(prompt, model_name=req.model, temperature=req.temperature)
    except Exception as e:
        # Show the real Gemini error in Swagger instead of generic 500
        raise HTTPException(status_code=500, detail=str(e))

    # Parse JSON and convert to Markdown
    try:
        md = json_to_md(json_response)
    except Exception as e:
        # If JSON parsing fails, return error with raw response for debugging
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse API response as JSON: {str(e)}. Raw response: {json_response[:200]}..."
        )

    # Save markdown to data folder
    md_filename = "cover_letter.md"
    md_path = (DATA_DIR / md_filename).resolve()
    md_path.write_text(md, encoding="utf-8")

    return {"md": md, "file_path": str(md_path), "filename": md_filename}