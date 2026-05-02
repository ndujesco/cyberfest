from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

from core.session import Session
from core.finding import Severity
from reports.ai_enricher import enrich_findings

_SEV_COLOR = {
    Severity.CRITICAL: colors.HexColor("#dc2626"),
    Severity.HIGH:     colors.HexColor("#ea580c"),
    Severity.MEDIUM:   colors.HexColor("#ca8a04"),
    Severity.LOW:      colors.HexColor("#16a34a"),
    Severity.INFO:     colors.HexColor("#6b7280"),
}


def render_pdf(session: Session, output_path: str | None = None) -> str:
    summary = session.summary()
    findings = session.get_findings()

    out_path = output_path or str(
        Path.home() / ".specterapi" / "reports" / f"specter_{session.id[:8]}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    )
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    ai_data = enrich_findings(findings, summary.get("target", ""))
    ai_findings = ai_data.get("findings", {})

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SpecterTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#0ea5e9"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "SpecterSub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#94a3b8"),
        spaceAfter=16,
    )
    section_style = ParagraphStyle(
        "SpecterSection",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#e2e8f0"),
        backColor=colors.HexColor("#1e293b"),
        borderPad=6,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "SpecterBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )
    label_style = ParagraphStyle(
        "SpecterLabel",
        parent=body_style,
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=colors.HexColor("#0ea5e9"),
        spaceAfter=2,
    )
    ai_body_style = ParagraphStyle(
        "SpecterAIBody",
        parent=body_style,
        fontSize=8,
        leading=12,
        textColor=colors.HexColor("#475569"),
        spaceAfter=4,
    )

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
    )
    story = []

    story.append(Paragraph("SpecterAPI Security Report", title_style))
    story.append(Paragraph(
        f"Target: {summary['target']}  |  Session: {session.id[:8].upper()}  |  "
        f"Generated: {datetime.now():%Y-%m-%d %H:%M}",
        subtitle_style,
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0ea5e9")))
    story.append(Spacer(1, 0.4 * cm))

    # Summary table
    sev_counts = summary.get("severity_counts", {})
    summary_data = [
        ["Metric", "Value"],
        ["Endpoints discovered", str(summary.get("endpoints", 0))],
        ["Total findings", str(summary.get("findings", 0))],
        ["Critical", str(sev_counts.get("critical", 0))],
        ["High", str(sev_counts.get("high", 0))],
        ["Medium", str(sev_counts.get("medium", 0))],
        ["Low", str(sev_counts.get("low", 0))],
    ]
    summary_table = Table(summary_data, colWidths=[8 * cm, 8 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(Paragraph("Executive Summary", section_style))
    story.append(summary_table)
    story.append(Spacer(1, 0.4 * cm))

    if ai_data.get("executive_summary"):
        story.append(Paragraph(ai_data["executive_summary"], ai_body_style))

    story.append(Spacer(1, 0.4 * cm))

    # Findings
    story.append(Paragraph("Findings", section_style))

    if not findings:
        story.append(Paragraph("No findings recorded in this session.", body_style))
    else:
        for i, f in enumerate(findings, 1):
            sev_color = _SEV_COLOR.get(f.severity, colors.gray)
            sev_label = f.severity.value.upper()
            ai = ai_findings.get(f.id, {})

            header_data = [[
                Paragraph(f"#{i} — {f.title}", ParagraphStyle(
                    "fh", parent=body_style, fontName="Helvetica-Bold", fontSize=10,
                )),
                Paragraph(sev_label, ParagraphStyle(
                    "sev", parent=body_style, fontName="Helvetica-Bold",
                    textColor=colors.white, alignment=1,
                )),
            ]]
            header_table = Table(header_data, colWidths=[13 * cm, 3 * cm])
            header_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f1f5f9")),
                ("BACKGROUND", (1, 0), (1, 0), sev_color),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(header_table)

            detail_data = [
                ["Module", f.module],
                ["Endpoint", f.endpoint],
                ["CWE", f.cwe or "—"],
                ["Evidence", f.evidence],
            ]
            detail_table = Table(detail_data, colWidths=[3 * cm, 13 * cm])
            detail_table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ]))
            story.append(detail_table)

            if ai:
                story.append(Spacer(1, 0.15 * cm))
                ai_block_data = []
                if ai.get("description"):
                    ai_block_data.append([
                        Paragraph("Description", label_style),
                        Paragraph(ai["description"], ai_body_style),
                    ])
                if ai.get("business_impact"):
                    ai_block_data.append([
                        Paragraph("Business Impact", label_style),
                        Paragraph(ai["business_impact"], ai_body_style),
                    ])
                if ai.get("technical_details"):
                    ai_block_data.append([
                        Paragraph("Technical Details", label_style),
                        Paragraph(ai["technical_details"], ai_body_style),
                    ])
                if ai.get("remediation"):
                    remediation_text = ai["remediation"].replace("•", "\n•")
                    ai_block_data.append([
                        Paragraph("Remediation", label_style),
                        Paragraph(remediation_text, ai_body_style),
                    ])
                if ai_block_data:
                    ai_table = Table(ai_block_data, colWidths=[3.5 * cm, 12.5 * cm])
                    ai_table.setStyle(TableStyle([
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ]))
                    story.append(ai_table)

            story.append(Spacer(1, 0.4 * cm))

    doc.build(story)
    return out_path
