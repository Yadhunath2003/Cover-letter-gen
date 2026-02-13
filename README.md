# Cover Letter Generator

An AI-powered cover letter generator that uses Google Gemini to create tailored, one-page cover letters from your resume and a job description. Choose from multiple writing styles and get polished markdown output — no placeholders, no invented facts.

## Features

- **AI-Powered Generation** — Uses Google Gemini to produce cover letters grounded in your actual resume and the target job description
- **Multiple Writing Styles** — Choose between `impact` (achievement-focused), `concise` (direct and crisp), or `narrative` (story-driven)
- **Structured Output** — Gemini returns structured JSON that is converted into clean, readable markdown
- **Web UI** — Minimal browser interface for selecting a style and generating letters with one click
- **REST API** — FastAPI backend with endpoints for generation, style listing, and model discovery

## Project Structure

```
Cover-letter-gen/
├── backend/
│   ├── main.py               # FastAPI app and API endpoints
│   ├── llm_client_gemini.py   # Google Gemini API wrapper
│   ├── prompts.py             # Prompt construction logic
│   └── json_to_md.py          # JSON response → Markdown converter
├── frontend/
│   ├── index.html             # Web interface
│   └── app.js                 # Client-side logic
├── templates/
│   ├── style_impact.txt       # Impact/achievement-focused style guide
│   ├── style_concise.txt      # Concise, direct style guide
│   └── style_narrative.txt    # Narrative/story-driven style guide
├── data/                      # Your resume and job description go here
├── requirements.txt
└── .gitignore
```

## Prerequisites

- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/apikey)

## Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/Yadhunath2003/Cover-letter-gen.git
   cd Cover-letter-gen
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Add your API key**

   Create a `.env` file inside the `backend/` directory:

   ```
   GEMINI_API_KEY="your_google_api_key_here"
   ```

4. **Add your input files**

   Place two files in the `data/` directory:

   - `resume.md` — Your resume in markdown format
   - `job_description.txt` — The job description you are targeting

## Usage

### Start the backend

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Open the frontend

Serve the frontend with any static file server, for example:

```bash
python -m http.server 3000 --directory frontend
```

Then open `http://localhost:3000` in your browser. Select a writing style and click **Generate Cover Letter**.

The generated cover letter is also saved to `data/cover_letter.md`.

### Use the API directly

```bash
curl -X POST http://127.0.0.1:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "style": "impact",
    "model": "gemini-2.5-flash",
    "temperature": 0.35,
    "resume_file": "resume.md",
    "jd_file": "job_description.txt"
  }'
```

## API Reference

| Method | Endpoint           | Description                              |
|--------|--------------------|------------------------------------------|
| POST   | `/api/generate`    | Generate a cover letter                  |
| GET    | `/api/styles`      | List available writing styles            |
| GET    | `/api/models`      | List available Gemini models             |
| GET    | `/api/debug-data`  | Check data file status (for debugging)   |

### POST `/api/generate`

**Request body:**

| Field          | Type   | Default                | Description                        |
|----------------|--------|------------------------|------------------------------------|
| `style`        | string | `"impact"`             | Writing style (`impact`, `concise`, `narrative`) |
| `model`        | string | `"gemini-2.5-flash"`   | Gemini model to use                |
| `temperature`  | float  | `0.35`                 | Generation temperature (0–1)       |
| `resume_file`  | string | `"resume.md"`          | Filename in `data/` for the resume |
| `jd_file`      | string | `"job_description.txt"`| Filename in `data/` for the JD     |

**Response:**

```json
{
  "md": "# Cover Letter\n...",
  "file_path": "/absolute/path/to/data/cover_letter.md",
  "filename": "cover_letter.md"
}
```

## Writing Styles

| Style       | Description                                                        |
|-------------|--------------------------------------------------------------------|
| `impact`    | Opens with a specific achievement; quantified wins; confident close |
| `concise`   | Direct hook with 2–3 key points; crisp and to the point            |
| `narrative` | Story-driven opening; connects personal purpose to the role         |

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn, Pydantic
- **Frontend:** Vanilla HTML + JavaScript
- **AI:** Google Gemini API (`google-genai`)
- **Config:** python-dotenv for environment management
