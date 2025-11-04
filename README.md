# Cover Letter Optimizer (Gemini + Markdown + pdfkit)

## Install
1) Python 3.10+
2) `pip install -r requirements.txt`
3) Install **wkhtmltopdf** (required by pdfkit)
4) Copy `.env.example` to `.env` and set `GEMINI_API_KEY`

## Run
```bash
python -m src.cli \
  --resume data/resume.md \
  --jd data/job_description.txt \
  --templates templates \
  --outdir out
