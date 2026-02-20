import json
from typing import Dict, Any


def json_to_md(json_str: str) -> str:
    """
    Convert JSON cover letter to a well-formatted Markdown document.

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
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    data = json.loads(cleaned.strip())

    md_lines = []

    # ── Header Block ─────────────────────────────────────────────────────────
    name = data.get("candidate_name", "Your Name")
    md_lines.append(f"# {name}")
    md_lines.append("")

    # Contact info on one line, separated by  |
    contact_parts = []
    if data.get("candidate_email"):
        contact_parts.append(data["candidate_email"])
    if data.get("candidate_phone"):
        contact_parts.append(data["candidate_phone"])
    if data.get("candidate_address"):
        contact_parts.append(data["candidate_address"])
    if contact_parts:
        md_lines.append("  |  ".join(contact_parts))
        md_lines.append("")

    # Divider to separate header from letter body
    md_lines.append("---")
    md_lines.append("")

    # ── Date ─────────────────────────────────────────────────────────────────
    if data.get("date"):
        md_lines.append(data["date"])
        md_lines.append("")

    # ── Recipient Block ───────────────────────────────────────────────────────
    recipient_lines = []
    if data.get("recipient_name"):
        recipient_lines.append(data["recipient_name"])
    if data.get("recipient_title"):
        recipient_lines.append(data["recipient_title"])
    if data.get("company_name"):
        recipient_lines.append(data["company_name"])
    if data.get("company_address"):
        recipient_lines.append(data["company_address"])

    if recipient_lines:
        md_lines.extend(recipient_lines)
        md_lines.append("")

    # ── Greeting ──────────────────────────────────────────────────────────────
    greeting = data.get("greeting", "Dear Hiring Manager,")
    md_lines.append(greeting)
    md_lines.append("")

    # ── Opening Paragraph ─────────────────────────────────────────────────────
    if data.get("opening_paragraph"):
        md_lines.append(data["opening_paragraph"])
        md_lines.append("")

    # ── Body Paragraphs ───────────────────────────────────────────────────────
    body_paragraphs = data.get("body_paragraphs", [])
    if isinstance(body_paragraphs, list):
        for para in body_paragraphs:
            md_lines.append(para)
            md_lines.append("")

    # ── Closing Paragraph ─────────────────────────────────────────────────────
    if data.get("closing_paragraph"):
        md_lines.append(data["closing_paragraph"])
        md_lines.append("")

    # ── Sign-off ──────────────────────────────────────────────────────────────
    md_lines.append("Sincerely,")
    md_lines.append("")

    # Signature name
    signature = data.get("signature", name)
    if signature:
        md_lines.append(signature)

    return "\n".join(md_lines)