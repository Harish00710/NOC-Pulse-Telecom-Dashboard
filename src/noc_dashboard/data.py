from __future__ import annotations

from pathlib import Path
import pandas as pd
try:
    import streamlit as st
except ModuleNotFoundError:  # Allows the data utilities to be unit-tested without launching Streamlit.
    class _StreamlitCompat:
        @staticmethod
        def cache_data(*_args, **_kwargs):
            def decorator(func):
                return func
            return decorator
    st = _StreamlitCompat()

from .config import DATA_DIR


@st.cache_data(show_spinner=False)
def _read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["timestamp"] if "kpi_history" in path else None)


def load_alarms() -> pd.DataFrame:
    path = DATA_DIR / "alarms.csv"
    df = _read_csv(str(path)).copy()
    required = {"alarm_id", "timestamp", "severity", "cell_id", "issue_type", "description", "status", "region", "assignee"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"alarms.csv is missing required columns: {', '.join(sorted(missing))}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def load_kpi_history() -> pd.DataFrame:
    path = DATA_DIR / "kpi_history.csv"
    df = _read_csv(str(path)).copy()
    required = {"timestamp", "availability_pct", "latency_ms", "throughput_mbps", "packet_loss_pct", "active_users"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"kpi_history.csv is missing required columns: {', '.join(sorted(missing))}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df.dropna(subset=["timestamp"]).sort_values("timestamp")


def load_cells() -> pd.DataFrame:
    path = DATA_DIR / "cells.csv"
    df = _read_csv(str(path)).copy()
    required = {"cell_id", "site_name", "region", "technology", "utilization_pct", "availability_pct"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"cells.csv is missing required columns: {', '.join(sorted(missing))}")
    return df


def current_kpis(history: pd.DataFrame) -> dict[str, float]:
    if history.empty:
        return {"availability": 0.0, "latency_ms": 0.0, "throughput_mbps": 0.0, "packet_loss_pct": 0.0, "active_users": 0.0}
    latest = history.iloc[-1]
    return {
        "availability": float(latest["availability_pct"]),
        "latency_ms": float(latest["latency_ms"]),
        "throughput_mbps": float(latest["throughput_mbps"]),
        "packet_loss_pct": float(latest["packet_loss_pct"]),
        "active_users": float(latest["active_users"]),
    }


def filter_alarms(
    alarms: pd.DataFrame,
    severities: list[str] | None = None,
    statuses: list[str] | None = None,
    regions: list[str] | None = None,
    search: str = "",
) -> pd.DataFrame:
    result = alarms.copy()
    if severities:
        result = result[result["severity"].isin(severities)]
    if statuses:
        result = result[result["status"].isin(statuses)]
    if regions:
        result = result[result["region"].isin(regions)]
    if search.strip():
        needle = search.strip().lower()
        searchable = result[["alarm_id", "cell_id", "issue_type", "description", "region", "assignee"]].fillna("").astype(str)
        mask = searchable.apply(lambda col: col.str.lower().str.contains(needle, regex=False)).any(axis=1)
        result = result[mask]
    return result.sort_values("timestamp", ascending=False)
