"""
Page 1 — Log a Workout.

Entry point for the Streamlit app. Run with:
    streamlit run Home.py
"""

from __future__ import annotations

import re
from datetime import date

import pandas as pd
import streamlit as st

import sheets
from auth import require_auth
from config import MEMBERS
from data import load_workouts
from ui import show_nav

st.set_page_config(page_title="Bogong 2026", page_icon="⛰", layout="centered")

require_auth()
show_nav("log")

st.title("⛰ Bogong 2026")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_duration(raw: str) -> int | None:
    """Parse 'h:mm' or plain integer minutes. Returns total minutes or None."""
    raw = raw.strip()
    if not raw:
        return None
    m = re.fullmatch(r"(\d+):([0-5]\d)", raw)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    if raw.isdigit():
        return int(raw)
    return None


# ── Log a Workout form ────────────────────────────────────────────────────────

st.subheader("Log a workout")

with st.form("log_form", clear_on_submit=True):
    members = st.multiselect("Members", MEMBERS)

    col1, col2 = st.columns(2)
    log_date = col1.date_input("Date", value=date.today())
    activity = col2.selectbox("Activity", ["Hike", "Walk", "Run", "Ride"])

    col3, col4 = st.columns(2)
    elev = col3.number_input("Elevation gain (m)", min_value=0, max_value=6000, value=None, step=10,
                              placeholder="e.g. 800")
    dist = col4.number_input("Distance (km)", min_value=0.0, max_value=200.0, value=None, step=0.1,
                              placeholder="e.g. 12.5", format="%.1f")

    dur_raw = st.text_input("Duration (h:mm)", placeholder="e.g. 2:30")
    notes = st.text_area("Notes", placeholder="Route, conditions, how it felt…", height=80)

    submitted = st.form_submit_button("Log workout", use_container_width=True, type="primary")

if submitted:
    errors = []
    if not members:
        errors.append("Select at least one member.")
    if elev is None:
        errors.append("Enter an elevation gain.")
    if dist is None:
        errors.append("Enter a distance.")
    dur = _parse_duration(dur_raw)
    if dur is None:
        errors.append("Duration must be in h:mm format (e.g. 2:30).")

    if errors:
        for e in errors:
            st.error(e)
    else:
        try:
            for member in members:
                sheets.append_hike(
                    hiker_name=member,
                    hike_date=log_date,
                    activity_type=activity,
                    elevation_gain_m=elev,
                    distance_km=dist,
                    duration_minutes=dur,
                    notes=notes or "",
                )
            load_workouts.clear()
            names = ", ".join(members)
            st.success(f"Logged for {names} — {int(elev):,} m · {dist} km")
        except Exception as exc:
            st.error(f"Error saving workout: {exc}")


# ── Recent workouts table ─────────────────────────────────────────────────────

st.subheader("Recent workouts")

df = load_workouts()

if df.empty:
    st.info("No workouts logged yet.")
else:
    show = (
        df.sort_values("hike_date", ascending=False)
        .head(30)
        [["hiker_name", "hike_date", "activity_type", "elevation_gain_m",
          "distance_km", "duration_minutes", "notes"]]
        .rename(columns={
            "hiker_name": "Member",
            "hike_date": "Date",
            "activity_type": "Activity",
            "elevation_gain_m": "Elev (m)",
            "distance_km": "Dist (km)",
            "duration_minutes": "Dur (min)",
            "notes": "Notes",
        })
    )
    st.dataframe(show, use_container_width=True, hide_index=True)
