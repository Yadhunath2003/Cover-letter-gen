import json
from typing import Dict, Any


def json_to_md(json_str: str) -> str:
    """
    Convert JSON cover letter to Markdown format.
    
    Args:
        json_str: JSON string with cover letter data (may be wrapped in ```json ... ``` fences)
        
    Returns:
        Markdown formatted cover letter
        
    Raises:
        json.JSONDecodeError: If JSON is invalid
    """
    # Strip markdown code fences if present
    cleaned = json_str.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]  # Remove ```json
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]  # Remove just ```
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]  # Remove trailing ```
    
    data = json.loads(cleaned.strip())
    
    md_lines = []
    
    # Header with candidate info
    md_lines.append(f"# {data.get('candidate_name', 'Your Name')}")
    if data.get('candidate_email'):
        md_lines.append(f"{data['candidate_email']}")
    if data.get('candidate_phone'):
        md_lines.append(f"{data['candidate_phone']}")
    md_lines.append("")
    
    # Date
    if data.get('date'):
        md_lines.append(data['date'])
        md_lines.append("")
    
    # Recipient info
    recipient_name = data.get('recipient_name', 'Hiring Manager')
    if recipient_name:
        md_lines.append(recipient_name)
    
    company = data.get('company_name', '')
    if company:
        md_lines.append(company)
    md_lines.append("")
    
    # Greeting
    greeting = data.get('greeting', 'Dear Hiring Manager,')
    if greeting:
        md_lines.append(greeting)
    md_lines.append("")
    
    # Opening paragraph
    if data.get('opening_paragraph'):
        md_lines.append(data['opening_paragraph'])
        md_lines.append("")
    
    # Body paragraphs
    body_paragraphs = data.get('body_paragraphs', [])
    if isinstance(body_paragraphs, list):
        for para in body_paragraphs:
            md_lines.append(para)
            md_lines.append("")
    
    # Closing paragraph
    if data.get('closing_paragraph'):
        md_lines.append(data['closing_paragraph'])
        md_lines.append("")
    
    # Signature
    signature = data.get('signature', '')
    if signature:
        md_lines.append(signature)
    
    return "\n".join(md_lines)
