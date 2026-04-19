"""
Password gate and global mobile CSS.

Every page calls require_auth() as its first statement.
"""

from __future__ import annotations

import os

import streamlit as st


_MOBILE_CSS = """
<style>
/* ── Layout ──────────────────────────────────────────────────────────────── */
.block-container {
    padding: 1rem 1rem 3rem;
    max-width: 100% !important;
}

/* ── Touch targets ───────────────────────────────────────────────────────── */
.stButton > button {
    min-height: 44px;
    width: 100%;
    font-size: 1rem;
}
.stTextInput input,
.stNumberInput input,
.stSelectbox select,
.stDateInput input {
    min-height: 44px;
    font-size: 1rem;
}
.stMultiSelect [data-baseweb="select"] {
    min-height: 44px;
}
.stTextArea textarea {
    font-size: 1rem;
}

/* ── Metrics ─────────────────────────────────────────────────────────────── */
div[data-testid="metric-container"] {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 0.75rem;
}

/* ── Form submit button ──────────────────────────────────────────────────── */
div[data-testid="stFormSubmitButton"] button {
    min-height: 48px;
    width: 100%;
    font-size: 1.05rem;
    font-weight: 600;
}

/* ── Dataframes — allow horizontal scroll on small screens ───────────────── */
div[data-testid="stDataFrame"] {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}
</style>
"""


def apply_mobile_css() -> None:
    st.markdown(_MOBILE_CSS, unsafe_allow_html=True)


def require_auth() -> None:
    """Inject CSS and, if APP_PASSWORD is set, enforce password gate."""
    apply_mobile_css()

    pwd_env = os.getenv("APP_PASSWORD", "")
    if not pwd_env:
        return

    if st.session_state.get("authenticated"):
        return

    st.title("⛰ Bogong 2026")
    pwd = st.text_input("Password", type="password", label_visibility="collapsed",
                        placeholder="Enter password…")
    if st.button("Enter", use_container_width=True):
        if pwd == pwd_env:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()
