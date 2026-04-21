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
from config import MEMBERS, MEMBER_WEIGHTS_KG

PLAN_DF = training_plan.PLAN_DF


DEFAULT_BODY_WEIGHT_KG = 70.0


def pandolf_adjusted_elev(elev_m: float, pack_kg: float, hiker: str) -> float:
    """Pandolf-equation adjusted elevation for load carriage.

    Scales actual elevation by (body_weight + pack) / body_weight, reflecting
    the proportionally greater metabolic cost of the grade-resistance term.
    Returns elev_m unchanged when no pack is carried.
    """
    if pack_kg <= 0:
        return elev_m
    bw = MEMBER_WEIGHTS_KG.get(hiker, DEFAULT_BODY_WEIGHT_KG)
    return round(elev_m * (bw + pack_kg) / bw)


@st.cache_data(ttl=300)
def load_workouts() -> pd.DataFrame:
    df = sheets.load_hikes()
    if df.empty:
        return df
    df["adjusted_elevation_m"] = df.apply(
        lambda r: pandolf_adjusted_elev(r["elevation_gain_m"], r["pack_weight_kg"], r["hiker_name"]),
        axis=1,
    )
    return df


def weekly_actual(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate workouts to weekly totals per member.

    Returns both raw elevation_gain_m and Pandolf-adjusted_elevation_m columns.
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "hiker_name", "week",
            "elevation_gain_m", "adjusted_elevation_m",
            "distance_km", "duration_minutes",
        ])

    df = df.copy()
    df["week"] = df["hike_date"].apply(training_plan.date_to_week)
    df = df.dropna(subset=["week"])
    df["week"] = df["week"].astype(int)

    adj_col = "adjusted_elevation_m" if "adjusted_elevation_m" in df.columns else "elevation_gain_m"

    return (
        df.groupby(["hiker_name", "week"], as_index=False)
        .agg(
            elevation_gain_m=("elevation_gain_m", "sum"),
            adjusted_elevation_m=(adj_col, "sum"),
            distance_km=("distance_km", "sum"),
            duration_minutes=("duration_minutes", "sum"),
        )
    )


def cumulative_actual(df: pd.DataFrame, elev_col: str = "adjusted_elevation_m") -> pd.DataFrame:
    """Running cumulative elevation per member up to the current plan week.

    elev_col: which weekly column to cumulate ('elevation_gain_m' or 'adjusted_elevation_m').
    """
    wa = weekly_actual(df)
    current_week = training_plan.get_current_week()
    weeks = range(1, max(current_week, 1) + 1)
    src = elev_col if elev_col in wa.columns else "elevation_gain_m"
    rows = []
    for member in MEMBERS:
        m = wa[wa["hiker_name"] == member].set_index("week")[src]
        m = m.reindex(weeks, fill_value=0)
        for week, val in m.cumsum().items():
            rows.append({"hiker_name": member, "week": week, "cum_elevation_m": val})
    return pd.DataFrame(rows)
