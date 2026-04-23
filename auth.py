"""
Password gate and global mobile CSS.

Every page calls require_auth() as its first statement.

Auth is persisted via a URL query parameter (?auth=<token>). After a correct
password entry the token is appended to the URL, so refreshes and navigation
stay authenticated without needing cookies or external dependencies.
"""

from __future__ import annotations

import hashlib
import os

import streamlit as st


def _token(pwd: str) -> str:
    """Derive a short URL-safe token from the password."""
    return hashlib.sha256(pwd.encode()).hexdigest()[:24]


_MOBILE_CSS = """
<style>
/* ── Title ───────────────────────────────────────────────────────────────── */
h1 { font-size: 1.75rem !important; line-height: 1.2 !important; }

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

    token = _token(pwd_env)

    # Valid token in URL — stay authenticated and keep it in sync with session state
    if st.query_params.get("auth") == token:
        st.session_state.authenticated = True
        return

    # Same session, different page (query params may have been cleared by navigation)
    if st.session_state.get("authenticated"):
        st.query_params["auth"] = token
        return

    _, col, _ = st.columns([1, 2, 1])
    col.title("⛰ Marina's 40th 🎉")
    with col.form("auth_form"):
        pwd = st.text_input("Password", type="password", label_visibility="collapsed",
                            placeholder="Enter password…")
        submitted = st.form_submit_button("Enter", use_container_width=True)
    if submitted:
        if pwd == pwd_env:
            st.session_state.authenticated = True
            st.query_params["auth"] = token
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()
