"""Page 3 — Group Progress: team-wide stats and charts."""

from __future__ import annotations

from datetime import date

import streamlit as st

import plan as training_plan
from auth import require_auth
from charts import (
    PLOTLY_CFG,
    make_group_cumulative,
    make_group_totals,
    make_group_weekly_stacked,
    make_scatter,
)
from config import EVENT_DATE
from data import PLAN_DF, cumulative_actual, load_workouts, weekly_actual

st.set_page_config(page_title="Group Progress · Bogong 2026", page_icon="⛰", layout="centered")
require_auth()

st.title("Group Progress")

# ── Load data ─────────────────────────────────────────────────────────────────

df = load_workouts()
wa = weekly_actual(df)
ca = cumulative_actual(df)

cw = training_plan.get_current_week()
days_left = (EVENT_DATE - date.today()).days

plan_cum_target = int(
    PLAN_DF.loc[PLAN_DF["week"] == cw, "cum_elevation_m"].iloc[0]
) if cw > 0 and not PLAN_DF[PLAN_DF["week"] == cw].empty else 0

# ── Header stats ──────────────────────────────────────────────────────────────

col1, col2, col3 = st.columns(3)
col1.metric("Days to climb", days_left)
col2.metric("Current week", f"Week {cw}" if cw > 0 else "—")
col3.metric("Plan target to date", f"{plan_cum_target:,} m")

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────

st.subheader("Cumulative elevation — all members vs plan")
st.plotly_chart(
    make_group_cumulative(ca, PLAN_DF),
    use_container_width=True,
    config=PLOTLY_CFG,
)

st.subheader("Total elevation to date")
st.plotly_chart(
    make_group_totals(df, plan_cum_target),
    use_container_width=True,
    config=PLOTLY_CFG,
)

st.subheader("Weekly elevation vs plan target")
st.plotly_chart(
    make_group_weekly_stacked(wa, PLAN_DF),
    use_container_width=True,
    config=PLOTLY_CFG,
)

st.subheader("Elevation vs distance per workout")
st.plotly_chart(
    make_scatter(df),
    use_container_width=True,
    config=PLOTLY_CFG,
)

# ── Refresh ───────────────────────────────────────────────────────────────────

if st.button("Refresh data", use_container_width=True):
    load_workouts.clear()
    st.rerun()
