from __future__ import annotations

import streamlit as st

from src.noc_dashboard.data import load_alarms, load_kpi_history, load_cells, current_kpis
from src.noc_dashboard.ui import inject_global_css, render_sidebar_brand, render_metric_card

st.set_page_config(
    page_title="NOC Pulse | Network Operations Center",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
render_sidebar_brand()

st.markdown('<div class="eyebrow">NETWORK OPERATIONS CENTER</div>', unsafe_allow_html=True)
st.title("NOC Pulse")
st.markdown("Monitor network health, investigate alarms, inspect packet captures, and publish daily reports.")
st.caption("DEMO ENVIRONMENT · All dashboard KPIs and alarms are generated sample data. No live network devices are connected.")

alarms = load_alarms()
history = load_kpi_history()
cells = load_cells()
kpis = current_kpis(history)

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_metric_card("Network availability", f"{kpis['availability']:.2f}%", "Target ≥ 99.5%", "positive")
with c2:
    render_metric_card("Average latency", f"{kpis['latency_ms']:.0f} ms", "Target < 50 ms", "neutral")
with c3:
    render_metric_card("Throughput", f"{kpis['throughput_mbps']:.1f} Mbps", "Aggregate demo traffic", "neutral")
with c4:
    render_metric_card("Active alarms", str(int((alarms['status'] == 'Open').sum())), f"{int((alarms['severity'] == 'Critical').sum())} critical", "negative" if (alarms['severity'] == 'Critical').any() else "positive")

st.markdown("### Operations snapshot")
left, right = st.columns([1.55, 1])
with left:
    st.markdown('<div class="panel-title">Network performance · last 24 hours</div>', unsafe_allow_html=True)
    chart_data = history.tail(24).set_index("timestamp")[["availability_pct", "latency_ms"]]
    st.line_chart(chart_data, height=290, use_container_width=True)
with right:
    st.markdown('<div class="panel-title">Alarm severity · current sample</div>', unsafe_allow_html=True)
    severity_counts = alarms[alarms["status"] == "Open"]["severity"].value_counts().reindex(["Critical", "Major", "Minor", "Warning"], fill_value=0)
    st.bar_chart(severity_counts, height=290, use_container_width=True)

st.markdown("### Cell inventory")
summary = cells.groupby("region", as_index=False).agg(cells=("cell_id", "count"), avg_utilization=("utilization_pct", "mean"), avg_availability=("availability_pct", "mean"))
summary["avg_utilization"] = summary["avg_utilization"].map(lambda x: f"{x:.1f}%")
summary["avg_availability"] = summary["avg_availability"].map(lambda x: f"{x:.2f}%")
st.dataframe(summary, hide_index=True, use_container_width=True)

st.markdown("---")
st.markdown("**Quick navigation:** use the pages in the left sidebar to open the KPI monitor, alarm tracker, packet analyzer, or PDF report center.")
