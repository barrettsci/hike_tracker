"""
Shared data loading and aggregation helpers.

All pages import from here. load_workouts() is cached by Streamlit for 5 min.
Call st.cache_data.clear() + st.rerun() to force a refresh.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import plan as training_plan
import sheets
from config import MEMBERS

PLAN_DF = training_plan.PLAN_DF


@st.cache_data(ttl=300)
def load_workouts() -> pd.DataFrame:
    return sheets.load_hikes()


def weekly_actual(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate workouts to weekly totals per member."""
    if df.empty:
        return pd.DataFrame(columns=["hiker_name", "week", "elevation_gain_m", "distance_km", "duration_minutes"])

    df = df.copy()
    df["week"] = df["hike_date"].apply(training_plan.date_to_week)
    df = df.dropna(subset=["week"])
    df["week"] = df["week"].astype(int)

    return (
        df.groupby(["hiker_name", "week"], as_index=False)
        .agg(
            elevation_gain_m=("elevation_gain_m", "sum"),
            distance_km=("distance_km", "sum"),
            duration_minutes=("duration_minutes", "sum"),
        )
    )


def cumulative_actual(df: pd.DataFrame) -> pd.DataFrame:
    """Running cumulative elevation per member, up to the current plan week only."""
    wa = weekly_actual(df)
    current_week = training_plan.get_current_week()
    # Only fill weeks that have actually started — avoids a flat line into the future
    weeks = range(1, max(current_week, 1) + 1)
    rows = []
    for member in MEMBERS:
        m = wa[wa["hiker_name"] == member].set_index("week")["elevation_gain_m"]
        m = m.reindex(weeks, fill_value=0)
        m_cum = m.cumsum()
        for week, val in m_cum.items():
            rows.append({"hiker_name": member, "week": week, "cum_elevation_m": val})
    return pd.DataFrame(rows)
