"""Page 2 — Progress: team-wide stats and charts."""

from __future__ import annotations

from datetime import date

import pandas as pd
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
from config import EVENT_DATE, MEMBERS
from data import PLAN_DF, cumulative_actual, load_workouts, weekly_actual
from ui import show_nav

st.set_page_config(page_title="Progress · Bogong 2026", page_icon="⛰", layout="centered")
require_auth()
show_nav("progress")

st.title("Progress")

# ── Load data ─────────────────────────────────────────────────────────────────

df: pd.DataFrame = load_workouts()
wa = weekly_actual(df)
ca = cumulative_actual(df)

cw = training_plan.get_current_week()
days_left = (EVENT_DATE - date.today()).days


# ── Header stats ──────────────────────────────────────────────────────────────

st.markdown(
    "<style>[data-testid='stMetricValue']{font-size:1.1rem!important}"
    "[data-testid='stMetricLabel']{font-size:0.75rem!important}</style>",
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
col1.metric("Days to climb", days_left)
col2.metric("Current week", f"Week {cw}" if cw > 0 else "—")

st.divider()

# ── Leaderboard ───────────────────────────────────────────────────────────────

st.subheader("Leaderboard")

pw = cw - 1

if cw > 1:
    past_wa = wa[wa["week"] < cw]

    # Overall — most elevation across all completed weeks
    totals = past_wa.groupby("hiker_name")["elevation_gain_m"].sum()
    for m in MEMBERS:
        if m not in totals.index:
            totals[m] = 0
    leader_elev = totals.idxmax()
    leader_elev_val = int(totals.max())

    # Overall — closest to plan (cumulative |actual − planned| per week)
    plan_weekly = PLAN_DF[PLAN_DF["week"] < cw].set_index("week")["target_elevation_m"]
    deviations: dict[str, float] = {}
    for member in MEMBERS:
        actual = (
            past_wa[past_wa["hiker_name"] == member]
            .set_index("week")["elevation_gain_m"]
            .reindex(range(1, cw), fill_value=0)
        )
        deviations[member] = (actual - plan_weekly).abs().sum()
    dev_series = pd.Series(deviations)
    leader_plan = dev_series.idxmin()
    leader_plan_dev = int(dev_series.min())

    st.caption("Overall")
    st.markdown(
        f"- **Most elevation** — {leader_elev} ({leader_elev_val:,} m)\n"
        f"- **Closest to plan** — {leader_plan} ({leader_plan_dev:,} m deviation)"
    )

if pw >= 1:
    pw_wa = wa[wa["week"] == pw]

    # Last week — most elevation
    pw_totals = pw_wa.groupby("hiker_name")["elevation_gain_m"].sum()
    for m in MEMBERS:
        if m not in pw_totals.index:
            pw_totals[m] = 0
    pw_leader_elev = pw_totals.idxmax()
    pw_leader_elev_val = int(pw_totals.max())

    # Last week — closest to plan
    pw_plan_target = int(PLAN_DF.loc[PLAN_DF["week"] == pw, "target_elevation_m"].iloc[0])
    pw_deviations = {m: abs(int(pw_totals.get(m, 0)) - pw_plan_target) for m in MEMBERS}
    pw_leader_plan = min(pw_deviations, key=pw_deviations.__getitem__)
    pw_leader_plan_dev = pw_deviations[pw_leader_plan]

    st.caption(f"Week {pw}")
    st.markdown(
        f"- **Most elevation** — {pw_leader_elev} ({pw_leader_elev_val:,} m)\n"
        f"- **Closest to plan** — {pw_leader_plan} ({pw_leader_plan_dev:,} m deviation)"
    )

if cw <= 1:
    st.caption("Not enough completed weeks yet.")

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────

st.subheader("Cumulative elevation vs plan")
st.plotly_chart(
    make_group_cumulative(ca, PLAN_DF),
    use_container_width=True,
    config=PLOTLY_CFG,
)

st.subheader("Total elevation to date")
st.plotly_chart(
    make_group_totals(df),
    use_container_width=True,
    config=PLOTLY_CFG,
)

st.subheader("Weekly elevation vs plan")
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
