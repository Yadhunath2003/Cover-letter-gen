BASE_INSTRUCTIONS = """You will write a truthful, one-page cover letter.
Use the resume and job description below. Keep it under 400 words.
Address impact with numbers when available. Keep a confident, friendly tone.
Never invent facts; only reorganize or rephrase truthfully.

IMPORTANT:
- Use the ACTUAL name from the resume (not "[Your Name]" or placeholders)
- Use the ACTUAL company name from the job description (not "[Company Name]" or placeholders)
- Use the ACTUAL job title from the job description (not "[Job Title]" or placeholders)
- Extract and use real information from the provided data
- Do NOT use any placeholders or bracketed text like [Your Name], [Company Name], etc.

Return ONLY valid JSON with this structure (no code fences, no commentary):
{
  "candidate_name": "Full name from resume",
  "candidate_email": "Email from resume (or infer from context)",
  "candidate_phone": "Phone from resume (or empty string if not found)",
  "date": "Today's date in YYYY-MM-DD format",
  "recipient_name": "Recipient name if mentioned in JD, else empty string",
  "recipient_title": "Job title from the JD",
  "company_name": "Company name from the JD",
  "greeting": "Dear [Recipient Name] or Dear Hiring Manager",
  "opening_paragraph": "2-3 sentences introducing yourself and the role",
  "body_paragraphs": ["paragraph 1 with accomplishments", "paragraph 2 with relevant skills"],
  "closing_paragraph": "1-2 sentences with call to action",
  "signature": "Candidate name"
}
"""

def build_cover_letter_prompt(md_resume: str, jd_text: str, style_hint: str) -> str:
    return f"""{BASE_INSTRUCTIONS}

STYLE HINT:
{style_hint}

### Resume (Markdown)
{md_resume}

### Job Description
{jd_text}
"""
