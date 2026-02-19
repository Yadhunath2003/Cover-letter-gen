import re
import pdfkit

# Windows path to wkhtmltopdf — update this if yours is installed elsewhere
WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
PDF_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)


def md_to_html(md_text: str) -> str:
    """
    Convert cover letter Markdown to a fully styled HTML document
    that matches a professional cover letter layout.
    """
    lines = md_text.split("\n")

    # Extract structured parts
    name = ""
    contact = ""
    rest_lines = []
    i = 0

    # First line is usually # Name
    if lines and lines[0].startswith("# "):
        name = lines[0][2:].strip()
        i = 1

    # Skip blank line after name
    if i < len(lines) and lines[i].strip() == "":
        i += 1

    # Contact line (contains |)
    if i < len(lines) and "|" in lines[i]:
        contact = lines[i].strip()
        i += 1

    # Skip blank line
    if i < len(lines) and lines[i].strip() == "":
        i += 1

    # Skip --- divider
    if i < len(lines) and lines[i].strip() == "---":
        i += 1

    # Everything else is the letter body
    rest_lines = lines[i:]

    # Convert contact line: split by | and make individual spans
    contact_parts = [c.strip() for c in contact.split("|") if c.strip()]
    contact_html = " &nbsp;|&nbsp; ".join(
        f'<span>{part}</span>' for part in contact_parts
    )

    # Convert body lines to HTML paragraphs
    body_html = _convert_body(rest_lines)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Garamond:ital,wght@0,400;0,700;1,400&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&display=swap');

    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: 'EB Garamond', Georgia, 'Times New Roman', serif;
      font-size: 11.5pt;
      color: #1a1a1a;
      background: #fff;
      padding: 0;
      margin: 0;
    }}

    .page {{
      width: 210mm;
      min-height: 297mm;
      padding: 18mm 20mm 18mm 20mm;
      margin: 0 auto;
      background: #fff;
    }}

    /* ── Header ── */
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 6px;
    }}

    .header-left .name {{
      font-size: 22pt;
      font-weight: 600;
      letter-spacing: 0.5px;
      color: #111;
      line-height: 1.1;
    }}

    .header-right {{
      text-align: right;
      font-size: 9.5pt;
      color: #444;
      line-height: 1.8;
    }}

    .divider {{
      border: none;
      border-top: 1.5px solid #1a1a1a;
      margin: 8px 0 18px 0;
    }}

    /* ── Letter Body ── */
    .body {{
      line-height: 1.65;
    }}

    .body p {{
      margin-bottom: 11px;
      text-align: justify;
    }}

    .body .date {{
      margin-bottom: 16px;
      color: #333;
    }}

    .body .recipient {{
      margin-bottom: 16px;
      line-height: 1.5;
    }}

    .body .greeting {{
      margin-bottom: 14px;
    }}

    .body .signoff {{
      margin-top: 18px;
      margin-bottom: 4px;
    }}

    .body .signature {{
      font-weight: 600;
      font-size: 11.5pt;
    }}
  </style>
</head>
<body>
  <div class="page">

    <!-- Header: Name left, Contact right -->
    <div class="header">
      <div class="header-left">
        <div class="name">{name}</div>
      </div>
      <div class="header-right">
        {contact_html}
      </div>
    </div>

    <hr class="divider" />

    <!-- Letter Body -->
    <div class="body">
      {body_html}
    </div>

  </div>
</body>
</html>"""

    return html


def _convert_body(lines: list) -> str:
    """Convert body lines into semantic HTML sections."""
    html_parts = []
    i = 0
    section = "date"  # track where we are: date → recipient → greeting → body → signoff → signature

    # Collect non-empty blocks separated by blank lines
    blocks = []
    current = []
    for line in lines:
        if line.strip() == "":
            if current:
                blocks.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))

    for idx, block in enumerate(blocks):
        stripped = block.strip()

        # Date block (contains digits and looks like a date)
        if idx == 0 and re.match(r"^\d{4}-\d{2}-\d{2}$", stripped):
            html_parts.append(f'<p class="date">{stripped}</p>')

        # Recipient block (multi-line, appears before greeting)
        elif idx == 1 and not stripped.lower().startswith("dear"):
            recipient_lines = stripped.replace("\n", "<br>")
            html_parts.append(f'<p class="recipient">{recipient_lines}</p>')

        # Greeting
        elif stripped.lower().startswith("dear"):
            html_parts.append(f'<p class="greeting">{stripped}</p>')

        # Sincerely / sign-off
        elif stripped.lower().startswith("sincerely"):
            html_parts.append(f'<p class="signoff">{stripped}</p>')

        # Last block = signature
        elif idx == len(blocks) - 1 and not stripped.lower().startswith("dear"):
            html_parts.append(f'<p class="signature">{stripped}</p>')

        # Regular paragraph
        else:
            html_parts.append(f'<p>{stripped}</p>')

    return "\n      ".join(html_parts)


def md_to_pdf(md_text: str, output_path: str) -> None:
    """
    Convert Markdown cover letter to a styled PDF file.

    Args:
        md_text:     Markdown string of the cover letter
        output_path: File path to save the PDF (e.g. "/tmp/coverletter.pdf")
    """
    html = md_to_html(md_text)

    options = {
        "page-size":       "A4",
        "margin-top":      "0mm",
        "margin-right":    "0mm",
        "margin-bottom":   "0mm",
        "margin-left":     "0mm",
        "encoding":        "UTF-8",
        "enable-local-file-access": "",
        "disable-smart-shrinking": "",
        "print-media-type": "",
    }

    pdfkit.from_string(html, output_path, options=options, configuration=PDF_CONFIG)