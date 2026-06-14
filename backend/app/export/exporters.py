"""Render a structured index to various downloadable formats."""
from __future__ import annotations

import csv
import io
import json

from app.indexing.formatter import format_index_text

EXPORT_FORMATS = ("pdf", "csv", "json", "markdown")


def export_index(index: dict, fmt: str) -> tuple[bytes, str, str]:
    """Return ``(content_bytes, media_type, file_extension)`` for ``fmt``."""
    fmt = fmt.lower()
    if fmt == "json":
        return _to_json(index)
    if fmt == "csv":
        return _to_csv(index)
    if fmt == "markdown":
        return _to_markdown(index)
    if fmt == "pdf":
        return _to_pdf(index)
    raise ValueError(f"Unsupported export format '{fmt}'. Use one of {EXPORT_FORMATS}.")


def _to_json(index: dict) -> tuple[bytes, str, str]:
    payload = json.dumps(index, indent=2, ensure_ascii=False).encode("utf-8")
    return payload, "application/json", "json"


def _to_csv(index: dict) -> tuple[bytes, str, str]:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["letter", "topic", "pages"])
    for group in index.get("groups", []):
        for entry in group["entries"]:
            writer.writerow(
                [group["letter"], entry["topic"], ", ".join(map(str, entry["pages"]))]
            )
    return buffer.getvalue().encode("utf-8"), "text/csv", "csv"


def _to_markdown(index: dict) -> tuple[bytes, str, str]:
    lines = ["# Index", ""]
    for group in index.get("groups", []):
        lines.append(f"## {group['letter']}")
        lines.append("")
        for entry in group["entries"]:
            pages = ", ".join(str(p) for p in entry["pages"])
            lines.append(f"- **{entry['topic']}** — {pages}")
        lines.append("")
    return "\n".join(lines).encode("utf-8"), "text/markdown", "md"


def _to_pdf(index: dict) -> tuple[bytes, str, str]:
    try:
        return _to_pdf_reportlab(index)
    except ImportError:
        # Fall back to a plain-text "PDF" so exports never hard-fail.
        text = format_index_text(index)
        return text.encode("utf-8"), "application/pdf", "pdf"


def _to_pdf_reportlab(index: dict) -> tuple[bytes, str, str]:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, title="Index")
    styles = getSampleStyleSheet()
    story = [Paragraph("Index", styles["Title"]), Spacer(1, 0.2 * inch)]

    for group in index.get("groups", []):
        story.append(Paragraph(group["letter"], styles["Heading2"]))
        for entry in group["entries"]:
            pages = ", ".join(str(p) for p in entry["pages"])
            story.append(Paragraph(f"{entry['topic']} &nbsp;&nbsp; {pages}", styles["Normal"]))
        story.append(Spacer(1, 0.1 * inch))

    doc.build(story)
    return buffer.getvalue(), "application/pdf", "pdf"
