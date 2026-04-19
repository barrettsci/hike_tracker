"""Page 2 — My Progress: personal stats + charts for a single member."""

from __future__ import annotations

import streamlit as st

import plan as training_plan
from auth import require_auth
from charts import PLOTLY_CFG, make_cumulative_chart, make_weekly_chart
from config import MEMBERS
from data import PLAN_DF, cumulative_actual, load_workouts, weekly_actual

st.set_page_config(page_title="My Progress · Bogong 2026", page_icon="⛰", layout="centered")
require_auth()

st.title("My Progress")

# ── Member selector ───────────────────────────────────────────────────────────

member = st.selectbox("Member", MEMBERS, label_visibility="collapsed")

# ── Load + aggregate data ─────────────────────────────────────────────────────

df = load_workouts()
wa = weekly_actual(df)
ca = cumulative_actual(df)

cw = training_plan.get_current_week()

m_wa = wa[wa["hiker_name"] == member] if not wa.empty else wa
m_workouts = df[df["hiker_name"] == member] if not df.empty else df

total_elev = int(m_wa["elevation_gain_m"].sum()) if not m_wa.empty else 0
total_dist = round(float(m_wa["distance_km"].sum()), 1) if not m_wa.empty else 0.0
n_workouts = len(m_workouts)

plan_cum_to_date = int(
    PLAN_DF.loc[PLAN_DF["week"] == cw, "cum_elevation_m"].iloc[0]
) if cw > 0 and not PLAN_DF[PLAN_DF["week"] == cw].empty else 0

diff = total_elev - plan_cum_to_date
diff_label = f"+{diff:,} m ahead" if diff >= 0 else f"{diff:,} m behind"

week_target = int(
    PLAN_DF.loc[PLAN_DF["week"] == cw, "target_elevation_m"].iloc[0]
) if cw > 0 and not PLAN_DF[PLAN_DF["week"] == cw].empty else 0
week_done = int(m_wa.loc[m_wa["week"] == cw, "elevation_gain_m"].sum()) if not m_wa.empty else 0

# ── Stats metrics ─────────────────────────────────────────────────────────────

col1, col2 = st.columns(2)
col1.metric("Total elevation", f"{total_elev:,} m")
col2.metric("Total distance", f"{total_dist} km")

col3, col4 = st.columns(2)
col3.metric("Workouts", n_workouts)
col4.metric("vs plan", diff_label, delta_color="normal" if diff >= 0 else "inverse")

if cw > 0:
    st.metric(f"Week {cw} progress", f"{week_done:,} / {week_target:,} m",
              delta=f"{week_done - week_target:+,} m",
              delta_color="normal" if week_done >= week_target else "inverse")

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────

st.subheader("Cumulative elevation vs plan")
st.plotly_chart(
    make_cumulative_chart(ca, PLAN_DF, member),
    use_container_width=True,
    config=PLOTLY_CFG,
)

st.subheader("Weekly elevation vs target")
st.plotly_chart(
    make_weekly_chart(wa, PLAN_DF, member),
    use_container_width=True,
    config=PLOTLY_CFG,
)

# ── Workout log table ─────────────────────────────────────────────────────────

st.subheader("Workout log")

if m_workouts.empty:
    st.info("No workouts logged yet.")
else:
    show = (
        m_workouts.sort_values("hike_date", ascending=False)
        [["hike_date", "activity_type", "elevation_gain_m",
          "distance_km", "duration_minutes", "notes"]]
        .rename(columns={
            "hike_date": "Date",
            "activity_type": "Activity",
            "elevation_gain_m": "Elev (m)",
            "distance_km": "Dist (km)",
            "duration_minutes": "Dur (min)",
            "notes": "Notes",
        })
    )
    st.dataframe(show, use_container_width=True, hide_index=True)
