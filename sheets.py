"""
Google Sheets data layer.

Local dev:  place credentials.json (service account key) in the project root,
            and set SPREADSHEET_ID in a .env file.

Deployment: set GOOGLE_CREDENTIALS_JSON (base64-encoded JSON string of the key)
            and SPREADSHEET_ID in the shinyapps.io environment variables panel.

The Google Sheet needs one tab named "hikes". The service account must have
Editor access to the spreadsheet.
"""

from __future__ import annotations

import base64
import json
import os
from datetime import date, datetime
from uuid import uuid4

import gspread
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

HIKE_COLS = [
    "log_id",
    "timestamp",
    "hiker_name",
    "hike_date",
    "activity_type",
    "elevation_gain_m",
    "distance_km",
    "duration_minutes",
    "notes",
]


def _get_client() -> gspread.Client:
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        # Support both raw JSON string and base64-encoded JSON
        try:
            info = json.loads(base64.b64decode(creds_json).decode())
        except Exception:
            info = json.loads(creds_json)
        return gspread.service_account_from_dict(info)
    return gspread.service_account(filename="credentials.json")


def _get_worksheet(sheet_name: str = "hikes") -> gspread.Worksheet:
    client = _get_client()
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    if not spreadsheet_id:
        raise EnvironmentError(
            "SPREADSHEET_ID environment variable is not set. "
            "Copy .env.example to .env and fill in the spreadsheet ID."
        )
    sh = client.open_by_key(spreadsheet_id)
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(sheet_name, rows=2000, cols=len(HIKE_COLS))
        ws.append_row(HIKE_COLS)
        return ws
    # Ensure header row matches HIKE_COLS — append any missing columns
    existing = ws.row_values(1)
    for col in HIKE_COLS:
        if col not in existing:
            ws.update_cell(1, len(existing) + 1, col)
            existing.append(col)
    return ws


def get_row_count() -> int:
    """Cheap check for reactive.poll — returns current data row count."""
    try:
        ws = _get_worksheet()
        return len(ws.get_all_values())
    except Exception:
        return -1


def load_hikes() -> pd.DataFrame:
    try:
        ws = _get_worksheet()
        records = ws.get_all_records()
        if not records:
            return _empty_df()
        df = pd.DataFrame(records)
        # Back-fill any columns absent from older rows
        for col in HIKE_COLS:
            if col not in df.columns:
                df[col] = ""
        df["hike_date"] = pd.to_datetime(df["hike_date"], errors="coerce").dt.date
        for col in ("elevation_gain_m", "distance_km", "duration_minutes"):
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df.dropna(subset=["hike_date"]).reset_index(drop=True)
    except Exception as e:
        print(f"[sheets] load_hikes error: {e}")
        return _empty_df()


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=HIKE_COLS)


def append_hike(
    hiker_name: str,
    hike_date: date,
    activity_type: str,
    elevation_gain_m: float,
    distance_km: float,
    duration_minutes: int,
    notes: str,
) -> None:
    ws = _get_worksheet()
    ws.append_row([
        str(uuid4()),
        datetime.utcnow().isoformat(),
        hiker_name,
        hike_date.isoformat(),
        activity_type,
        int(elevation_gain_m),
        round(distance_km, 2),
        int(duration_minutes),
        notes.strip(),
    ])
