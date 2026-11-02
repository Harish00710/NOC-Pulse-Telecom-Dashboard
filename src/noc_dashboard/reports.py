from __future__ import annotations
from datetime import datetime
from io import BytesIO
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


def build_daily_report(history: pd.DataFrame, alarms: pd.DataFrame, cells: pd.DataFrame, report_date: datetime | None = None) -> bytes:
    """Create a compact, downloadable NOC daily performance report as a PDF."""
    report_date = report_date or datetime.now()
    latest = history.sort_values("timestamp").iloc[-1] if not history.empty else None
    avg_avail = float(history["availability_pct"].mean()) if not history.empty else 0.0
    avg_latency = float(history["latency_ms"].mean()) if not history.empty else 0.0
    avg_throughput = float(history["throughput_mbps"].mean()) if not history.empty else 0.0
    avg_loss = float(history["packet_loss_pct"].mean()) if not history.empty else 0.0
    open_alarms = alarms[alarms["status"] == "Open"] if not alarms.empty else alarms
    severity_counts = open_alarms["severity"].value_counts() if not open_alarms.empty else pd.Series(dtype=int)
    critical_count = int(severity_counts.get("Critical", 0))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=17*mm, leftMargin=17*mm, topMargin=16*mm, bottomMargin=16*mm, title="NOC Pulse Daily Performance Report")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="NocTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=21, leading=25, textColor=colors.HexColor("#14243b"), alignment=TA_LEFT, spaceAfter=4))
    styles.add(ParagraphStyle(name="NocSub", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#607086"), spaceAfter=12))
    styles.add(ParagraphStyle(name="NocH2", parent=styles["Heading2"], fontSize=12, textColor=colors.HexColor("#173d59"), spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name="NocBody", parent=styles["BodyText"], fontSize=8.5, leading=12, textColor=colors.HexColor("#28384d")))
    story = [
        Paragraph("NOC PULSE", styles["NocTitle"]),
        Paragraph(f"DAILY NETWORK PERFORMANCE REPORT · {report_date:%d %B %Y} · GENERATED {datetime.now():%H:%M}", styles["NocSub"]),
        Paragraph("Executive summary", styles["NocH2"]),
        Paragraph("This report summarizes the supplied NOC demo dataset. Measurements are simulated and are not sourced from a live network management system.", styles["NocBody"]),
        Spacer(1, 8),
    ]
    latest_vals = [
        ["Metric", "Current / Latest", "Daily average"],
        ["Availability", f"{float(latest['availability_pct']):.2f}%" if latest is not None else "N/A", f"{avg_avail:.2f}%"],
        ["Latency", f"{float(latest['latency_ms']):.1f} ms" if latest is not None else "N/A", f"{avg_latency:.1f} ms"],
        ["Throughput", f"{float(latest['throughput_mbps']):.1f} Mbps" if latest is not None else "N/A", f"{avg_throughput:.1f} Mbps"],
        ["Packet loss", f"{float(latest['packet_loss_pct']):.2f}%" if latest is not None else "N/A", f"{avg_loss:.2f}%"],
    ]
    table = Table(latest_vals, colWidths=[55*mm, 55*mm, 55*mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#173d59")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,1), (-1,-1), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0,1), (-1,-1), colors.HexColor("#26364a")),
        ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#d5dee8")),
        ("PADDING", (0,0), (-1,-1), 7),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ]))
    story.extend([table, Paragraph("Alarm overview", styles["NocH2"])])
    alarm_rows = [["Severity", "Open alarms"]]
    for severity in ["Critical", "Major", "Minor", "Warning"]:
        alarm_rows.append([severity, str(int(severity_counts.get(severity, 0)))])
    alarm_rows.append(["Total open", str(len(open_alarms))])
    at = Table(alarm_rows, colWidths=[95*mm, 70*mm])
    at.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#173d59")), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("BACKGROUND", (0,1), (-1,-1), colors.HexColor("#f1f5f9")),
        ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#d5dee8")), ("PADDING", (0,0), (-1,-1), 7),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ]))
    story.extend([at, Paragraph("Operational notes", styles["NocH2"])])
    if critical_count:
        note = f"There are {critical_count} open critical alarm(s). Prioritize validation of impacted cells and service restoration before routine optimization tasks."
    else:
        note = "No open critical alarms are present in the current sample. Continue routine monitoring and review major alarms for recurring patterns."
    story.append(Paragraph(note, styles["NocBody"]))
    story.append(Spacer(1, 7))
    story.append(Paragraph(f"Cell inventory: {len(cells)} cells across {cells['region'].nunique() if not cells.empty else 0} regions. Average cell availability: {cells['availability_pct'].mean():.2f}%.", styles["NocBody"]) if not cells.empty else Paragraph("Cell inventory: no cell records available.", styles["NocBody"]))
    story.extend([Spacer(1, 20), Paragraph("Data classification: DEMO / SIMULATED · This document is intended for project demonstration and must not be used as an operational SLA record.", styles["NocSub"])])

    def footer(canvas, _doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d5dee8"))
        canvas.line(17*mm, 12*mm, A4[0]-17*mm, 12*mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#7a899d"))
        canvas.drawString(17*mm, 7*mm, "NOC Pulse · Telecom Network Assurance Demo")
        canvas.drawRightString(A4[0]-17*mm, 7*mm, f"Page {_doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
