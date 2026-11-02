from __future__ import annotations
import tempfile
from pathlib import Path
import streamlit as st
import pandas as pd

from src.noc_dashboard.config import MAX_PCAP_MB
from src.noc_dashboard.packet_analyzer import analyze_capture
from src.noc_dashboard.ui import inject_global_css, render_sidebar_brand, render_metric_card

st.set_page_config(page_title="Packet Analyzer | NOC Pulse", page_icon="🧪", layout="wide")
inject_global_css(); render_sidebar_brand()
st.markdown('<div class="eyebrow">PACKET INSPECTION / TRAFFIC VISIBILITY</div>', unsafe_allow_html=True)
st.title("Wireshark Packet Analyzer")
st.caption("Upload a packet capture to inspect protocols, endpoints, packet sizes, and transport metadata.")
st.info("For full protocol support, install Wireshark and ensure `tshark.exe` is on PATH. Without it, NOC Pulse uses a built-in fallback for classic Ethernet `.pcap` files. `.pcapng` requires TShark.")

uploaded = st.file_uploader("Upload packet capture", type=["pcap", "pcapng", "cap"], help=f"Maximum upload size: {MAX_PCAP_MB} MB")
if uploaded is None:
    st.markdown("### Try the included sample capture")
    sample_path = Path(__file__).resolve().parents[1] / "data" / "sample" / "demo_traffic.pcap"
    if sample_path.exists():
        if st.button("Analyze included demo_traffic.pcap", type="primary"):
            with open(sample_path, "rb") as fh:
                payload = fh.read()
            st.session_state["capture_bytes"] = payload
            st.session_state["capture_name"] = sample_path.name
            st.rerun()
    st.caption("A small generated PCAP is included in data/sample for testing the analyzer without a live capture.")
else:
    size_mb = uploaded.size / (1024 * 1024)
    if size_mb > MAX_PCAP_MB:
        st.error(f"File is {size_mb:.1f} MB. The configured upload limit is {MAX_PCAP_MB} MB.")
        st.stop()
    st.session_state["capture_bytes"] = uploaded.getvalue()
    st.session_state["capture_name"] = uploaded.name

if "capture_bytes" in st.session_state:
    raw = st.session_state["capture_bytes"]
    capture_name = st.session_state.get("capture_name", "uploaded_capture.pcap")
    if st.button("Run packet analysis", type="primary"):
        suffix = ".pcapng" if capture_name.lower().endswith(".pcapng") else ".pcap"
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(raw)
                tmp_path = tmp.name
            with st.spinner("Reading capture and extracting packet metadata..."):
                frame, method, note = analyze_capture(tmp_path)
            st.session_state["packet_frame"] = frame
            st.session_state["packet_method"] = method
            st.session_state["packet_note"] = note
            st.session_state["packet_name"] = capture_name
        except Exception as exc:
            st.error(str(exc))
        finally:
            try: Path(tmp_path).unlink(missing_ok=True)
            except Exception: pass

if "packet_frame" in st.session_state:
    frame: pd.DataFrame = st.session_state["packet_frame"]
    st.success(f"Analysis complete · {st.session_state['packet_method']}")
    st.caption(st.session_state["packet_note"])
    if frame.empty:
        st.warning("No packets were decoded from this capture.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        protocol_count = frame["protocol"].nunique()
        for col, args in zip([c1,c2,c3,c4], [("Packets", f"{len(frame):,}", "Decoded records"), ("Protocols", str(protocol_count), "Distinct protocols"), ("Bytes", f"{int(frame['length'].sum()):,}", "Captured frame bytes"), ("Endpoints", str(pd.concat([frame['source'], frame['destination']]).nunique()), "Unique source / destination")]):
            with col: render_metric_card(*args)
        left, right = st.columns(2)
        with left:
            st.markdown('<div class="panel-title">Protocol distribution</div>', unsafe_allow_html=True)
            st.bar_chart(frame["protocol"].value_counts().head(12), height=260)
        with right:
            st.markdown('<div class="panel-title">Top source endpoints</div>', unsafe_allow_html=True)
            st.bar_chart(frame["source"].value_counts().head(10), height=260)
        st.markdown("### Packet details")
        protocol_filter = st.multiselect("Protocol filter", sorted(frame["protocol"].dropna().unique()), default=sorted(frame["protocol"].dropna().unique()))
        filtered = frame[frame["protocol"].isin(protocol_filter)]
        st.dataframe(filtered, hide_index=True, use_container_width=True, column_config={"timestamp": st.column_config.DatetimeColumn("Timestamp", format="HH:mm:ss.SSS")})
        st.download_button("Download decoded packet summary (CSV)", data=filtered.to_csv(index=False).encode("utf-8"), file_name="packet_analysis.csv", mime="text/csv")
        if len(frame) >= 5000:
            st.warning("The display is limited to the first 5,000 packets to keep local analysis responsive.")
