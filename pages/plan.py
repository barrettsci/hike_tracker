"""Page 4 — Training Plan: 26-week plan overview and schedule table."""

from __future__ import annotations

import streamlit as st

from charts import PLOTLY_CFG, make_plan_overview
from data import PLAN_DF

st.title("Plan")
st.caption("26-week Uphill Athlete plan · target 1800 m · 10 Oct 2026")

# ── Plan overview chart ───────────────────────────────────────────────────────

st.plotly_chart(
    make_plan_overview(PLAN_DF),
    use_container_width=True,
    config=PLOTLY_CFG,
)

# ── Week-by-week schedule table ───────────────────────────────────────────────

st.subheader("Week-by-week schedule")

table = (
    PLAN_DF[["week", "phase", "week_start", "week_end",
             "target_elevation_m", "cum_elevation_m", "notes"]]
    .rename(columns={
        "week": "Week",
        "phase": "Phase",
        "week_start": "Start",
        "week_end": "End",
        "target_elevation_m": "Elev target (m)",
        "cum_elevation_m": "Cum elev (m)",
        "notes": "Notes",
    })
)

st.dataframe(table, use_container_width=True, hide_index=True)
