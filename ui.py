"""Shared UI helpers."""

from __future__ import annotations

import streamlit as st

# (href, label, key)
_PAGES = [
    ("/",               "Log",      "log"),
    ("/Progress",       "Progress", "progress"),
    ("/Training_Plan",  "Plan",     "plan"),
]


def show_nav(current: str = "") -> None:
    """Render a top navigation bar and hide the sidebar.

    Args:
        current: key of the active page ("log", "progress", or "plan").
    """
    st.markdown("""
<style>
[data-testid^="stSidebar"],
[data-testid="collapsedControl"],
[data-testid*="ollapsed"],
[data-testid="stExpandSidebarButton"] { display: none !important; }
/* Force nav columns to lay out horizontally */
[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    flex: 1 1 0 !important;
    min-width: 0 !important;
    width: auto !important;
}
/* Nav buttons — identical structure for all */
.nav-btn {
    background-color: #1E88E5 !important;
    border-radius: 6px !important;
    color: #FFFFFF !important;
    display: block !important;
    font-weight: 500 !important;
    padding: 0.45rem 0.75rem !important;
    text-decoration: none !important;
    transition: background-color 0.15s ease !important;
}
.nav-btn:hover {
    background-color: #1565C0 !important;
    color: #FFFFFF !important;
}
/* Selected page — only the fill changes */
.nav-selected {
    background-color: #0D47A1 !important;
    cursor: default !important;
    pointer-events: none !important;
}
/* Remove the <p> wrapper from layout so all buttons size identically */
[data-testid="stMarkdown"] p:has(.nav-btn) {
    display: contents !important;
}
</style>
<div style="height: 60px"></div>
""", unsafe_allow_html=True)

    auth_token = st.query_params.get("auth", "")
    auth_suffix = f"?auth={auth_token}" if auth_token else ""

    cols = st.columns(len(_PAGES))
    for col, (href, label, key) in zip(cols, _PAGES):
        with col:
            if key == current:
                st.markdown(f'<a class="nav-btn nav-selected" href="{href}{auth_suffix}">{label}</a>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<a class="nav-btn" href="{href}{auth_suffix}" target="_blank">{label}</a>',
                            unsafe_allow_html=True)
