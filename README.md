
# Cover Letter Generator

A FastAPI-based cover letter generator powered by Google Gemini API. Provide your resume and job description, and it automatically generates tailored cover letters in JSON → Markdown format.

## Features

- **Gemini AI Integration**: Uses Google Gemini 2.5 Flash to generate intelligent, personalized cover letters
- **JSON → Markdown Pipeline**: Converts AI output through JSON intermediate format for structured data handling
- **Multiple Styles**: Support for different writing styles (impact, narrative, concise)
- **REST API**: Easy-to-use FastAPI endpoints for integration
- **Auto-save**: Generated cover letters are automatically saved as `.md` files in the `data/` folder

## Installation

1. **Requirements**: Python 3.10+
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment**:
   - Create `.env` file in the `backend/` folder
   - Add your Google Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

## Project Structure

```
Cover-letter-gen/
├── backend/
│   ├── main.py                 # FastAPI app with endpoints
│   ├── llm_client_gemini.py   # Gemini API client
│   ├── prompts.py             # Prompt templates
│   ├── json_to_md.py          # JSON to Markdown converter
│   └── export_pdf.py          # (Optional) PDF export helper
├── data/ (will upload your resume and job description)
│   ├── resume.md              # Your resume in Markdown
│   ├── job_description.txt    # Target job description (Text file.)
│   └── cover_letter.md        # Generated output
├── templates/
│   ├── style_impact.txt       # Impact-focused style hint
│   ├── style_narrative.txt    # Narrative style hint
│   └── style_concise.txt      # Concise style hint
└── requirements.txt
```

## API Usage

### Start the server

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Visit `http://127.0.0.1:8000/docs` for interactive API documentation.

### Endpoints

#### 1. Generate Cover Letter
**POST** `/api/generate`

Request body:
```json
{
  "style": "impact",
  "model": "gemini-2.5-flash",
  "temperature": 0.35,
  "resume_file": "resume.md",
  "jd_file": "job_description.txt"
}
```

Response:
```json
{
  "md": "# Your Name\n...[markdown content]...",
  "file_path": "C:\\path\\to\\data\\cover_letter.md",
  "filename": "cover_letter.md"
}
```

The generated markdown is automatically saved to `data/cover_letter.md`.

#### 2. Get Available Styles
**GET** `/api/styles`

Returns available style templates.

#### 3. Get Available Models
**GET** `/api/models`

Returns list of available Gemini models.

#### 4. Debug Data
**GET** `/api/debug-data`

Verify that resume and job description files are being read correctly.

## Data Pipeline

```
Resume + Job Description
         ↓
   Gemini API Prompt
         ↓
    JSON Response
         ↓
  Parse JSON → Extract Fields
         ↓
   Markdown Formatting
         ↓
   Save to data/cover_letter.md
```

## Configuration

Edit the request body in `/api/generate` to customize:
- **style**: Different writing styles (`impact`, `narrative`, `concise`)
- **model**: Gemini model version (default: `gemini-2.5-flash`)
- **temperature**: Creativity level (0.0-1.0, lower = more deterministic)
- **resume_file**: Path to resume file (relative to `data/`)
- **jd_file**: Path to job description file (relative to `data/`)

## Example Workflow

1. **Prepare files**:
   - Place your resume in `data/resume.md`
   - Place job description in `data/job_description.txt`

2. **Generate**:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/generate \
     -H "Content-Type: application/json" \
     -d '{"style": "impact"}'
   ```

3. **Download**:
   - Get the markdown from the response or open `data/cover_letter.md`

## Dependencies

- `google-genai`: Google Gemini API client
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `pydantic`: Data validation
- `python-dotenv`: Environment variable management
- `markdown`: Markdown formatting

## Notes

- The API requires a valid Google Gemini API key
- Cover letters are limited to ~400 words and one page
- JSON wrapper ensures structured data handling before Markdown conversion
- Generated files are overwritten on each generation (save results if needed)

## Future Enhancements

- PDF export functionality
- Email integration for direct submission
- Cover letter history/versioning
- Batch generation for multiple job applications
