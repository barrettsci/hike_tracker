"""
Mountain Training 2026 — Python Shiny app.
Run locally:  shiny run app.py --reload
Deploy:       rsconnect deploy shiny . --name <account> --title mountain-training
"""

from __future__ import annotations

import os
from datetime import date

import pandas as pd
import plotly.graph_objects as go
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_plotly

import config
import plan as training_plan
import sheets

# ── Convenience aliases ────────────────────────────────────────────────────────
PLAN_DF = training_plan.PLAN_DF
MEMBERS = config.MEMBERS
MC = config.MEMBER_COLORS
PC = config.PHASE_COLORS


# ══════════════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════════════

app_ui = ui.page_navbar(

    # ── Tab 1 · Log a Hike ────────────────────────────────────────────────────
    ui.nav_panel(
        "Log a Hike",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("Record a training walk, run, hike, or ride"),
                ui.input_select("log_hiker", "Your name", choices=MEMBERS),
                ui.input_date("log_date", "Date", value=date.today()),
                ui.input_numeric(
                    "log_elev", "Elevation gain (m)", value=None, min=0, max=6000,
                ),
                ui.input_numeric(
                    "log_dist", "Distance (km)", value=None, min=0, max=200, step=0.1,
                ),
                ui.input_text(
                    "log_dur", "Duration (h:mm)",
                    placeholder="e.g. 2:30",
                ),
                ui.input_select(
                    "log_activity", "Activity type",
                    choices=["Hike", "Walk", "Run", "Ride"],
                ),
                ui.input_text_area(
                    "log_notes", "Notes",
                    placeholder="Route, conditions, how it felt…",
                    rows=3,
                ),
                ui.input_action_button(
                    "log_submit", "Log hike", class_="btn-primary w-100 mt-2",
                ),
                width=300,
            ),
            ui.output_ui("log_status"),
            ui.hr(),
            ui.h5("Recent hikes (all members)"),
            ui.output_data_frame("recent_hikes_table"),
        ),
    ),

    # ── Tab 2 · My Progress ───────────────────────────────────────────────────
    ui.nav_panel(
        "My Progress",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_select("my_hiker", "Member", choices=MEMBERS),
                ui.hr(),
                ui.output_ui("my_stats_panel"),
                width=240,
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Cumulative elevation vs plan"),
                    output_widget("chart_my_cumulative", height="360px"),
                ),
                ui.card(
                    ui.card_header("Weekly elevation vs target"),
                    output_widget("chart_my_weekly", height="360px"),
                ),
            ),
            ui.card(
                ui.card_header("Hike log"),
                ui.output_data_frame("my_hikes_table"),
            ),
        ),
    ),

    # ── Tab 3 · Group Progress ────────────────────────────────────────────────
    ui.nav_panel(
        "Group Progress",
        ui.output_ui("group_header_stats"),
        ui.layout_columns(
            ui.card(
                ui.card_header("Cumulative elevation — all members vs plan"),
                output_widget("chart_group_cumulative", height="380px"),
            ),
            ui.card(
                ui.card_header("Total elevation to date"),
                output_widget("chart_group_totals", height="380px"),
            ),
            col_widths=[8, 4],
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Weekly elevation vs plan target"),
                output_widget("chart_group_weekly", height="340px"),
            ),
            ui.card(
                ui.card_header("Elevation vs distance per hike"),
                output_widget("chart_scatter", height="340px"),
            ),
        ),
        ui.input_action_button(
            "refresh", "↻  Refresh data", class_="btn-outline-secondary btn-sm mt-2",
        ),
    ),

    # ── Tab 4 · Training Plan ─────────────────────────────────────────────────
    ui.nav_panel(
        "Training Plan",
        ui.card(
            ui.card_header(
                "26-week Uphill Athlete plan · target: 1 800 m in a day · October 10 2026"
            ),
            output_widget("chart_plan_overview", height="360px"),
        ),
        ui.card(
            ui.card_header("Full week-by-week schedule"),
            ui.output_data_frame("plan_table"),
        ),
    ),

    title="⛰  Bogong 2026",
    id="page",
    fillable_mobile=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# Server
# ══════════════════════════════════════════════════════════════════════════════

def server(input, output, session):

    # ── Auth ──────────────────────────────────────────────────────────────────

    _PASSWORD = os.environ.get("APP_PASSWORD", "").strip()

    @reactive.effect
    def _show_login():
        if _PASSWORD:
            ui.modal_show(ui.modal(
                ui.p("Enter the group password to continue.", class_="text-muted"),
                ui.input_password("password", "", placeholder="Password"),
                ui.input_action_button(
                    "login_submit", "Enter", class_="btn-primary w-100 mt-2",
                ),
                title="⛰  Bogong 2026",
                footer=None,
                easy_close=False,
            ))

    @reactive.effect
    def _check_password():
        n = input.login_submit()   # reactive dependency — re-runs on every click
        if not n:
            return
        with reactive.isolate():   # read password without adding it as a trigger
            entered = input.password()
        if entered == _PASSWORD:
            ui.modal_remove()
        else:
            ui.notification_show("Incorrect password", type="error", duration=3)

    # ── Reactive data core ────────────────────────────────────────────────────

    _refresh = reactive.value(0)

    @reactive.calc
    def hikes() -> pd.DataFrame:
        _refresh.get()          # take a dependency so re-runs on refresh
        return sheets.load_hikes()

    @reactive.calc
    def weekly_actual() -> pd.DataFrame:
        df = hikes()
        if df.empty:
            return pd.DataFrame(
                columns=["hiker_name", "week", "elevation_gain_m", "distance_km"]
            )
        df = df.copy()
        df["week"] = df["hike_date"].apply(training_plan.date_to_week)
        df = df.dropna(subset=["week"]).copy()
        df["week"] = df["week"].astype(int)
        return df.groupby(["hiker_name", "week"], as_index=False).agg(
            elevation_gain_m=("elevation_gain_m", "sum"),
            distance_km=("distance_km", "sum"),
            duration_minutes=("duration_minutes", "sum"),
        )

    @reactive.calc
    def cumulative_actual() -> pd.DataFrame:
        wa = weekly_actual()
        current_week = training_plan.get_current_week()
        if wa.empty or current_week == 0:
            return pd.DataFrame(
                columns=["hiker_name", "week", "cum_elevation_m", "cum_distance_km"]
            )
        all_weeks = list(range(1, current_week + 1))
        rows = []
        for member in MEMBERS:
            m = wa[wa["hiker_name"] == member].set_index("week")
            m_full = m.reindex(all_weeks, fill_value=0)
            for w in all_weeks:
                rows.append({
                    "hiker_name":      member,
                    "week":            w,
                    "cum_elevation_m": float(m_full.loc[w, "elevation_gain_m"]) if w in m_full.index else 0.0,
                    "cum_distance_km": float(m_full.loc[w, "distance_km"]) if w in m_full.index else 0.0,
                })
        df = pd.DataFrame(rows)
        df["cum_elevation_m"] = df.groupby("hiker_name")["cum_elevation_m"].cumsum()
        df["cum_distance_km"] = df.groupby("hiker_name")["cum_distance_km"].cumsum()
        return df

    # ── Log a hike ────────────────────────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.log_submit)
    def _submit_hike():
        missing = [
            name for name, val in [
                ("Elevation gain", input.log_elev()),
                ("Distance", input.log_dist()),
            ] if val is None
        ]
        if missing:
            ui.notification_show(
                f"Please fill in: {', '.join(missing)}",
                type="warning", duration=5,
            )
            return
        dur = _parse_duration(input.log_dur())
        if dur is None:
            ui.notification_show(
                "Duration must be in h:mm format (e.g. 2:30)",
                type="warning", duration=5,
            )
            return
        try:
            sheets.append_hike(
                hiker_name=input.log_hiker(),
                hike_date=input.log_date(),
                activity_type=input.log_activity(),
                elevation_gain_m=input.log_elev(),
                distance_km=input.log_dist(),
                duration_minutes=dur,
                notes=input.log_notes() or "",
            )
            _refresh.set(_refresh.get() + 1)
            ui.notification_show(
                f"Logged! {int(input.log_elev()):,} m · {input.log_dist()} km",
                type="message",
                duration=4,
            )
        except Exception as e:
            ui.notification_show(f"Error saving hike: {e}", type="error", duration=8)

    @reactive.effect
    @reactive.event(input.refresh)
    def _manual_refresh():
        _refresh.set(_refresh.get() + 1)

    @output
    @render.ui
    def log_status():
        return ui.p("")   # notifications carry the feedback

    @output
    @render.data_frame
    def recent_hikes_table():
        df = hikes()
        if df.empty:
            return render.DataGrid(pd.DataFrame(
                columns=["Hiker", "Date", "Activity", "Elevation (m)",
                         "Distance (km)", "Duration (min)", "Notes"]
            ))
        show = (
            df.sort_values("hike_date", ascending=False)
            .head(30)
            [["hiker_name", "hike_date", "activity_type", "elevation_gain_m",
              "distance_km", "duration_minutes", "notes"]]
            .rename(columns={
                "hiker_name":      "Hiker",
                "hike_date":       "Date",
                "activity_type":   "Activity",
                "elevation_gain_m":"Elevation (m)",
                "distance_km":     "Distance (km)",
                "duration_minutes":"Duration (min)",
                "notes":           "Notes",
            })
        )
        return render.DataGrid(show, width="100%")

    # ── My Progress ───────────────────────────────────────────────────────────

    @output
    @render.ui
    def my_stats_panel():
        hiker = input.my_hiker()
        wa = weekly_actual()
        cw = training_plan.get_current_week()

        m_wa = wa[wa["hiker_name"] == hiker] if not wa.empty else pd.DataFrame()
        total_elev = int(m_wa["elevation_gain_m"].sum()) if not m_wa.empty else 0
        total_dist = round(float(m_wa["distance_km"].sum()), 1) if not m_wa.empty else 0.0
        n_hikes = int(hikes()[hikes()["hiker_name"] == hiker].shape[0]) if not hikes().empty else 0

        plan_cum = int(
            PLAN_DF.loc[PLAN_DF["week"] == cw, "cum_elevation_m"].iloc[0]
        ) if cw > 0 else 0

        diff = total_elev - plan_cum
        status = f"+{diff:,} m ahead" if diff >= 0 else f"{diff:,} m behind"
        status_color = "green" if diff >= 0 else "#c0392b"

        week_target = int(
            PLAN_DF.loc[PLAN_DF["week"] == cw, "target_elevation_m"].iloc[0]
        ) if cw > 0 else 0
        week_done = int(
            m_wa.loc[m_wa["week"] == cw, "elevation_gain_m"].sum()
        ) if not m_wa.empty else 0

        return ui.div(
            _stat("Total elevation", f"{total_elev:,} m"),
            _stat("Total distance",  f"{total_dist} km"),
            _stat("Hikes logged",    str(n_hikes)),
            ui.hr(),
            _stat("vs plan (cumulative)",
                  ui.span(status, style=f"color:{status_color};font-weight:600")),
            _stat(f"Week {cw} progress",
                  f"{week_done:,} / {week_target:,} m"),
        )

    @output
    @render_plotly
    def chart_my_cumulative():
        hiker = input.my_hiker()
        cum = cumulative_actual()
        cw  = training_plan.get_current_week()
        fig = go.Figure()

        # Plan line (full 26 weeks)
        fig.add_trace(go.Scatter(
            x=PLAN_DF["week"], y=PLAN_DF["cum_elevation_m"],
            name="Plan target", mode="lines",
            line=dict(color="#888", dash="dash", width=2),
            hovertemplate="Week %{x}<br>Plan: %{y:,} m<extra></extra>",
        ))

        # Member area
        m = cum[cum["hiker_name"] == hiker] if not cum.empty else pd.DataFrame()
        if not m.empty and m["cum_elevation_m"].max() > 0:
            fig.add_trace(go.Scatter(
                x=m["week"], y=m["cum_elevation_m"],
                name=hiker, mode="lines",
                line=dict(color=MC.get(hiker, "#555"), width=3),
                fill="tozeroy",
                fillcolor=_hex_to_rgba(MC.get(hiker, "#555555")),
                hovertemplate=f"{hiker}<br>Week %{{x}}<br>%{{y:,}} m<extra></extra>",
            ))

        _add_vline(fig, cw)
        fig.update_layout(**_layout(
            yaxis_title="Cumulative elevation (m)",
            xaxis=dict(title="Training week", range=[0.5, 26.5], showgrid=False),
        ))
        return fig

    @output
    @render_plotly
    def chart_my_weekly():
        hiker = input.my_hiker()
        wa    = weekly_actual()
        cw    = training_plan.get_current_week()
        m     = wa[wa["hiker_name"] == hiker] if not wa.empty else pd.DataFrame()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=m["week"] if not m.empty else [],
            y=m["elevation_gain_m"] if not m.empty else [],
            name=hiker,
            marker_color=MC.get(hiker, "#555"),
            hovertemplate="Week %{x}<br>%{y:,} m<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=PLAN_DF["week"], y=PLAN_DF["target_elevation_m"],
            name="Weekly target", mode="lines",
            line=dict(color="#888", dash="dash", width=2),
            hovertemplate="Week %{x}<br>Target: %{y:,} m<extra></extra>",
        ))
        _add_vline(fig, cw)
        fig.update_layout(**_layout(
            yaxis_title="Elevation gain (m)",
            xaxis=dict(title="Training week", range=[0.5, 26.5], showgrid=False),
        ))
        return fig

    @output
    @render.data_frame
    def my_hikes_table():
        hiker = input.my_hiker()
        df = hikes()
        if df.empty:
            return render.DataGrid(pd.DataFrame())
        m = (
            df[df["hiker_name"] == hiker]
            .sort_values("hike_date", ascending=False)
            [["hike_date", "activity_type", "elevation_gain_m",
              "distance_km", "duration_minutes", "notes"]]
            .rename(columns={
                "hike_date":       "Date",
                "activity_type":   "Activity",
                "elevation_gain_m":"Elevation (m)",
                "distance_km":     "Distance (km)",
                "duration_minutes":"Duration (min)",
                "notes":           "Notes",
            })
        )
        return render.DataGrid(m, width="100%")

    # ── Group Progress ────────────────────────────────────────────────────────

    @output
    @render.ui
    def group_header_stats():
        cw        = training_plan.get_current_week()
        days_left = max(0, (config.EVENT_DATE - date.today()).days)
        phase     = PLAN_DF.loc[PLAN_DF["week"] == cw, "phase"].iloc[0] if cw > 0 else "—"
        cum_tgt   = int(PLAN_DF.loc[PLAN_DF["week"] == cw, "cum_elevation_m"].iloc[0]) if cw > 0 else 0
        return ui.layout_columns(
            _value_card("Days to climb",      str(days_left),     "Oct 10 2026"),
            _value_card("Current week",        f"Week {cw}",       phase),
            _value_card("Plan target (cumul)", f"{cum_tgt:,} m",   "elevation to date"),
            col_widths=[4, 4, 4],
        )

    @output
    @render_plotly
    def chart_group_cumulative():
        cum = cumulative_actual()
        cw  = training_plan.get_current_week()
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=PLAN_DF["week"], y=PLAN_DF["cum_elevation_m"],
            name="Plan", mode="lines",
            line=dict(color="#555", dash="dash", width=2.5),
            hovertemplate="Week %{x}<br>Plan: %{y:,} m<extra></extra>",
        ))

        for member in MEMBERS:
            m = cum[cum["hiker_name"] == member] if not cum.empty else pd.DataFrame()
            if m.empty or m["cum_elevation_m"].max() == 0:
                continue
            fig.add_trace(go.Scatter(
                x=m["week"], y=m["cum_elevation_m"],
                name=member, mode="lines+markers",
                line=dict(color=MC.get(member, "#888"), width=2.5),
                marker=dict(size=5),
                hovertemplate=f"{member}<br>Week %{{x}}<br>%{{y:,}} m<extra></extra>",
            ))

        _add_vline(fig, cw)
        fig.update_layout(**_layout(
            yaxis_title="Cumulative elevation (m)",
            xaxis=dict(title="Training week", range=[0.5, 26.5], showgrid=False),
            legend=dict(orientation="h", y=1.08, x=0),
        ))
        return fig

    @output
    @render_plotly
    def chart_group_totals():
        wa  = weekly_actual()
        cw  = training_plan.get_current_week()
        plan_cum = int(
            PLAN_DF.loc[PLAN_DF["week"] == cw, "cum_elevation_m"].iloc[0]
        ) if cw > 0 else 0

        totals = [
            {
                "member": m,
                "elevation_m": int(
                    wa.loc[wa["hiker_name"] == m, "elevation_gain_m"].sum()
                ) if not wa.empty else 0,
            }
            for m in MEMBERS
        ]
        df_t = pd.DataFrame(totals)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_t["member"], y=df_t["elevation_m"],
            marker_color=[MC.get(m, "#888") for m in df_t["member"]],
            text=df_t["elevation_m"].apply(lambda v: f"{v:,} m"),
            textposition="outside",
            hovertemplate="%{x}<br>%{y:,} m<extra></extra>",
            showlegend=False,
        ))
        if plan_cum > 0:
            fig.add_hline(
                y=plan_cum, line_dash="dash", line_color="#555",
                annotation_text=f"Plan: {plan_cum:,} m",
                annotation_position="top right",
            )
        fig.update_layout(**_layout(
            yaxis_title="Total elevation (m)",
            xaxis=dict(title="", showgrid=False),
        ))
        return fig

    @output
    @render_plotly
    def chart_group_weekly():
        wa  = weekly_actual()
        cw  = training_plan.get_current_week()
        fig = go.Figure()

        for member in MEMBERS:
            m = wa[wa["hiker_name"] == member] if not wa.empty else pd.DataFrame()
            fig.add_trace(go.Bar(
                x=m["week"] if not m.empty else [],
                y=m["elevation_gain_m"] if not m.empty else [],
                name=member,
                marker_color=MC.get(member, "#888"),
                hovertemplate=f"{member}<br>Week %{{x}}<br>%{{y:,}} m<extra></extra>",
            ))

        fig.add_trace(go.Scatter(
            x=PLAN_DF["week"], y=PLAN_DF["target_elevation_m"],
            name="Target", mode="lines",
            line=dict(color="#333", dash="dash", width=2),
            hovertemplate="Week %{x}<br>Target: %{y:,} m<extra></extra>",
        ))
        _add_vline(fig, cw)
        fig.update_layout(**_layout(
            yaxis_title="Elevation gain (m)",
            xaxis=dict(title="Training week", range=[0.5, 26.5], showgrid=False),
            barmode="group",
            legend=dict(orientation="h", y=1.08, x=0),
        ))
        return fig

    @output
    @render_plotly
    def chart_scatter():
        df = hikes()
        fig = go.Figure()
        if df.empty:
            fig.add_annotation(
                text="No hikes logged yet",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="#aaa"),
            )
        else:
            for member in MEMBERS:
                m = df[df["hiker_name"] == member]
                if m.empty:
                    continue
                fig.add_trace(go.Scatter(
                    x=m["distance_km"], y=m["elevation_gain_m"],
                    name=member, mode="markers",
                    marker=dict(color=MC.get(member, "#888"), size=9, opacity=0.8),
                    customdata=m[["hike_date", "duration_minutes", "notes"]].values,
                    hovertemplate=(
                        f"<b>{member}</b><br>"
                        "Distance: %{x} km<br>"
                        "Elevation: %{y:,} m<br>"
                        "Date: %{customdata[0]}<br>"
                        "Duration: %{customdata[1]} min<br>"
                        "Notes: %{customdata[2]}"
                        "<extra></extra>"
                    ),
                ))
        fig.update_layout(**_layout(
            xaxis=dict(title="Distance (km)", showgrid=True, gridcolor="#eee"),
            yaxis_title="Elevation gain (m)",
            legend=dict(orientation="h", y=1.08, x=0),
        ))
        return fig

    # ── Training Plan ─────────────────────────────────────────────────────────

    @output
    @render_plotly
    def chart_plan_overview():
        cw  = training_plan.get_current_week()
        fig = go.Figure()

        for phase, color in PC.items():
            rows = PLAN_DF[PLAN_DF["phase"] == phase]
            if rows.empty:
                continue
            fig.add_trace(go.Bar(
                x=rows["week"], y=rows["target_elevation_m"],
                name=phase, marker_color=color,
                hovertemplate=(
                    "Week %{x} · " + phase +
                    "<br>Target: %{y:,} m<extra></extra>"
                ),
            ))

        fig.add_hline(
            y=1800, line_dash="dot", line_color="#E63946",
            annotation_text="Event day: 1 800 m",
            annotation_position="top right",
            annotation_font_color="#E63946",
        )
        _add_vline(fig, cw)
        fig.update_layout(**_layout(
            yaxis_title="Weekly elevation target (m)",
            xaxis=dict(title="Training week", range=[0.5, 26.5], showgrid=False),
            barmode="stack",
            legend=dict(orientation="h", y=1.08, x=0),
        ))
        return fig

    @output
    @render.data_frame
    def plan_table():
        cw  = training_plan.get_current_week()
        df  = PLAN_DF.copy()
        df.insert(0, "Now", df["week"].apply(lambda w: "▶" if w == cw else ""))
        df["week_start"] = df["week_start"].astype(str)
        df["week_end"]   = df["week_end"].astype(str)
        df = df.rename(columns={
            "week":               "Week",
            "phase":              "Phase",
            "week_start":         "From",
            "week_end":           "To",
            "target_elevation_m": "Elev target (m)",
            "target_distance_km": "Dist target (km)",
            "cum_elevation_m":    "Cumul. elev (m)",
            "notes":              "Notes",
        })[["Now","Week","Phase","From","To",
            "Elev target (m)","Dist target (km)","Cumul. elev (m)","Notes"]]
        return render.DataGrid(df, width="100%")


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _parse_duration(text: str) -> int | None:
    """Parse 'h:mm' or plain minutes into total minutes. Returns None if invalid."""
    text = (text or "").strip()
    if not text:
        return None
    if ":" in text:
        parts = text.split(":", 1)
        try:
            return int(parts[0]) * 60 + int(parts[1])
        except ValueError:
            return None
    try:
        return int(text)
    except ValueError:
        return None


def _add_vline(fig: go.Figure, current_week: int) -> None:
    if 1 <= current_week <= 26:
        fig.add_vline(
            x=current_week, line_dash="dot", line_color="#bbb", line_width=1.5,
            annotation_text=f"Wk {current_week}",
            annotation_position="top right",
            annotation_font_size=10,
            annotation_font_color="#999",
        )


def _layout(**overrides) -> dict:
    base = dict(
        margin=dict(l=50, r=20, t=30, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="system-ui, -apple-system, sans-serif", size=12),
        hovermode="x unified",
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0", zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    base.update(overrides)
    return base


def _stat(label: str, value) -> ui.Tag:
    return ui.p(
        ui.span(label, class_="text-muted", style="font-size:0.8rem;"),
        ui.br(),
        value if isinstance(value, ui.Tag) else ui.strong(str(value)),
        style="margin-bottom:0.6rem;",
    )


def _hex_to_rgba(hex_color: str, alpha: float = 0.15) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _value_card(title: str, value: str, subtitle: str) -> ui.Tag:
    return ui.card(
        ui.card_body(
            ui.p(title, class_="text-muted mb-1", style="font-size:0.8rem;"),
            ui.h4(value, class_="mb-0"),
            ui.p(subtitle, class_="text-muted mt-1 mb-0", style="font-size:0.8rem;"),
        ),
        class_="text-center",
    )


# ══════════════════════════════════════════════════════════════════════════════
app = App(app_ui, server)
