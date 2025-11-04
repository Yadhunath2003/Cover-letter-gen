from pathlib import Path
import markdown as md
import pdfkit

def md_to_pdf(md_text: str, out_pdf: Path):
    # 1) Markdown → HTML
    html = md.markdown(md_text, extensions=["extra", "toc", "sane_lists"])

    # 2) HTML → PDF (wkhtmltopdf required)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    # basic PDF options; tweak as needed
    options = {
        "quiet": "",
        "disable-smart-shrinking": "",
        "page-size": "Letter",
        "margin-top": "15mm",
        "margin-right": "15mm",
        "margin-bottom": "15mm",
        "margin-left": "15mm",
        "encoding": "UTF-8",
    }
    pdfkit.from_string(html, str(out_pdf), options=options)
    return out_pdf
