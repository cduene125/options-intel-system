# Options Intel System

Repo-ready Streamlit setup.

## Run locally

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

## Streamlit Cloud

Main file:

```text
dashboard.py
```

Do **not** upload `.env`.

Put your keys in Streamlit Cloud under:

```text
App Settings > Secrets
```

Use this format:

```toml
APCA_API_KEY_ID = "your_new_alpaca_key"
APCA_API_SECRET_KEY = "your_new_alpaca_secret"
APCA_PAPER = "true"
NEWS_API_KEY = "your_news_api_key"
```
