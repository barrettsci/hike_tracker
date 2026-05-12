# Hiking training tracker

A group training tracker for a planned hike.

Current version tracks groupmembers' elevation gain against a 26-week plan (adjust to suit your own goals).

## Running locally

```bash
pip install -r requirements.txt
streamlit run Home.py
```

Requires a `.env` file (copy `.env.example`) with:

```
SPREADSHEET_ID=your-google-sheet-id
GOOGLE_CREDENTIALS_JSON=base64-encoded-service-account-key
APP_PASSWORD=optional-password-gate
```

For local dev you can place `credentials.json` (service account key) in the project root instead of using `GOOGLE_CREDENTIALS_JSON`.

## Deploying to Streamlit Community Cloud

1. Push repo to GitHub (public repo works fine — the app has a password gate)
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your GitHub account
3. **New app** → select this repo → set main file to `Home.py`
4. Under **Advanced settings → Secrets**, add:

```toml
SPREADSHEET_ID = "your-sheet-id"
GOOGLE_CREDENTIALS_JSON = "your-base64-encoded-key"
APP_PASSWORD = "your-password"
```

To encode your service account key: `base64 -w 0 credentials.json`

Streamlit Cloud redeploys automatically on every push to main.
