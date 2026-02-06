from pathlib import Path
import re
from ..backend.llm_client_gemini import generate_text
from ..backend.prompts import build_cover_letter_prompt

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def generate_variants(md_resume_path: Path, jd_path: Path, templates_dir: Path, model="gemini-1.5-flash"):
    md_resume = read_text(md_resume_path)
    jd = read_text(jd_path)

    style_files = sorted(templates_dir.glob("style_*.txt"))
    variants = []
    for sf in style_files:
        style_hint = read_text(sf)
        prompt = build_cover_letter_prompt(md_resume, jd, style_hint)
        out = generate_text(prompt, model_name=model, temperature=0.35)
        variants.append((sf.stem, out))
    return variants

# super-simple selector: prefer more JD keyword overlap (only stdlib)
def choose_best(variants: list[tuple[str, str]], jd_text: str) -> tuple[str, str]:
    wordset = set(re.findall(r"[A-Za-z0-9][A-Za-z0-9+\-_/]{2,}", jd_text.lower()))
    def score(md: str) -> int:
        words = set(re.findall(r"[A-Za-z0-9][A-Za-z0-9+\-_/]{2,}", md.lower()))
        return len(words & wordset)
    best = max(variants, key=lambda v: score(v[1])) if variants else ("", "")
    return best

