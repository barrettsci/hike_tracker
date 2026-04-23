"""Entry point. Run with: streamlit run Home.py"""

from __future__ import annotations

import streamlit as st

from auth import require_auth
from ui import show_nav

st.set_page_config(page_title="Marina's 40th 🎉", page_icon="⛰", layout="centered")
require_auth()

pg = st.navigation(
    [
        st.Page("pages/log.py",       title="Log"),
        st.Page("pages/progress.py",  title="Progress", url_path="progress"),
        st.Page("pages/plan.py",      title="Plan",     url_path="plan"),
    ],
    position="hidden",
)
show_nav(pg.title.lower())
pg.run()
