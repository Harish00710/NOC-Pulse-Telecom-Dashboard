from __future__ import annotations
import streamlit as st

from src.noc_dashboard.data import load_kpi_history, load_cells, current_kpis
from src.noc_dashboard.ui import inject_global_css, render_sidebar_brand, render_metric_card

st.set_page_config(page_title="Live KPI Monitor | NOC Pulse", page_icon="📈", layout="wide")
inject_global_css(); render_sidebar_brand()
st.markdown('<div class="eyebrow">SERVICE ASSURANCE / PERFORMANCE</div>', unsafe_allow_html=True)
st.title("Live KPI Monitor")
st.caption("Latest sample KPIs and historical performance. Values are simulated for this local demo.")

history = load_kpi_history()
cells = load_cells()
if history.empty:
    st.warning("No KPI history found. Check data/sample/kpi_history.csv.")
    st.stop()

window = st.selectbox("Time window", ["Last 6 hours", "Last 12 hours", "Last 24 hours", "All available data"], index=2)
count = {"Last 6 hours": 6, "Last 12 hours": 12, "Last 24 hours": 24, "All available data": len(history)}[window]
view = history.tail(count)
kpis = current_kpis(view)

cols = st.columns(5)
metrics = [
    ("Availability", f"{kpis['availability']:.2f}%", "Service uptime"),
    ("Latency", f"{kpis['latency_ms']:.1f} ms", "Round-trip delay"),
    ("Throughput", f"{kpis['throughput_mbps']:.1f} Mbps", "Aggregate traffic"),
    ("Packet loss", f"{kpis['packet_loss_pct']:.2f}%", "Observed loss"),
    ("Active users", f"{kpis['active_users']:,.0f}", "Estimated sessions"),
]
for col, (label, value, note) in zip(cols, metrics):
    with col: render_metric_card(label, value, note, "positive" if label == "Availability" and kpis["availability"] >= 99.5 else "neutral")

st.markdown("### Performance trends")
left, right = st.columns(2)
with left:
    st.markdown('<div class="panel-title">Availability and packet loss</div>', unsafe_allow_html=True)
    st.line_chart(view.set_index("timestamp")[["availability_pct", "packet_loss_pct"]], height=290, use_container_width=True)
with right:
    st.markdown('<div class="panel-title">Latency and throughput</div>', unsafe_allow_html=True)
    st.line_chart(view.set_index("timestamp")[["latency_ms", "throughput_mbps"]], height=290, use_container_width=True)

st.markdown("### Cell performance")
col1, col2 = st.columns([1.3, 1])
with col1:
    st.dataframe(cells.sort_values("utilization_pct", ascending=False), hide_index=True, use_container_width=True)
with col2:
    st.markdown('<div class="panel-title">Utilization by technology</div>', unsafe_allow_html=True)
    by_tech = cells.groupby("technology")["utilization_pct"].mean().sort_values(ascending=False)
    st.bar_chart(by_tech, height=260, use_container_width=True)
    st.caption(f"Last sample timestamp: {view.iloc[-1]['timestamp']:%d %b %Y, %H:%M} UTC")

csv = view.to_csv(index=False).encode("utf-8")
st.download_button("Download KPI data (CSV)", data=csv, file_name="noc_kpi_history.csv", mime="text/csv")
