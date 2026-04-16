"""
26-week Uphill Athlete training plan.
Structure: 6 mesocycles of 3-week build + 1-week rest, then a taper week and event week.
Target: 1800 m elevation gain in a single day on October 10, 2026.
"""

from datetime import date, timedelta

import pandas as pd

from config import PLAN_START, EVENT_DATE

# (week, phase, target_elevation_m, target_distance_km, notes)
# Weekly elevation targets ramp 3 weeks then drop for rest, across 6 mesocycles.
# Peak weeks scale toward ~1600 m/week so a full event-day effort (1800 m) is
# well within the athlete's range by October.
_PLAN = [
    # Mesocycle 1 — establish base
    (1,  "Build", 500,  10, "Establish aerobic base. All Zone 1/2 — conversational pace."),
    (2,  "Build", 700,  15, ""),
    (3,  "Build", 900,  18, ""),
    (4,  "Rest",  300,   6, "Recovery week — easy flat walks only."),
    # Mesocycle 2
    (5,  "Build", 600,  15, ""),
    (6,  "Build", 800,  18, ""),
    (7,  "Build", 1000, 22, ""),
    (8,  "Rest",  300,   8, "Recovery week."),
    # Mesocycle 3
    (9,  "Build", 700,  22, ""),
    (10, "Build", 900,  25, ""),
    (11, "Build", 1100, 28, ""),
    (12, "Rest",  350,  10, "Recovery week."),
    # Mesocycle 4 — muscular endurance begins
    (13, "Build", 800,  25, ""),
    (14, "Build", 1000, 28, ""),
    (15, "Build", 1200, 32, "Include one long day targeting 700 m+ in a single push."),
    (16, "Rest",  350,  12, "Recovery week."),
    # Mesocycle 5 — specific endurance
    (17, "Build", 900,  30, ""),
    (18, "Build", 1100, 35, ""),
    (19, "Build", 1400, 38, "Include one big day: 1000 m+ in a single outing."),
    (20, "Rest",  400,  15, "Recovery week."),
    # Mesocycle 6 — peak block
    (21, "Build", 1100, 38, ""),
    (22, "Build", 1400, 40, "Goal simulation day: aim for 1400 m+ in one outing."),
    (23, "Build", 1600, 35, "Begin reducing volume — quality over quantity."),
    (24, "Rest",  400,  18, "Rest week."),
    # Taper & event
    (25, "Taper", 800,  20, "Keep legs fresh. Short, sharp efforts only."),
    (26, "Event", 1800, 25, "Summit day — October 10! Target: 1800 m elevation gain."),
]


def get_plan_df() -> pd.DataFrame:
    rows = []
    cum_elev = 0
    cum_dist = 0.0
    for week, phase, elev, dist, notes in _PLAN:
        cum_elev += elev
        cum_dist += dist
        week_start = PLAN_START + timedelta(weeks=week - 1)
        rows.append({
            "week":               week,
            "phase":              phase,
            "week_start":         week_start,
            "week_end":           week_start + timedelta(days=6),
            "target_elevation_m": elev,
            "target_distance_km": dist,
            "notes":              notes,
            "cum_elevation_m":    cum_elev,
            "cum_distance_km":    cum_dist,
        })
    return pd.DataFrame(rows)


def get_current_week() -> int:
    """Return the plan week number for today (1-26), or 0 if before the plan starts."""
    delta = (date.today() - PLAN_START).days
    if delta < 0:
        return 0
    return min(delta // 7 + 1, 26)


def date_to_week(d: date) -> int | None:
    """Map a calendar date to a plan week number (1-26), or None if outside the plan."""
    delta = (d - PLAN_START).days
    if delta < 0:
        return None
    w = delta // 7 + 1
    return w if 1 <= w <= 26 else None


# Pre-compute once at import time — used by UI and server alike
PLAN_DF = get_plan_df()
