from datetime import date

# ── Update these with real names before sharing ────────────────────────────────
MEMBERS = ["Marina", "Miheka", "Hannah", "Nick", "Luke"]

MEMBER_COLORS = {
    MEMBERS[0]: "#E63946",
    MEMBERS[1]: "#2196F3",
    MEMBERS[2]: "#4CAF50",
    MEMBERS[3]: "#FF9800",
    MEMBERS[4]: "#6A00FF",
}

PHASE_COLORS = {
    "Build": "#5C9BD4",
    "Rest":  "#81C784",
    "Taper": "#FFB74D",
    "Event": "#E63946",
}

PLAN_START = date(2026, 4, 13)   # Monday of week 1
EVENT_DATE = date(2026, 10, 10)  # Summit day
HIKES_SHEET = "hikes"

# Body weights used for Pandolf pack-adjusted elevation. Update as needed.
MEMBER_WEIGHTS_KG: dict[str, float] = {
    "Marina": 55.0,
    "Miheka": 55.0,
    "Hannah": 55.0,
    "Nick":   90.0,
    "Luke":   80.0,
}
