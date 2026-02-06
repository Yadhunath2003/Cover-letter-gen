import os
import tempfile
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from prompts import build_cover_letter_prompt
from llm_client_gemini import generate_text
from export_pdf import md_to_pdf

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

    # Option A: send text directly (Swagger paste)
    resume_md: Optional[str] = None
    jd_text: Optional[str] = None


    # read from /data folder by filename
    resume_file: str = "resume.md"
    jd_file: str = "job_description.txt"

    # Style must match templates/style_<style>.txt
    style: str = "impact"

    # Model + generation
    model: str = "gemini-1.5-flash"
    temperature: float = 0.35


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

@app.post("/api/generate")
def generate(req: GenerateReq):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Missing GEMINI_API_KEY (check backend/.env)")

    # Load resume + JD (prefer request body, otherwise read from /data)
    resume_md = (req.resume_md or "").strip()
    jd_text = (req.jd_text or "").strip()

    if not resume_md:
        resume_md = _read_file_or_raise((DATA_DIR / req.resume_file).resolve())

    if not jd_text:
        jd_text = _read_file_or_raise((DATA_DIR / req.jd_file).resolve())

    # Load style hint
    style_file = (TEMPLATES_DIR / f"style_{req.style}.txt").resolve()
    if not style_file.exists():
        available = sorted([p.stem.replace("style_", "") for p in TEMPLATES_DIR.glob("style_*.txt")])
        raise HTTPException(status_code=400, detail=f"Invalid style. Available: {available}")

    style_hint = style_file.read_text(encoding="utf-8", errors="ignore")

    # Build prompt
    prompt = build_cover_letter_prompt(resume_md, jd_text, style_hint)

    # Generate
    try:
        md = generate_text(prompt, model_name=req.model, temperature=req.temperature)
    except Exception as e:
        # Show the real Gemini error in Swagger instead of generic 500
        raise HTTPException(status_code=500, detail=str(e))

    return {"md": md}


class PdfReq(BaseModel):
    md_text: str


@app.post("/api/pdf")
def pdf(req: PdfReq):
    with tempfile.TemporaryDirectory() as td:
        out_pdf = Path(td) / "coverletter.pdf"
        md_to_pdf(req.md_text, out_pdf)
        pdf_bytes = out_pdf.read_bytes()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=coverletter.pdf"},
    )