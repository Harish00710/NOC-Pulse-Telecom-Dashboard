from __future__ import annotations
import streamlit as st


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
        .stApp { background: #0b1020; color: #e7edf8; }
        [data-testid="stHeader"] { background: rgba(11,16,32,.92); }
        [data-testid="stSidebar"] { background: #10182b; border-right: 1px solid #23304a; }
        [data-testid="stSidebar"] * { color: #dce6f7; }
        h1,h2,h3 { font-family: 'Space Grotesk', sans-serif !important; color: #f4f7fc !important; }
        p, label, .stMarkdown { color: #c4cee0; }
        .eyebrow { color:#59d5c5; font-size:.72rem; font-weight:700; letter-spacing:.17em; margin-bottom:.35rem; }
        .brand { padding: 8px 0 22px 0; }
        .brand-name { font-family:'Space Grotesk'; font-size:1.35rem; font-weight:700; color:#f5f8ff; }
        .brand-sub { color:#8292af; font-size:.72rem; letter-spacing:.12em; }
        .metric-card { background:linear-gradient(145deg,#17243a,#121b2e); border:1px solid #263652; border-radius:14px; padding:17px 18px; min-height:118px; }
        .metric-label { color:#9aabc7; font-size:.78rem; margin-bottom:9px; }
        .metric-value { color:#f4f7fc; font-family:'Space Grotesk'; font-size:1.72rem; font-weight:700; line-height:1.1; }
        .metric-note { color:#899bb8; font-size:.73rem; margin-top:8px; }
        .metric-positive { color:#57d6bd; } .metric-negative { color:#ff7c88; } .metric-neutral { color:#8daeff; }
        .panel-title { font-family:'Space Grotesk'; font-size:1rem; font-weight:600; color:#e9f0fb; margin:8px 0 10px; }
        div[data-testid="stDataFrame"] { border:1px solid #263652; border-radius:10px; overflow:hidden; }
        .stButton>button, .stDownloadButton>button { border-radius:9px; border:1px solid #355174; background:#19304b; color:#eaf4ff; }
        .stButton>button:hover, .stDownloadButton>button:hover { border-color:#54d6c3; color:white; }
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] { background:#121d31; }
        div[data-testid="stAlert"] { border-radius:10px; }
        .small-note { color:#8192ad; font-size:.78rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    st.sidebar.markdown(
        '<div class="brand"><div class="brand-name">◈ NOC PULSE</div><div class="brand-sub">NETWORK OPERATIONS · DEMO</div></div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("**Workspace**")
    st.sidebar.caption("Telecom network assurance")
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div class='small-note'>Environment: <b>SIMULATED DATA</b><br>Build: 1.0.0 · Local demo</div>", unsafe_allow_html=True)


def render_metric_card(label: str, value: str, note: str, tone: str = "neutral") -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note metric-{tone}">{note}</div></div>',
        unsafe_allow_html=True,
    )
