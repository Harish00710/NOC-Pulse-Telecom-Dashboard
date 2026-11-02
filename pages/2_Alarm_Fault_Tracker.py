from __future__ import annotations
import streamlit as st

from src.noc_dashboard.data import load_alarms, filter_alarms
from src.noc_dashboard.ui import inject_global_css, render_sidebar_brand, render_metric_card

st.set_page_config(page_title="Alarm & Fault Tracker | NOC Pulse", page_icon="🚨", layout="wide")
inject_global_css(); render_sidebar_brand()
st.markdown('<div class="eyebrow">INCIDENT MANAGEMENT / FAULT CORRELATION</div>', unsafe_allow_html=True)
st.title("Alarm & Fault Tracker")
st.caption("Search, filter, prioritize, and export the simulated alarm feed.")

alarms = load_alarms()
open_alarms = alarms[alarms["status"] == "Open"]
critical = int((open_alarms["severity"] == "Critical").sum())
major = int((open_alarms["severity"] == "Major").sum())
resolved = int((alarms["status"] == "Resolved").sum())
cols = st.columns(4)
for col, args in zip(cols, [("Open alarms", str(len(open_alarms)), "Awaiting action", "negative"), ("Critical", str(critical), "Highest priority", "negative"), ("Major", str(major), "High priority", "neutral"), ("Resolved", str(resolved), "Closed in sample", "positive")]):
    with col: render_metric_card(*args)

st.markdown("### Alarm query")
f1, f2, f3 = st.columns([1, 1, 1.2])
with f1:
    severities = st.multiselect("Severity", ["Critical", "Major", "Minor", "Warning"], default=["Critical", "Major", "Minor", "Warning"])
with f2:
    statuses = st.multiselect("Status", sorted(alarms["status"].dropna().unique()), default=sorted(alarms["status"].dropna().unique()))
with f3:
    regions = st.multiselect("Region", sorted(alarms["region"].dropna().unique()), default=sorted(alarms["region"].dropna().unique()))
search = st.text_input("Search alarm ID, Cell ID, issue type, description, region, or assignee", placeholder="e.g. CELL-CHN-004 or Backhaul")
filtered = filter_alarms(alarms, severities, statuses, regions, search)

st.markdown(f"**{len(filtered)}** matching alarm record(s)")
display_cols = ["timestamp", "alarm_id", "severity", "cell_id", "issue_type", "description", "status", "region", "assignee"]
st.dataframe(filtered[display_cols], hide_index=True, use_container_width=True, column_config={
    "timestamp": st.column_config.DatetimeColumn("Raised at", format="DD MMM YYYY, HH:mm"),
    "severity": st.column_config.TextColumn("Severity"),
    "cell_id": st.column_config.TextColumn("Cell ID"),
})

left, right = st.columns(2)
with left:
    st.markdown('<div class="panel-title">Alarm mix by severity</div>', unsafe_allow_html=True)
    st.bar_chart(filtered["severity"].value_counts().reindex(["Critical", "Major", "Minor", "Warning"], fill_value=0), height=250)
with right:
    st.markdown('<div class="panel-title">Alarms by issue type</div>', unsafe_allow_html=True)
    st.bar_chart(filtered["issue_type"].value_counts().head(8), height=250)

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("Export filtered alarms (CSV)", data=csv, file_name="noc_alarm_export.csv", mime="text/csv")
with st.expander("Alarm handling notes"):
    st.markdown("- **Critical:** investigate immediately; validate service impact and escalate to the owning team.\n- **Major:** prioritize within the active shift and check for correlated alarms.\n- **Minor / Warning:** monitor trends and confirm whether thresholds are persistently breached.\n\nThe sample dataset is illustrative and does not represent a real operator's alarm policy.")
