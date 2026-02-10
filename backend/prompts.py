BASE_INSTRUCTIONS = """You will write a truthful, one-page cover letter in Markdown.
Use the resume and job description below. Keep it under 400 words.
Address impact with numbers when available. Keep a confident, friendly tone.
Never invent facts; only reorganize or rephrase truthfully.

IMPORTANT:
- Use the ACTUAL name from the resume (not "[Your Name]" or placeholders)
- Use the ACTUAL company name from the job description (not "[Company Name]" or placeholders)
- Use the ACTUAL job title from the job description (not "[Job Title]" or placeholders)
- Extract and use real information from the provided data
- Do NOT use any placeholders or bracketed text like [Your Name], [Company Name], etc.

Return ONLY the final cover letter in Markdown. No code fences, no commentary.
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
