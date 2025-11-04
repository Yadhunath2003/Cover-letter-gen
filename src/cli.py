import argparse
from pathlib import Path
from datetime import datetime
from .generator import generate_variants, choose_best
from .export_pdf import md_to_pdf

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", type=Path, default=Path("data/resume.md"))
    ap.add_argument("--jd", type=Path, default=Path("data/job_description.txt"))
    ap.add_argument("--templates", type=Path, default=Path("templates"))
    ap.add_argument("--outdir", type=Path, default=Path("out"))
    ap.add_argument("--model", type=str, default="gemini-1.5-flash")
    args = ap.parse_args()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = args.outdir / f"run_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1) Generate cover letter variants (one per style_*.txt)
    variants = generate_variants(args.resume, args.jd, args.templates, model=args.model)
    for name, md_text in variants:
        (run_dir / f"{name}.md").write_text(md_text, encoding="utf-8")

    # 2) Pick best by JD keyword overlap
    jd_text = args.jd.read_text(encoding="utf-8")
    best_name, best_md = choose_best(variants, jd_text)
    (run_dir / "best_coverletter.md").write_text(best_md, encoding="utf-8")

    # 3) Export to PDF
    pdf_path = run_dir / "best_coverletter.pdf"
    md_to_pdf(best_md, pdf_path)
    print(f"Best variant: {best_name}")
    print(f"Saved PDF: {pdf_path}")

if __name__ == "__main__":
    main()
