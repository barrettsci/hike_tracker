"""
Plotly figure builders — all mobile-optimised.

Every chart:
  • No toolbar (displayModeBar: False)
  • No scroll-zoom
  • dragmode=False (disables pan/zoom gestures)
  • Compact margins, horizontal legend above chart
  • use_container_width=True when rendered via st.plotly_chart()
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from config import MEMBER_COLORS, MEMBERS, PHASE_COLORS

# Shared config dict passed to every st.plotly_chart() call
PLOTLY_CFG: dict = {"displayModeBar": False, "scrollZoom": False, "staticPlot": True}

# Shared layout defaults applied to every figure
_LAYOUT = dict(
    margin=dict(l=8, r=8, t=36, b=8),
    dragmode=False,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=11)),
    font=dict(size=12),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)


def _base_fig(**extra_layout) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(**_LAYOUT, **extra_layout)
    return fig


# ── Group charts ──────────────────────────────────────────────────────────────

def make_group_cumulative(cum_df: pd.DataFrame, plan_df: pd.DataFrame) -> go.Figure:
    """Multi-line: all members cumulative elevation vs plan."""
    fig = _base_fig()

    fig.add_trace(go.Scatter(
        x=plan_df["week"],
        y=plan_df["cum_elevation_m"],
        mode="lines",
        name="Plan",
        line=dict(color="#aaa", dash="dash", width=2),
    ))

    for member in MEMBERS:
        m = cum_df[cum_df["hiker_name"] == member]
        if m.empty or m["cum_elevation_m"].sum() == 0:
            continue
        fig.add_trace(go.Scatter(
            x=m["week"],
            y=m["cum_elevation_m"],
            mode="lines+markers",
            name=member,
            line=dict(color=MEMBER_COLORS.get(member, "#333"), width=2),
            marker=dict(size=4),
        ))

    fig.update_xaxes(title_text="Week", dtick=4, fixedrange=True)
    fig.update_yaxes(title_text="Elevation (m)", fixedrange=True)
    return fig


def make_group_totals(workouts_df: pd.DataFrame, elev_col: str = "elevation_gain_m") -> go.Figure:
    """Bar: total elevation per member."""
    totals = {m: 0 for m in MEMBERS}
    if not workouts_df.empty:
        col = elev_col if elev_col in workouts_df.columns else "elevation_gain_m"
        for m, grp in workouts_df.groupby("hiker_name"):
            if m in totals:
                totals[m] = int(grp[col].sum())

    members = list(totals.keys())
    values = [totals[m] for m in members]
    colors = [MEMBER_COLORS.get(m, "#333") for m in members]

    fig = _base_fig()
    fig.add_trace(go.Bar(
        x=members,
        y=values,
        marker_color=colors,
        showlegend=False,
        text=[f"{v:,} m" for v in values],
        textposition="outside",
    ))

    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(title_text="Elevation (m)", fixedrange=True)
    return fig


def make_group_weekly_stacked(
    weekly_df: pd.DataFrame,
    plan_df: pd.DataFrame,
    elev_col: str = "elevation_gain_m",
) -> go.Figure:
    """Grouped bar: weekly elevation by member + plan target line."""
    fig = _base_fig(barmode="group")

    all_weeks = list(range(1, 27))
    col = elev_col if (not weekly_df.empty and elev_col in weekly_df.columns) else "elevation_gain_m"

    for member in MEMBERS:
        m = weekly_df[weekly_df["hiker_name"] == member] if not weekly_df.empty else pd.DataFrame()
        elev_by_week = m.set_index("week")[col].reindex(all_weeks, fill_value=0) if not m.empty else pd.Series(0, index=all_weeks)
        fig.add_trace(go.Bar(
            x=all_weeks,
            y=elev_by_week.values,
            name=member,
            marker_color=MEMBER_COLORS.get(member, "#333"),
        ))

    fig.add_trace(go.Scatter(
        x=plan_df["week"],
        y=plan_df["target_elevation_m"],
        mode="lines",
        name="Target",
        line=dict(color="#aaa", dash="dash", width=2),
    ))

    fig.update_xaxes(title_text="Week", dtick=4, fixedrange=True)
    fig.update_yaxes(title_text="Elevation (m)", fixedrange=True)
    return fig


def make_scatter(workouts_df: pd.DataFrame, elev_col: str = "elevation_gain_m") -> go.Figure:
    """Scatter: elevation vs distance per workout, coloured by member."""
    fig = _base_fig()

    if workouts_df.empty:
        return fig

    col = elev_col if elev_col in workouts_df.columns else "elevation_gain_m"

    for member in MEMBERS:
        m = workouts_df[workouts_df["hiker_name"] == member]
        if m.empty:
            continue
        fig.add_trace(go.Scatter(
            x=m["distance_km"],
            y=m[col],
            mode="markers",
            name=member,
            marker=dict(color=MEMBER_COLORS.get(member, "#333"), size=8, opacity=0.75),
        ))

    fig.update_xaxes(title_text="Distance (km)", fixedrange=True)
    fig.update_yaxes(title_text="Elevation (m)", fixedrange=True)
    return fig


def make_weekly_target_progress(
    wa: pd.DataFrame,
    plan_df: pd.DataFrame,
    current_week: int,
    elev_col: str = "elevation_gain_m",
) -> go.Figure:
    """Stacked bar: each member's achieved vs remaining elevation for the current week."""
    target_row = plan_df.loc[plan_df["week"] == current_week, "target_elevation_m"]
    target = int(target_row.iloc[0]) if not target_row.empty else 0

    col = elev_col if (not wa.empty and elev_col in wa.columns) else "elevation_gain_m"
    cw_data = wa[wa["week"] == current_week] if not wa.empty else pd.DataFrame()

    achieved, remaining, colors = [], [], []
    for member in MEMBERS:
        row = cw_data[cw_data["hiker_name"] == member]
        val = int(row[col].sum()) if not row.empty else 0
        achieved.append(min(val, target))
        remaining.append(max(target - val, 0))
        colors.append(MEMBER_COLORS.get(member, "#333"))

    fig = _base_fig(barmode="stack")

    fig.add_trace(go.Bar(
        x=MEMBERS,
        y=achieved,
        name="Achieved",
        marker_color=colors,
        text=[f"{v:,} m" if v > 0 else "" for v in achieved],
        textposition="inside",
        insidetextanchor="middle",
    ))
    fig.add_trace(go.Bar(
        x=MEMBERS,
        y=remaining,
        name="Remaining",
        marker_color="#E0E0E0",
        text=[f"{v:,} m" if v > 0 else "" for v in remaining],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#999"),
    ))

    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(title_text="Elevation (m)", fixedrange=True)
    return fig


# ── Training plan chart ───────────────────────────────────────────────────────

def make_plan_overview(plan_df: pd.DataFrame) -> go.Figure:
    """Stacked bar: weekly target elevation by phase + 1800 m event line."""
    fig = _base_fig(barmode="stack")

    for phase, color in PHASE_COLORS.items():
        rows = plan_df[plan_df["phase"] == phase]
        if rows.empty:
            continue
        fig.add_trace(go.Bar(
            x=rows["week"],
            y=rows["target_elevation_m"],
            name=phase,
            marker_color=color,
            hovertemplate="Week %{x}<br>%{y} m<extra></extra>",
        ))

    fig.add_hline(
        y=1800,
        line_dash="dash",
        line_color="#E63946",
        annotation_text="Event: 1800 m",
        annotation_position="top right",
        annotation_font_size=10,
    )

    fig.update_xaxes(title_text="Week", dtick=4, fixedrange=True)
    fig.update_yaxes(title_text="Target elevation (m)", fixedrange=True)
    return fig
