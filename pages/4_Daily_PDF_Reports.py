from __future__ import annotations
from datetime import datetime, date
import streamlit as st

from src.noc_dashboard.data import load_alarms, load_kpi_history, load_cells
from src.noc_dashboard.reports import build_daily_report
from src.noc_dashboard.ui import inject_global_css, render_sidebar_brand, render_metric_card

st.set_page_config(page_title="Daily PDF Reports | NOC Pulse", page_icon="📄", layout="wide")
inject_global_css(); render_sidebar_brand()
st.markdown('<div class="eyebrow">REPORTING / SHIFT HANDOVER</div>', unsafe_allow_html=True)
st.title("Automated PDF Report Generation")
st.caption("Build a daily performance summary from the included KPI, alarm, and cell inventory datasets.")

history = load_kpi_history()
alarms = load_alarms()
cells = load_cells()
open_count = int((alarms["status"] == "Open").sum())
availability = float(history.iloc[-1]["availability_pct"]) if not history.empty else 0.0
latency = float(history.iloc[-1]["latency_ms"]) if not history.empty else 0.0

c1,c2,c3 = st.columns(3)
with c1: render_metric_card("Latest availability", f"{availability:.2f}%", "Most recent sample", "positive")
with c2: render_metric_card("Latest latency", f"{latency:.1f} ms", "Most recent sample", "neutral")
with c3: render_metric_card("Open alarms", str(open_count), "Included in generated report", "negative" if open_count else "positive")

st.markdown("### Report settings")
report_date = st.date_input("Report date", value=date.today())
include_note = st.checkbox("Include demo-data classification notice", value=True, disabled=True)
st.write(f"Report source: {len(history)} KPI samples · {len(alarms)} alarm records · {len(cells)} cells")
if st.button("Generate daily PDF report", type="primary"):
    try:
        pdf_bytes = build_daily_report(history, alarms, cells, datetime.combine(report_date, datetime.min.time()))
        st.session_state["daily_report_pdf"] = pdf_bytes
        st.session_state["daily_report_name"] = f"noc_daily_report_{report_date:%Y%m%d}.pdf"
        st.success("Report generated successfully.")
    except Exception as exc:
        st.error(f"Report generation failed: {exc}")

if "daily_report_pdf" in st.session_state:
    st.download_button("Download PDF report", data=st.session_state["daily_report_pdf"], file_name=st.session_state["daily_report_name"], mime="application/pdf")
    st.caption("The PDF includes an executive summary, KPI table, alarm severity overview, cell inventory summary, and a simulated-data disclaimer.")
