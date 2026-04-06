from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def build_review_pdf(
    *,
    employee_name: str,
    cycle_label: str,
    summary: str,
    manager_comments: str,
    development_actions: list[str],
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"{employee_name} Review")
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"Performance Review: {employee_name}", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Cycle: {cycle_label}", styles["Heading2"]),
        Spacer(1, 8),
        Paragraph(summary, styles["BodyText"]),
        Spacer(1, 10),
        Paragraph("Manager Comments", styles["Heading3"]),
        Paragraph(manager_comments or "No manager comments provided.", styles["BodyText"]),
        Spacer(1, 10),
        Paragraph("Development Actions", styles["Heading3"]),
    ]
    for action in development_actions:
        story.append(Paragraph(f"- {action}", styles["BodyText"]))
        story.append(Spacer(1, 4))
    doc.build(story)
    return buffer.getvalue()
