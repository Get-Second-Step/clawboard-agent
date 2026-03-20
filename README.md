# ClawBoard — AI Audit Agent

AI-powered marketing audit agent. Runs parallel audits across Google Ads, Meta Ads, and GA4. Sends branded PDF reports via Telegram.

## Deploy on your VPS

```bash
curl -fsSL https://raw.githubusercontent.com/Get-Second-Step/clawboard-agent/main/install.sh | bash
```

## Setup after install

```bash
# 1. Add your API keys
nano ~/clawboard-agent/config/credentials.env

# 2. Generate Google OAuth token
cd ~/clawboard-agent && python3 scripts/generate_google_token.py

# 3. Run an audit
cd ~/clawboard-agent && uv run python audit_agent.py "Audit my Google Ads account"
```

## What you need

| Credential | Where to get it |
|---|---|
| `GOOGLE_AI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads → Tools → API Center |
| `GOOGLE_CLIENT_ID/SECRET` | Google Cloud Console → OAuth 2.0 |
| `GOOGLE_REFRESH_TOKEN` | Run `python3 scripts/generate_google_token.py` |
| `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/BotFather) on Telegram |

## Run manually

```bash
cd ~/clawboard-agent
uv run python audit_agent.py "Run a full audit for 'Client Name'"
uv run python audit_agent.py "Google Ads audit only for 'Client Name'"
```

Reports are saved to `reports/` as HTML and PDF.
