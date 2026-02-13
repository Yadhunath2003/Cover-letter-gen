
  # Cover Letter Optimizer (Gemini + Markdown + pdfkit)

  ## Install
  1) Python 3.10+
  2) `pip install -r requirements.txt`
  3) Create `.env` in `/backend` folder and paste `GEMINI_API_KEY="Your_Google_API_KEY"`

  ## About
  A cover letter generator powered by Google Gemini API. Provide your resume and job description, and it automatically generates a tailored cover letter in markdown format.

  ## Run
  ```bash
  python -m src.cli \
    --resume data/resume.md \
    --jd data/job_description.txt \
    --templates templates \
    --outdir out
  ```

  ## Output
  Generated cover letters are saved as markdown files in the specified output directory.
