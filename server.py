#!/usr/bin/env python3
"""
ClawBoard Pro — Local VPS Interface
Runs on your VPS at http://your-vps-ip:3000

Features:
- Chat with your ad accounts (free-form + quick commands)
- Connect / disconnect ad platforms (1-account limit on open source)
- Agent picker with scheduling customisation
- Delivery channels: Telegram, Slack, WhatsApp
- Reports viewer
"""

import asyncio
import json
import os
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import uvicorn
from dotenv import dotenv_values, load_dotenv, set_key
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
CREDS_FILE  = PROJECT_DIR / "config" / "credentials.env"
REPORTS_DIR = PROJECT_DIR / "reports"
CHAT_LOG    = PROJECT_DIR / "reports" / "chat.log"

OPEN_SOURCE_ACCOUNT_LIMIT = 1   # Upgrade to ClawBoard Pro for unlimited

load_dotenv(CREDS_FILE)

app = FastAPI(title="ClawBoard Pro", docs_url=None, redoc_url=None)

UI_DIR = PROJECT_DIR / "ui"

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_server_base(request: Request) -> str:
    host = request.headers.get("host", "localhost:3000")
    scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
    return f"{scheme}://{host}"


def creds() -> dict:
    return dotenv_values(CREDS_FILE) if CREDS_FILE.exists() else {}


def save_cred(key: str, value: str):
    CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not CREDS_FILE.exists():
        CREDS_FILE.write_text("")
    set_key(str(CREDS_FILE), key, value)
    os.environ[key] = value


def platform_status() -> dict:
    c = creds()
    def ok(*keys):
        return all(c.get(k) and "your_" not in c.get(k, "your_") for k in keys)
    return {
        "google_ads": ok("GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_REFRESH_TOKEN",
                         "GOOGLE_CLIENT_ID", "GOOGLE_ADS_CUSTOMER_ID"),
        "meta_ads":   ok("META_ACCESS_TOKEN", "META_BUSINESS_ACCOUNT_ID"),
        "ga4":        ok("GOOGLE_ANALYTICS_PROPERTY_ID", "GOOGLE_REFRESH_TOKEN"),
        "mcc":        ok("GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_REFRESH_TOKEN",
                         "GOOGLE_CLIENT_ID", "GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
    }


def connected_client_accounts() -> list:
    """List of connected client-level accounts (not MCC). Used for limit check."""
    s = platform_status()
    result = []
    c = creds()
    if s["google_ads"]:
        acct = c.get("GOOGLE_ADS_CUSTOMER_ID", "")
        result.append({"platform": "google_ads", "id": acct, "label": f"Google Ads · {acct}"})
    if s["meta_ads"]:
        acct = c.get("META_BUSINESS_ACCOUNT_ID", "")
        result.append({"platform": "meta_ads", "id": acct, "label": f"Meta Ads · {acct}"})
    return result


def at_account_limit() -> bool:
    return len(connected_client_accounts()) >= OPEN_SOURCE_ACCOUNT_LIMIT


def recent_reports(limit: int = 5) -> list:
    pdfs  = sorted(REPORTS_DIR.glob("*.pdf"),  key=lambda f: f.stat().st_mtime, reverse=True)
    htmls = sorted(REPORTS_DIR.glob("*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    files, seen = [], set()
    for f in sorted(pdfs + htmls, key=lambda f: f.stat().st_mtime, reverse=True):
        if f.name in ("chat.log",):
            continue
        stem = f.stem
        if stem not in seen:
            seen.add(stem)
            files.append({
                "name": f.name, "stem": stem,
                "size": f"{f.stat().st_size // 1024}KB",
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%b %d %H:%M"),
                "is_pdf": f.suffix == ".pdf",
            })
        if len(files) >= limit:
            break
    return files


def get_cron_schedule() -> dict:
    """Read current ClawBoard cron entry."""
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "audit_agent" in line or "clawboard" in line.lower():
                parts = line.strip().split()
                if len(parts) >= 5:
                    return {"raw": line.strip(), "minute": parts[0], "hour": parts[1],
                            "dom": parts[2], "month": parts[3], "dow": parts[4]}
    except Exception:
        pass
    return {"raw": "0 9 * * *", "minute": "0", "hour": "9", "dom": "*", "month": "*", "dow": "*"}


def set_cron_schedule(minute: str, hour: str, dow: str):
    """Update the ClawBoard cron entry."""
    cmd = f"cd {PROJECT_DIR} && python3 audit_agent.py 'Run daily performance marketing audit' >> {PROJECT_DIR}/reports/cron.log 2>&1"
    new_entry = f"{minute} {hour} * * {dow} {cmd}  # clawboard-daily"
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        lines = [l for l in result.stdout.splitlines()
                 if "audit_agent" not in l and "clawboard-daily" not in l]
        lines.append(new_entry)
        new_crontab = "\n".join(lines) + "\n"
        proc = subprocess.run(["crontab", "-"], input=new_crontab, text=True)
        return proc.returncode == 0
    except Exception:
        return False


# ── Design System ─────────────────────────────────────────────────────────────

CSS = """
*, *::before, *::after { box-sizing: border-box; }
body { margin: 0; background: #07080a; color: #f0f0f2; font-family: 'Inter', system-ui, sans-serif; font-size: 15px; line-height: 1.6; height: 100vh; display: flex; flex-direction: column; }
a { color: #E87811; text-decoration: none; }
a:hover { color: #f08828; }

/* Topbar */
.topbar { display: flex; align-items: center; justify-content: space-between; padding: 0 28px; height: 52px; border-bottom: 1px solid rgba(255,255,255,0.06); background: #0c0d10; flex-shrink: 0; }
.logo { font-family: 'Space Grotesk', sans-serif; font-size: 17px; font-weight: 700; color: #f0f0f2; letter-spacing: -0.03em; display: flex; align-items: center; gap: 8px; }
.logo .dot { color: #E87811; }
.logo .pro-badge { font-size: 9px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; background: rgba(232,120,17,0.15); border: 1px solid rgba(232,120,17,0.3); color: #E87811; padding: 2px 6px; }
.nav-links { display: flex; gap: 4px; }
.nav-links a { color: #8b8fa8; font-size: 13px; font-weight: 500; padding: 6px 12px; transition: all 0.15s; }
.nav-links a:hover { color: #f0f0f2; background: rgba(255,255,255,0.04); }
.nav-links a.active { color: #f0f0f2; background: rgba(255,255,255,0.06); }
.topbar-right { display: flex; align-items: center; gap: 12px; font-size: 12px; }
.upgrade-link { font-size: 12px; font-weight: 600; color: #E87811; border: 1px solid rgba(232,120,17,0.3); padding: 5px 12px; }
.upgrade-link:hover { background: rgba(232,120,17,0.08); color: #f08828; }

/* Layout */
.app-body { display: flex; flex: 1; overflow: hidden; }
.sidebar { width: 220px; flex-shrink: 0; border-right: 1px solid rgba(255,255,255,0.06); background: #0a0b0e; display: flex; flex-direction: column; overflow-y: auto; padding: 16px 0; }
.main { flex: 1; overflow-y: auto; display: flex; flex-direction: column; }
.container { max-width: 860px; margin: 0 auto; padding: 32px 24px; width: 100%; }

/* Sidebar */
.sidebar-section { padding: 0 12px; margin-bottom: 20px; }
.sidebar-label { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #4a4d5e; padding: 0 8px; margin-bottom: 6px; }
.sidebar-item { display: flex; align-items: center; justify-content: space-between; padding: 7px 8px; font-size: 13px; color: #8b8fa8; }
.sidebar-item .name { display: flex; align-items: center; gap: 7px; }
.sidebar-dot { width: 6px; height: 6px; border-radius: 50%; background: #2a2c35; flex-shrink: 0; }
.sidebar-dot.live { background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.5); }
.sidebar-dot.soon { background: #E87811; opacity: 0.4; }
.sidebar-limit { font-size: 10px; color: #4a4d5e; padding: 6px 8px; }
.sidebar-upgrade { margin: 0 8px; padding: 8px 10px; background: rgba(232,120,17,0.06); border: 1px solid rgba(232,120,17,0.15); font-size: 11px; line-height: 1.5; }
.sidebar-upgrade a { color: #E87811; font-weight: 600; }

/* Chat */
.chat-wrap { flex: 1; display: flex; flex-direction: column; height: 100%; }
.chat-history { flex: 1; overflow-y: auto; padding: 24px 28px; display: flex; flex-direction: column; gap: 16px; }
.chat-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 20px; padding: 40px; }
.chat-empty-title { font-family: 'Space Grotesk', sans-serif; font-size: 20px; font-weight: 700; letter-spacing: -0.03em; text-align: center; }
.chat-empty-sub { font-size: 14px; color: #8b8fa8; text-align: center; max-width: 380px; }
.quick-cmds { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.quick-cmd { padding: 8px 14px; background: #0e0f12; border: 1px solid rgba(255,255,255,0.08); color: #f0f0f2; font-size: 13px; cursor: pointer; font-family: 'Inter', sans-serif; transition: all 0.15s; }
.quick-cmd:hover { border-color: rgba(232,120,17,0.4); background: rgba(232,120,17,0.05); color: #E87811; }
.msg { display: flex; gap: 10px; max-width: 680px; }
.msg.user { align-self: flex-end; flex-direction: row-reverse; }
.msg-bubble { padding: 12px 16px; font-size: 14px; line-height: 1.6; }
.msg.user .msg-bubble { background: #E87811; color: #07080a; font-weight: 500; }
.msg.agent .msg-bubble { background: #0e0f12; border: 1px solid rgba(255,255,255,0.06); color: #e0e0e8; white-space: pre-wrap; }
.msg-avatar { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; font-family: 'Space Grotesk', sans-serif; font-weight: 700; }
.msg.user .msg-avatar { background: #E87811; color: #07080a; }
.msg.agent .msg-avatar { background: #1a1c24; color: #E87811; border: 1px solid rgba(232,120,17,0.2); }
.chat-input-bar { padding: 16px 28px; border-top: 1px solid rgba(255,255,255,0.06); background: #0a0b0e; flex-shrink: 0; }
.chat-input-row { display: flex; gap: 10px; align-items: flex-end; }
.chat-input { flex: 1; background: #13151a; border: 1px solid rgba(255,255,255,0.08); color: #f0f0f2; font-family: 'Inter', sans-serif; font-size: 14px; padding: 12px 16px; outline: none; resize: none; max-height: 120px; transition: border-color 0.15s; }
.chat-input:focus { border-color: rgba(232,120,17,0.35); }
.chat-input::placeholder { color: #4a4d5e; }
.chat-send { padding: 12px 20px; background: #E87811; color: #07080a; border: none; font-weight: 700; font-size: 14px; cursor: pointer; flex-shrink: 0; font-family: 'Inter', sans-serif; transition: all 0.15s; height: 47px; }
.chat-send:hover { background: #f08828; }
.chat-send:disabled { opacity: 0.5; cursor: not-allowed; }
.typing-dot { display: inline-flex; gap: 3px; align-items: center; }
.typing-dot span { width: 5px; height: 5px; border-radius: 50%; background: #8b8fa8; animation: blink 1.2s infinite; }
.typing-dot span:nth-child(2) { animation-delay: 0.2s; }
.typing-dot span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%,80%,100% { opacity: 0.3; } 40% { opacity: 1; } }

/* General UI */
.page-title { font-family: 'Space Grotesk', sans-serif; font-size: 22px; font-weight: 700; letter-spacing: -0.03em; margin: 0 0 4px; }
.page-subtitle { color: #8b8fa8; font-size: 14px; margin: 0 0 28px; }
.section { margin-bottom: 32px; }
.section-label { font-size: 11px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #8b8fa8; margin-bottom: 10px; }
.panel { background: #0e0f12; border: 1px solid rgba(255,255,255,0.06); padding: 20px; }
.panel-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.panel-row:last-child { border-bottom: none; padding-bottom: 0; }
.panel-row:first-child { padding-top: 0; }
.btn { display: inline-flex; align-items: center; gap: 7px; padding: 8px 16px; font-size: 13px; font-weight: 600; font-family: 'Inter', sans-serif; cursor: pointer; border: none; transition: all 0.15s; text-decoration: none; white-space: nowrap; }
.btn-primary { background: #E87811; color: #07080a; }
.btn-primary:hover { background: #f08828; color: #07080a; }
.btn-ghost { background: transparent; color: #f0f0f2; border: 1px solid rgba(255,255,255,0.1); }
.btn-ghost:hover { border-color: rgba(255,255,255,0.2); background: rgba(255,255,255,0.04); }
.btn-danger { background: transparent; color: #ef4444; border: 1px solid rgba(239,68,68,0.15); font-size: 12px; padding: 5px 12px; }
.btn-danger:hover { background: rgba(239,68,68,0.06); }
.btn-sm { padding: 5px 12px; font-size: 12px; }
.badge-connected { display: inline-flex; align-items: center; gap: 5px; padding: 2px 8px; background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.2); color: #22c55e; font-size: 10px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; }
.badge-connected::before { content: ''; width: 5px; height: 5px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 5px rgba(34,197,94,0.6); }
.badge-off { display: inline-flex; align-items: center; gap: 5px; padding: 2px 8px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); color: #8b8fa8; font-size: 10px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; }
.badge-soon { padding: 2px 8px; background: rgba(232,120,17,0.07); border: 1px solid rgba(232,120,17,0.2); color: #E87811; font-size: 10px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; }
.form-group { margin-bottom: 14px; }
.form-label { display: block; font-size: 11px; font-weight: 600; color: #8b8fa8; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.08em; }
.form-input, .form-select { width: 100%; padding: 9px 12px; background: #13151a; border: 1px solid rgba(255,255,255,0.08); color: #f0f0f2; font-family: 'Inter', sans-serif; font-size: 14px; outline: none; transition: border-color 0.15s; }
.form-select { cursor: pointer; }
.form-input:focus, .form-select:focus { border-color: rgba(232,120,17,0.4); }
.form-input::placeholder { color: #4a4d5e; }
.form-hint { font-size: 12px; color: #4a4d5e; margin-top: 4px; }
.alert { padding: 12px 16px; border-left: 3px solid; margin-bottom: 20px; font-size: 13px; }
.alert-success { background: rgba(34,197,94,0.05); border-color: #22c55e; color: #86efac; }
.alert-error   { background: rgba(239,68,68,0.05); border-color: #ef4444; color: #fca5a5; }
.alert-info    { background: rgba(232,120,17,0.05); border-color: #E87811; color: #fdba74; }
.limit-wall { background: #0e0f12; border: 1px solid rgba(232,120,17,0.25); padding: 20px 24px; }
.limit-wall-title { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 16px; margin-bottom: 6px; }
.limit-wall-body { font-size: 13px; color: #8b8fa8; line-height: 1.6; margin-bottom: 14px; }
.agent-card { background: #0e0f12; border: 1px solid rgba(255,255,255,0.06); padding: 18px; }
.agent-card.active { border-color: rgba(232,120,17,0.25); }
.agent-name { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 15px; margin-bottom: 3px; }
.agent-desc { font-size: 13px; color: #8b8fa8; }
.divider { height: 1px; background: rgba(255,255,255,0.05); margin: 24px 0; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: rgba(255,255,255,0.05); }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: rgba(255,255,255,0.05); }
code { font-family: 'SF Mono', monospace; font-size: 12px; background: rgba(255,255,255,0.05); padding: 2px 6px; color: #E87811; }
"""

FONTS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
"""


def topbar(active: str = "chat") -> str:
    links = [("chat", "/", "Chat"), ("agents", "/agents", "Agents"),
             ("reports", "/reports", "Reports"), ("settings", "/settings", "Settings")]
    nav = "".join(
        f'<a href="{u}" class="{"active" if a == active else ""}">{label}</a>'
        for a, u, label in links
    )
    return f"""
    <div class="topbar">
      <div class="logo">Claw<span class="dot">Board</span> <span class="pro-badge">Pro</span></div>
      <nav class="nav-links">{nav}</nav>
      <div class="topbar-right">
        <a href="https://clawboard.pro/upgrade" target="_blank" class="upgrade-link">↑ Upgrade</a>
      </div>
    </div>"""


def sidebar_html() -> str:
    s = platform_status()
    c = creds()

    def item(label, key, coming=False):
        dot_cls = "live" if s.get(key) else ("soon" if coming else "")
        return f"""
        <div class="sidebar-item">
          <div class="name">
            <div class="sidebar-dot {dot_cls}"></div>
            <span>{label}</span>
          </div>
        </div>"""

    connected = connected_client_accounts()
    at_limit = at_account_limit()

    upgrade_block = ""
    if at_limit:
        upgrade_block = f"""
        <div class="sidebar-upgrade">
          You're on <strong>Open Source</strong>.<br>
          <a href="https://clawboard.pro/upgrade" target="_blank">Upgrade to ClawBoard Pro</a> to manage unlimited client accounts.
        </div>"""

    return f"""
    <div class="sidebar">
      <div class="sidebar-section">
        <div class="sidebar-label">Connected</div>
        {item("Google Ads", "google_ads")}
        {item("Meta Ads", "meta_ads")}
        {item("GA4", "ga4")}
      </div>
      <div class="sidebar-section">
        <div class="sidebar-label">Coming Soon</div>
        {item("LinkedIn Ads", "linkedin", True)}
        {item("TikTok Ads", "tiktok", True)}
        {item("Microsoft Ads", "microsoft", True)}
      </div>
      <div class="sidebar-section">
        <div class="sidebar-limit">Open Source · {len(connected)}/{OPEN_SOURCE_ACCOUNT_LIMIT} account</div>
        <div class="sidebar-section" style="padding:0;">
          <a href="/connect" class="btn btn-ghost btn-sm" style="width:100%;justify-content:center;font-size:12px;">Manage Account</a>
        </div>
      </div>
      {upgrade_block}
    </div>"""


UPDATE_BANNER_JS = """
<script>
(function() {
  const banner = document.getElementById('update-banner');
  const btn    = document.getElementById('update-btn');
  const label  = document.getElementById('update-label');
  if (!banner) return;
  fetch('/api/update-check')
    .then(r => r.json())
    .then(d => {
      if (!d.up_to_date) {
        label.textContent = 'Update available (' + d.remote + '): ' + d.message;
        banner.style.display = 'flex';
      }
    }).catch(() => {});
  if (btn) {
    btn.addEventListener('click', () => {
      btn.textContent = 'Updating…';
      btn.disabled = true;
      fetch('/api/update', {method:'POST'})
        .then(r => r.json())
        .then(d => {
          if (d.ok) {
            label.textContent = d.message + ' Reloading in 3s…';
            setTimeout(() => location.reload(), 3000);
          } else {
            label.textContent = 'Update failed: ' + d.error;
            btn.disabled = false;
            btn.textContent = 'Retry';
          }
        });
    });
  }
})();
</script>
"""

UPDATE_BANNER_HTML = """
<div id="update-banner" style="display:none;align-items:center;justify-content:space-between;
  background:#1a2a1a;border-bottom:1px solid #2d4a2d;padding:8px 20px;font-size:13px;color:#7ec87e;">
  <span>⬆ <span id="update-label"></span></span>
  <button id="update-btn" onclick="" style="background:#2d6a2d;color:#fff;border:none;
    border-radius:6px;padding:4px 14px;font-size:12px;cursor:pointer;font-weight:600;">
    Update Now
  </button>
</div>
"""

def shell(active: str, body: str, title: str = "ClawBoard Pro", sidebar: bool = True) -> HTMLResponse:
    sb = sidebar_html() if sidebar else ""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — ClawBoard Pro</title>
{FONTS}
<style>{CSS}</style>
</head>
<body>
{UPDATE_BANNER_HTML}
{topbar(active)}
<div class="app-body">
  {sb}
  <div class="main">
    {body}
  </div>
</div>
{UPDATE_BANNER_JS}
</body>
</html>"""
    return HTMLResponse(html)


# ── Chat ──────────────────────────────────────────────────────────────────────

def load_chat_history(limit: int = 40) -> list:
    if not CHAT_LOG.exists():
        return []
    try:
        lines = CHAT_LOG.read_text().strip().splitlines()
        messages = [json.loads(l) for l in lines if l.strip()]
        return messages[-limit:]
    except Exception:
        return []


def append_chat(role: str, text: str):
    CHAT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(CHAT_LOG, "a") as f:
        f.write(json.dumps({"role": role, "text": text,
                            "ts": datetime.now().strftime("%H:%M")}) + "\n")


def chat_bubble(msg: dict) -> str:
    role = msg["role"]
    text = msg["text"].replace("<", "&lt;").replace(">", "&gt;")
    ts = msg.get("ts", "")
    if role == "user":
        return f"""
        <div class="msg user">
          <div class="msg-avatar">S</div>
          <div class="msg-bubble">{text}</div>
        </div>"""
    else:
        return f"""
        <div class="msg agent">
          <div class="msg-avatar">C</div>
          <div class="msg-bubble">{text}</div>
        </div>"""


QUICK_COMMANDS = [
    ("Audit last 7 days", "Run a quick audit of my ad accounts for the last 7 days"),
    ("Budget status", "What is my current budget utilisation and daily spend?"),
    ("Top keywords", "Show me my top 10 performing keywords by conversions"),
    ("CPA check", "What is my cost per acquisition and how does it compare to last week?"),
    ("Weekly brief", "Give me a full weekly performance brief with recommendations"),
    ("Wasted spend", "Find campaigns or keywords wasting budget with low quality scores"),
]


@app.get("/", response_class=HTMLResponse)
async def root_page():
    ui_file = UI_DIR / "app.html"
    if ui_file.exists():
        return HTMLResponse(ui_file.read_text())
    return RedirectResponse(url="/legacy", status_code=302)

@app.get("/legacy", response_class=HTMLResponse)
async def chat_page(request: Request):
    s = platform_status()
    history = load_chat_history()
    connected_count = sum(1 for v in s.values() if v)

    if not connected_count:
        # No accounts connected — show setup prompt
        body = f"""
        <div class="chat-wrap">
          <div class="chat-history" id="chat-history">
            <div class="chat-empty">
              <div class="chat-empty-title">Welcome to ClawBoard Pro</div>
              <div class="chat-empty-sub">Connect your ad accounts to start chatting with your data. Takes 2 minutes.</div>
              <a href="/connect" class="btn btn-primary">Connect an Account →</a>
            </div>
          </div>
          <div class="chat-input-bar">
            <div class="chat-input-row">
              <textarea class="chat-input" placeholder="Connect an account first to start chatting..." disabled></textarea>
              <button class="chat-send" disabled>Send</button>
            </div>
          </div>
        </div>"""
    else:
        msg_html = "".join(chat_bubble(m) for m in history) if history else ""
        empty_block = ""
        if not history:
            cmds_html = "".join(
                f'<button class="quick-cmd" onclick="sendMsg(\'{label}\')">{label}</button>'
                for label, _ in QUICK_COMMANDS
            )
            empty_block = f"""
            <div class="chat-empty" id="chat-empty">
              <div class="chat-empty-title">Chat with your ad accounts</div>
              <div class="chat-empty-sub">{connected_count} platform{"s" if connected_count != 1 else ""} connected. Ask anything or pick a quick command.</div>
              <div class="quick-cmds">{cmds_html}</div>
            </div>"""

        body = f"""
        <div class="chat-wrap">
          <div class="chat-history" id="chat-history">
            {empty_block}
            <div id="messages">{msg_html}</div>
          </div>
          <div class="chat-input-bar">
            <div class="chat-input-row">
              <textarea id="chat-input" class="chat-input" rows="1"
                placeholder="Ask about your campaigns, budgets, keywords..."
                onkeydown="handleKey(event)"></textarea>
              <button id="send-btn" class="chat-send" onclick="sendChat()">Send</button>
            </div>
          </div>
        </div>

        <script>
        const QUICK = {json.dumps({label: task for label, task in QUICK_COMMANDS})};

        function sendMsg(label) {{
          const task = QUICK[label] || label;
          document.getElementById('chat-input').value = task;
          sendChat();
        }}

        function handleKey(e) {{
          if (e.key === 'Enter' && !e.shiftKey) {{
            e.preventDefault();
            sendChat();
          }}
        }}

        async function sendChat() {{
          const input = document.getElementById('chat-input');
          const btn = document.getElementById('send-btn');
          const msgs = document.getElementById('messages');
          const empty = document.getElementById('chat-empty');
          const text = input.value.trim();
          if (!text) return;

          if (empty) empty.remove();
          input.value = '';
          btn.disabled = true;

          // User bubble
          msgs.innerHTML += `<div class="msg user"><div class="msg-avatar">S</div><div class="msg-bubble">${{text}}</div></div>`;

          // Typing indicator
          const typingId = 'typing-' + Date.now();
          msgs.innerHTML += `<div class="msg agent" id="${{typingId}}"><div class="msg-avatar">C</div><div class="msg-bubble"><div class="typing-dot"><span></span><span></span><span></span></div></div></div>`;
          scrollBottom();

          try {{
            const resp = await fetch('/chat', {{
              method: 'POST',
              headers: {{'Content-Type': 'application/json'}},
              body: JSON.stringify({{message: text}})
            }});
            const data = await resp.json();
            document.getElementById(typingId)?.remove();
            const reply = (data.reply || 'Agent is processing. Check back shortly.').replace(/</g,'&lt;').replace(/>/g,'&gt;');
            msgs.innerHTML += `<div class="msg agent"><div class="msg-avatar">C</div><div class="msg-bubble">${{reply}}</div></div>`;
          }} catch(e) {{
            document.getElementById(typingId)?.remove();
            msgs.innerHTML += `<div class="msg agent"><div class="msg-avatar">C</div><div class="msg-bubble" style="color:#ef4444;">Error reaching agent. Check that audit_agent.py is running.</div></div>`;
          }}

          btn.disabled = false;
          scrollBottom();
        }}

        function scrollBottom() {{
          const h = document.getElementById('chat-history');
          h.scrollTop = h.scrollHeight;
        }}
        window.addEventListener('load', scrollBottom);
        </script>"""

    return shell("chat", body, "Chat")


@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    message = data.get("message", "").strip()
    if not message:
        return JSONResponse({"reply": "Please enter a message."})

    append_chat("user", message)

    # Run audit_agent.py with the user's message, timeout 90s
    cmd = ["python3", str(PROJECT_DIR / "audit_agent.py"), message]
    try:
        result = subprocess.run(
            cmd, cwd=str(PROJECT_DIR),
            capture_output=True, text=True, timeout=90,
            env={**os.environ, "NO_PDF": "1"}  # skip PDF for chat, just return text
        )
        output = result.stdout.strip()
        if not output and result.stderr:
            output = f"Agent error: {result.stderr[:300]}"
        elif not output:
            output = "Audit completed. Check /reports for the full report."
    except subprocess.TimeoutExpired:
        output = "Agent is still processing — this audit takes 2-3 minutes. Check /reports when done, or use 'Run Audit Now' for a full async run."
    except Exception as e:
        output = f"Error starting agent: {str(e)}"

    append_chat("agent", output)
    return JSONResponse({"reply": output})


# ── Connect / Account Management ─────────────────────────────────────────────

@app.get("/connect", response_class=HTMLResponse)
async def connect_page(request: Request, success: str = "", error: str = ""):
    s   = platform_status()
    c   = creds()
    at_limit = at_account_limit()
    base = get_server_base(request)

    alert = ""
    if success: alert = f'<div class="alert alert-success">✓ {success}</div>'
    if error:   alert = f'<div class="alert alert-error">✗ {error}</div>'

    # ── Account limit wall ──
    limit_wall = ""
    if at_limit and not (s["google_ads"] or s["meta_ads"]):
        # Edge case — at limit but nothing showing? Show it.
        pass
    elif at_limit:
        accounts = connected_client_accounts()
        acct_label = accounts[0]["label"] if accounts else "an account"
        limit_wall = f"""
        <div class="limit-wall">
          <div class="limit-wall-title">1-Account Limit (Open Source)</div>
          <div class="limit-wall-body">
            You currently have <strong>{acct_label}</strong> connected.<br>
            To connect a different account, disconnect the current one first.<br>
            To manage <strong>multiple clients simultaneously</strong>, upgrade to ClawBoard Pro.
          </div>
          <a href="https://clawboard.pro/upgrade" target="_blank" class="btn btn-primary">Upgrade to ClawBoard Pro →</a>
        </div>"""

    # ── Google Ads card ──
    if s["google_ads"]:
        acct_id = c.get("GOOGLE_ADS_CUSTOMER_ID", "")
        google_card = f"""
        <div class="panel">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
            <div>
              <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:15px;">Google Ads</div>
              <div style="font-size:13px;color:#8b8fa8;margin-top:2px;">Account: {acct_id}</div>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <span class="badge-connected">Connected</span>
              <a href="/disconnect/google_ads" class="btn btn-danger">Disconnect</a>
            </div>
          </div>
        </div>"""
    else:
        disabled = ' style="opacity:0.4;pointer-events:none;"' if at_limit else ""
        google_card = f"""
        <div class="panel" {disabled}>
          <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:15px;margin-bottom:4px;">Connect Google Ads</div>
          <div style="font-size:13px;color:#8b8fa8;margin-bottom:20px;">3 steps · takes about 5 minutes the first time</div>
          <form method="POST" action="/connect/google_ads/manual">

            <div style="display:flex;flex-direction:column;gap:20px;">

              <!-- Step 1 -->
              <div style="display:flex;gap:14px;">
                <div style="flex-shrink:0;width:28px;height:28px;border-radius:50%;background:#e87811;color:#fff;font-weight:700;font-size:13px;display:flex;align-items:center;justify-content:center;">1</div>
                <div style="flex:1;">
                  <div style="font-weight:600;font-size:13px;margin-bottom:8px;">Your Google Ads account number</div>
                  <input class="form-input" name="customer_id" placeholder="123-456-7890" required>
                  <div class="form-hint">Top-right corner of your Google Ads dashboard (e.g. 316-669-4225)</div>
                </div>
              </div>

              <!-- Step 2 -->
              <div style="display:flex;gap:14px;">
                <div style="flex-shrink:0;width:28px;height:28px;border-radius:50%;background:#e87811;color:#fff;font-weight:700;font-size:13px;display:flex;align-items:center;justify-content:center;">2</div>
                <div style="flex:1;">
                  <div style="font-weight:600;font-size:13px;margin-bottom:2px;">Developer Token</div>
                  <div style="font-size:12px;color:#8b8fa8;margin-bottom:8px;">Google Ads → Tools &amp; Settings → API Center → copy "Developer token"</div>
                  <input class="form-input" name="developer_token" placeholder="Paste your developer token" required>
                </div>
              </div>

              <!-- Step 3 -->
              <div style="display:flex;gap:14px;">
                <div style="flex-shrink:0;width:28px;height:28px;border-radius:50%;background:#e87811;color:#fff;font-weight:700;font-size:13px;display:flex;align-items:center;justify-content:center;">3</div>
                <div style="flex:1;">
                  <div style="font-weight:600;font-size:13px;margin-bottom:2px;">Google Cloud OAuth credentials</div>
                  <div style="font-size:12px;color:#8b8fa8;margin-bottom:8px;">
                    <a href="https://console.cloud.google.com/apis/credentials" target="_blank" style="color:#e87811;">console.cloud.google.com</a> → Create OAuth 2.0 Client ID (Desktop app type) → copy Client ID &amp; Secret.<br>
                    Add <strong style="color:#f0f0f2;">{get_server_base(request)}/callback/google</strong> as an authorised redirect URI.
                  </div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                    <input class="form-input" name="client_id" placeholder="Client ID  (xxxx.apps.googleusercontent.com)" required>
                    <input class="form-input" name="client_secret" placeholder="Client Secret  (GOCSPX-...)" required>
                  </div>
                </div>
              </div>

            </div>

            <div style="margin-top:20px;padding-top:16px;border-top:1px solid #2a2d3e;display:flex;align-items:center;gap:12px;">
              <button type="submit" class="btn btn-primary" style="font-size:14px;padding:10px 22px;">Connect with Google →</button>
              <span style="font-size:12px;color:#4a4d5e;">You'll be redirected to Google to approve access, then auto-returned here</span>
            </div>
          </form>
        </div>"""

    # ── MCC card ──
    if s["mcc"]:
        mcc_id = c.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "")
        mcc_card = f"""
        <div class="panel" style="margin-top:12px;">
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div>
              <div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;">MCC (Manager Account)</div>
              <div style="font-size:13px;color:#8b8fa8;margin-top:2px;">MCC ID: {mcc_id}</div>
            </div>
            <div style="display:flex;gap:10px;">
              <span class="badge-connected">Connected</span>
              <a href="/disconnect/mcc" class="btn btn-danger">Disconnect</a>
            </div>
          </div>
        </div>"""
    else:
        mcc_card = f"""
        <div class="panel" style="margin-top:12px;border-style:dashed;">
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div>
              <div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;">MCC (Manager Account)</div>
              <div style="font-size:13px;color:#8b8fa8;margin-top:2px;">Optional — connect to audit sub-accounts under your MCC</div>
            </div>
            <a href="/connect/mcc" class="btn btn-ghost btn-sm">Add MCC →</a>
          </div>
        </div>"""

    # ── Meta card ──
    if s["meta_ads"]:
        meta_acct = c.get("META_BUSINESS_ACCOUNT_ID", "")
        meta_card = f"""
        <div class="panel">
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div>
              <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:15px;">Meta Ads</div>
              <div style="font-size:13px;color:#8b8fa8;margin-top:2px;">Account: {meta_acct}</div>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <span class="badge-connected">Connected</span>
              <a href="/disconnect/meta_ads" class="btn btn-danger">Disconnect</a>
            </div>
          </div>
        </div>"""
    else:
        disabled = ' style="opacity:0.4;pointer-events:none;"' if at_limit else ""
        meta_card = f"""
        <div class="panel" {disabled}>
          <div class="section-label" style="margin-bottom:14px;">Connect Meta Ads</div>
          <form method="POST" action="/connect/meta_ads/manual">
            <div class="grid-2" style="gap:12px;background:none;">
              <div class="form-group">
                <label class="form-label">App ID</label>
                <input class="form-input" name="app_id" placeholder="developers.facebook.com → App Settings" required>
              </div>
              <div class="form-group">
                <label class="form-label">App Secret</label>
                <input class="form-input" name="app_secret" required>
              </div>
              <div class="form-group">
                <label class="form-label">Business Account ID</label>
                <input class="form-input" name="account_id" placeholder="act_123456789" required>
              </div>
            </div>
            <button type="submit" class="btn btn-primary" style="margin-top:4px;">Save &amp; Authorise Meta →</button>
          </form>
        </div>"""

    body = f"""
    <div class="container">
      {alert}
      <div class="page-title">Account</div>
      <div class="page-subtitle">Connect ad platforms · 1 account limit on open source</div>

      {limit_wall}

      <div class="section">
        <div class="section-label">Google Ads</div>
        {google_card}
        {mcc_card}
      </div>

      <div class="section">
        <div class="section-label">Meta Ads</div>
        {meta_card}
      </div>

      <div class="section">
        <div class="section-label">GA4 Analytics</div>
        <div class="panel">
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div>
              <div style="font-size:14px;font-weight:600;">GA4 is linked via Google OAuth</div>
              <div style="font-size:13px;color:#8b8fa8;margin-top:2px;">
                {"Property ID: " + c.get("GOOGLE_ANALYTICS_PROPERTY_ID","") if s["ga4"] else "Connect Google Ads first, then add your GA4 Property ID in Settings."}
              </div>
            </div>
            {"<span class='badge-connected'>Connected</span>" if s["ga4"] else "<a href='/settings' class='btn btn-ghost btn-sm'>Add in Settings →</a>"}
          </div>
        </div>
      </div>
    </div>"""

    return shell("chat", body, "Connect")


@app.post("/connect/google_ads/manual")
async def google_manual_connect(request: Request):
    form = await request.form()
    # Use form values directly — avoids stale file read after save
    client_id     = str(form.get("client_id", "")).strip()
    client_secret = str(form.get("client_secret", "")).strip()
    save_cred("GOOGLE_ADS_DEVELOPER_TOKEN", str(form.get("developer_token", "")))
    save_cred("GOOGLE_ADS_CUSTOMER_ID", str(form.get("customer_id", "")).replace("-", ""))
    save_cred("GOOGLE_CLIENT_ID", client_id)
    save_cred("GOOGLE_CLIENT_SECRET", client_secret)

    redirect_uri = "https://clawboard.pro/callback/google"
    save_cred("_OAUTH_REDIRECT_URI", redirect_uri)

    params = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "https://www.googleapis.com/auth/adwords https://www.googleapis.com/auth/analytics.readonly",
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
    })
    oauth_url = f"https://accounts.google.com/o/oauth2/auth?{params}"
    return RedirectResponse(oauth_url, status_code=303)


@app.get("/callback/google")
async def google_callback(code: str = "", error: str = ""):
    if error or not code:
        return RedirectResponse(f"/connect?error=Google+auth+failed:+{error}")
    c = creds()
    redirect_uri = c.get("_OAUTH_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")
    return await _exchange_google_code(code, redirect_uri)


@app.post("/connect/google_ads/exchange-code")
async def google_exchange_code(request: Request):
    form = await request.form()
    code = str(form.get("auth_code", "")).strip()
    if not code:
        return RedirectResponse("/connect?error=No+code+entered")
    return await _exchange_google_code(code, "urn:ietf:wg:oauth:2.0:oob")


async def _exchange_google_code(code: str, redirect_uri: str):
    c = creds()
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": c.get("GOOGLE_CLIENT_ID", ""),
        "client_secret": c.get("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode()
    try:
        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token", data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            tokens = json.loads(resp.read())
    except Exception as e:
        return RedirectResponse(f"/connect?error=Token+exchange+failed:+{str(e)[:80]}")

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        return RedirectResponse("/connect?error=No+refresh+token.+Revoke+app+at+myaccount.google.com/permissions+and+try+again")

    save_cred("GOOGLE_REFRESH_TOKEN", refresh_token)
    return RedirectResponse("/connect?success=Google+Ads+connected+successfully")


@app.get("/connect/mcc", response_class=HTMLResponse)
async def mcc_page(success: str = "", error: str = ""):
    alert = ""
    if success: alert = f'<div class="alert alert-success">✓ {success}</div>'
    if error:   alert = f'<div class="alert alert-error">✗ {error}</div>'

    body = f"""
    <div class="container" style="max-width:560px;">
      {alert}
      <div class="page-title">Connect MCC</div>
      <div class="page-subtitle">Google Ads Manager Account — audits all sub-accounts under it</div>
      <div class="panel">
        <form method="POST" action="/connect/mcc/save">
          <div class="form-group">
            <label class="form-label">MCC Customer ID</label>
            <input class="form-input" name="mcc_id" placeholder="123-456-7890" required>
            <div class="form-hint">Your MCC / Manager Account ID (different from individual account IDs)</div>
          </div>
          <div class="alert alert-info" style="margin-top:8px;">
            Make sure your Google OAuth (connected via Google Ads above) has access to this MCC.
          </div>
          <button type="submit" class="btn btn-primary">Save MCC</button>
        </form>
      </div>
    </div>"""
    return shell("chat", body, "MCC")


@app.post("/connect/mcc/save")
async def mcc_save(request: Request):
    form = await request.form()
    mcc_id = form.get("mcc_id", "").replace("-", "")
    if not mcc_id:
        return RedirectResponse("/connect/mcc?error=MCC+ID+is+required")
    save_cred("GOOGLE_ADS_LOGIN_CUSTOMER_ID", mcc_id)
    return RedirectResponse("/connect?success=MCC+connected")


@app.post("/connect/meta_ads/manual")
async def meta_manual_connect(request: Request):
    form = await request.form()
    save_cred("META_APP_ID", form.get("app_id", ""))
    save_cred("META_APP_SECRET", form.get("app_secret", ""))
    save_cred("META_BUSINESS_ACCOUNT_ID", form.get("account_id", ""))

    c = creds()
    base = get_server_base(request)
    redirect_uri = f"{base}/callback/meta"
    save_cred("_META_REDIRECT_URI", redirect_uri)

    params = urllib.parse.urlencode({
        "client_id": c.get("META_APP_ID", ""),
        "redirect_uri": redirect_uri,
        "scope": "ads_read,ads_management,business_management,read_insights",
        "response_type": "code",
    })
    return RedirectResponse(f"https://www.facebook.com/v19.0/dialog/oauth?{params}")


@app.get("/callback/meta")
async def meta_callback(code: str = "", error: str = ""):
    if error or not code:
        return RedirectResponse(f"/connect?error=Meta+auth+failed:+{error}")

    c = creds()
    redirect_uri = c.get("_META_REDIRECT_URI", "")
    url = (f"https://graph.facebook.com/v19.0/oauth/access_token"
           f"?client_id={c.get('META_APP_ID','')}"
           f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
           f"&client_secret={c.get('META_APP_SECRET','')}"
           f"&code={code}")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return RedirectResponse(f"/connect?error=Meta+token+failed:+{str(e)[:60]}")

    token = data.get("access_token")
    if not token:
        return RedirectResponse("/connect?error=Meta+did+not+return+an+access+token")

    ll_url = (f"https://graph.facebook.com/v19.0/oauth/access_token"
              f"?grant_type=fb_exchange_token"
              f"&client_id={c.get('META_APP_ID','')}"
              f"&client_secret={c.get('META_APP_SECRET','')}"
              f"&fb_exchange_token={token}")
    try:
        with urllib.request.urlopen(ll_url, timeout=15) as resp:
            token = json.loads(resp.read()).get("access_token", token)
    except Exception:
        pass

    save_cred("META_ACCESS_TOKEN", token)
    return RedirectResponse("/connect?success=Meta+Ads+connected")


@app.get("/disconnect/{platform}")
async def disconnect(platform: str):
    key_map = {
        "google_ads": ["GOOGLE_REFRESH_TOKEN", "GOOGLE_ADS_CUSTOMER_ID",
                       "GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
        "mcc":        ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"],
        "meta_ads":   ["META_ACCESS_TOKEN", "META_BUSINESS_ACCOUNT_ID"],
        "ga4":        ["GOOGLE_ANALYTICS_PROPERTY_ID"],
    }
    for key in key_map.get(platform, []):
        save_cred(key, "")
    label = platform.replace("_", " ").replace("mcc", "MCC").title()
    return RedirectResponse(f"/connect?success={label}+disconnected")


# ── Audit trigger ─────────────────────────────────────────────────────────────

@app.post("/audit/run")
async def run_audit(request: Request):
    body = await request.json()
    platform = body.get("platform", "all")
    task = "Run a full performance marketing audit" if platform == "all" \
           else f"Run a {platform.replace('_', ' ')} audit"
    cmd = ["python3", str(PROJECT_DIR / "audit_agent.py"), task]
    try:
        subprocess.Popen(cmd, cwd=str(PROJECT_DIR),
                         stdout=open(REPORTS_DIR / "server_run.log", "a"),
                         stderr=subprocess.STDOUT)
        return JSONResponse({"status": "started", "message": "Audit started — reports ready in 2-3 mins"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


# ── Agents ────────────────────────────────────────────────────────────────────

AGENTS = [
    {
        "id": "audit",
        "name": "Audit Agent",
        "desc": "Deep parallel audit across all connected platforms. 46 Google Ads checks, 46 Meta checks, 30 GA4 checks. Runs on your schedule or on-demand.",
        "status": "active",
        "icon": "🔍",
    },
    {
        "id": "paid_media",
        "name": "Paid Media Agent",
        "desc": "Executes bid adjustments, pauses underperformers, reallocates budget. Writes changes back to Google Ads API.",
        "status": "soon",
        "icon": "⚡",
    },
    {
        "id": "listen",
        "name": "Listen Agent",
        "desc": "Real-time monitoring. Alerts you when CPAs spike, budgets exhaust, or tracking breaks. Works 24/7.",
        "status": "soon",
        "icon": "👂",
    },
    {
        "id": "ceo",
        "name": "CEO Agent",
        "desc": "Weekly executive brief. Answers 'are my campaigns profitable?' with plain-English analysis.",
        "status": "soon",
        "icon": "📊",
    },
]


@app.get("/agents", response_class=HTMLResponse)
async def agents_page(saved: str = ""):
    schedule = get_cron_schedule()

    alert = f'<div class="alert alert-success">✓ Schedule saved</div>' if saved else ""

    # Map DOW number to label
    dow_opts = [("0","Sunday"),("1","Monday"),("2","Tuesday"),("3","Wednesday"),
                ("4","Thursday"),("5","Friday"),("6","Saturday"),("*","Every day")]
    dow_select = "".join(
        f'<option value="{v}" {"selected" if schedule["dow"]==v else ""}>{l}</option>'
        for v, l in dow_opts
    )
    hour_select = "".join(
        f'<option value="{h}" {"selected" if schedule["hour"]==str(h) else ""}>{h:02d}:00</option>'
        for h in range(0, 24)
    )

    agent_cards = ""
    for ag in AGENTS:
        is_active = ag["status"] == "active"
        badge = '<span class="badge-connected">Active</span>' if is_active \
                else '<span class="badge-soon">Coming Soon</span>'
        card_style = 'active' if is_active else ''
        agent_cards += f"""
        <div class="agent-card {card_style}">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px;">
            <div style="display:flex;gap:10px;align-items:flex-start;">
              <span style="font-size:20px;">{ag["icon"]}</span>
              <div>
                <div class="agent-name">{ag["name"]}</div>
                <div class="agent-desc">{ag["desc"]}</div>
              </div>
            </div>
            {badge}
          </div>
        </div>"""

    body = f"""
    <div class="container">
      {alert}
      <div class="page-title">Agents</div>
      <div class="page-subtitle">Choose which agents run on your schedule</div>

      <div class="section">
        <div class="section-label">Available Agents</div>
        <div style="display:flex;flex-direction:column;gap:10px;">{agent_cards}</div>
      </div>

      <div class="divider"></div>

      <div class="section">
        <div class="section-label">Audit Schedule</div>
        <div class="panel">
          <form method="POST" action="/agents/schedule">
            <div class="grid-2" style="gap:16px;background:none;">
              <div class="form-group">
                <label class="form-label">Run on</label>
                <select class="form-select" name="dow">{dow_select}</select>
              </div>
              <div class="form-group">
                <label class="form-label">At (hour)</label>
                <select class="form-select" name="hour">{hour_select}</select>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:16px;margin-top:4px;">
              <button type="submit" class="btn btn-primary">Save Schedule</button>
              <span style="font-size:13px;color:#4a4d5e;">Current: <code>{schedule["raw"]}</code></span>
            </div>
          </form>
        </div>
      </div>

      <div class="divider"></div>

      <div class="section">
        <div class="section-label">Run Now</div>
        <div class="panel">
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div>
              <div style="font-size:14px;font-weight:500;">Manual audit run</div>
              <div style="font-size:13px;color:#8b8fa8;">Triggers full audit across all connected platforms. Report in 2-3 mins.</div>
            </div>
            <div style="display:flex;align-items:center;gap:12px;">
              <span id="run-status" style="font-size:13px;color:#8b8fa8;display:none;"></span>
              <button class="btn btn-primary" onclick="runAudit()">▶ Run Audit</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <script>
    async function runAudit() {{
      const s = document.getElementById('run-status');
      s.style.display='inline';s.textContent='Starting...';
      const r = await fetch('/audit/run',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{platform:'all'}})}});
      const d = await r.json();
      s.textContent = d.message;
    }}
    </script>"""

    return shell("agents", body, "Agents")


@app.post("/agents/schedule")
async def save_schedule(request: Request):
    form = await request.form()
    hour = form.get("hour", "9")
    dow  = form.get("dow", "*")
    minute = "0"
    set_cron_schedule(minute, hour, dow)
    return RedirectResponse("/agents?saved=1", status_code=302)


# ── Reports ───────────────────────────────────────────────────────────────────

@app.get("/reports", response_class=HTMLResponse)
async def reports_page():
    reports = recent_reports(30)
    rows = ""
    for r in reports:
        icon = "📄" if r["is_pdf"] else "🌐"
        rows += f"""
        <div class="panel-row">
          <div>
            <div style="font-size:14px;font-weight:500;">{icon} {r['stem'].replace('_',' ').replace('-',' ').title()}</div>
            <div style="font-size:12px;color:#8b8fa8;">{r['modified']} · {r['size']}</div>
          </div>
          <a href="/reports/{r['name']}" target="_blank" class="btn btn-ghost btn-sm">View</a>
        </div>"""

    if not rows:
        rows = '<p style="color:#4a4d5e;font-size:14px;padding:20px 0;text-align:center;">No reports yet. Go to Agents → Run Audit.</p>'

    body = f"""
    <div class="container">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:28px;">
        <div>
          <div class="page-title">Reports</div>
          <div class="page-subtitle">All generated audit reports</div>
        </div>
        <button class="btn btn-primary" onclick="runAudit()">▶ Run Audit</button>
      </div>
      <div class="panel">{rows}</div>
    </div>
    <script>
    async function runAudit() {{
      const r = await fetch('/audit/run',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{platform:'all'}})}});
      const d = await r.json();
      alert(d.message);
    }}
    </script>"""

    return shell("reports", body, "Reports")


@app.get("/reports/{filename}")
async def serve_report(filename: str):
    from fastapi.responses import FileResponse
    path = REPORTS_DIR / filename
    if not path.exists() or ".." in filename:
        return HTMLResponse("Not found", status_code=404)
    media = "application/pdf" if filename.endswith(".pdf") else "text/html"
    return FileResponse(path, media_type=media)


# ── Settings ──────────────────────────────────────────────────────────────────

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(saved: str = ""):
    c = creds()

    def field(label, key, placeholder="", hint="", type_="text"):
        val = c.get(key, "")
        if val and "your_" in val:
            val = ""
        display = (val[:6] + "••••••" if val and len(val) > 8 else val) if type_ != "text" else val
        return f"""
        <div class="form-group">
          <label class="form-label">{label}</label>
          <input class="form-input" name="{key}" value="{display}"
                 placeholder="{placeholder or f'Enter {label}'}" type="{type_}">
          {"<div class='form-hint'>" + hint + "</div>" if hint else ""}
        </div>"""

    alert = '<div class="alert alert-success">✓ Settings saved</div>' if saved else ""

    body = f"""
    <div class="container" style="max-width:700px;">
      {alert}
      <div class="page-title">Settings</div>
      <div class="page-subtitle" style="margin-bottom:28px;">API keys and delivery channels</div>

      <form method="POST" action="/settings/save">

        <div class="section">
          <div class="section-label">AI Engine</div>
          <div class="panel">
            {field("Google AI API Key", "GOOGLE_AI_API_KEY", hint="aistudio.google.com → Get API Key (free tier — 1M tokens/day)", type_="password")}
            <div class="form-hint" style="margin-top:-8px;">No Google AI key? Leave blank — falls back to Claude Sonnet.</div>
          </div>
        </div>

        <div class="section">
          <div class="section-label">Delivery Channels</div>
          <div class="panel" style="margin-bottom:10px;">
            <div style="font-size:13px;font-weight:600;margin-bottom:12px;color:#f0f0f2;">Telegram</div>
            {field("Bot Token", "TELEGRAM_BOT_TOKEN", hint="@BotFather → /newbot", type_="password")}
            {field("Chat ID", "TELEGRAM_CHAT_ID", hint="@userinfobot → /start to get your ID")}
          </div>
          <div class="panel" style="margin-bottom:10px;">
            <div style="font-size:13px;font-weight:600;margin-bottom:12px;color:#f0f0f2;">Slack</div>
            {field("Webhook URL", "SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/...", hint="Slack App → Incoming Webhooks → Add to Workspace", type_="password")}
            {field("Channel", "SLACK_CHANNEL", "#marketing-alerts", hint="Channel the bot will post to")}
          </div>
          <div class="panel">
            <div style="font-size:13px;font-weight:600;margin-bottom:12px;color:#f0f0f2;">WhatsApp</div>
            {field("Twilio Account SID", "TWILIO_ACCOUNT_SID", hint="console.twilio.com", type_="password")}
            {field("Twilio Auth Token", "TWILIO_AUTH_TOKEN", type_="password")}
            {field("WhatsApp From Number", "TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886", hint="Twilio Sandbox or Business number")}
            {field("Your WhatsApp Number", "WHATSAPP_TO_NUMBER", "whatsapp:+919876543210", hint="Your number with country code")}
          </div>
        </div>

        <div class="section">
          <div class="section-label">GA4 Analytics</div>
          <div class="panel">
            {field("GA4 Property ID", "GOOGLE_ANALYTICS_PROPERTY_ID", "123456789", hint="GA4 → Admin → Property Settings → Property ID")}
          </div>
        </div>

        <div class="section">
          <div class="section-label">Audit Config</div>
          <div class="panel">
            {field("Date Range (days)", "AUDIT_DATE_RANGE_DAYS", "30", hint="Default lookback window for all audits")}
          </div>
        </div>

        <button type="submit" class="btn btn-primary">Save Settings</button>
      </form>
    </div>"""

    return shell("settings", body, "Settings")


@app.post("/settings/save")
async def settings_save(request: Request):
    form = await request.form()
    for key, value in form.items():
        if value and "••••" not in str(value):
            save_cred(key, str(value))
    return RedirectResponse("/settings?saved=1", status_code=302)


# ── JSON API (used by new UI) ──────────────────────────────────────────────────

@app.get("/api/status")
async def api_status():
    return JSONResponse({"platforms": platform_status()})


@app.get("/api/reports")
async def api_reports():
    items = []
    for f in sorted(REPORTS_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.suffix in (".pdf", ".html") and f.is_file():
            size_kb = round(f.stat().st_size / 1024, 1)
            items.append({
                "name": f.name,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%d %b %Y %H:%M"),
                "size": f"{size_kb} KB",
            })
    return JSONResponse({"reports": items})


@app.get("/api/settings")
async def api_settings():
    c = creds()
    safe_keys = ["AGENCY_NAME", "AGENCY_EMAIL", "AGENCY_WEBSITE", "TELEGRAM_CHAT_ID"]
    return JSONResponse({k: c.get(k, "") for k in safe_keys})


@app.post("/api/save-credentials")
async def api_save_credentials(request: Request):
    data = await request.json()
    for key, value in data.items():
        if value and "••" not in str(value):
            save_cred(str(key), str(value))
    return JSONResponse({"ok": True, "saved": list(data.keys())})


@app.post("/api/lead")
async def api_lead(request: Request):
    data = await request.json()
    bot_token = os.environ.get("LEAD_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id   = os.environ.get("LEAD_CHAT_ID")   or os.environ.get("TELEGRAM_CHAT_ID", "")
    if bot_token and chat_id:
        try:
            import urllib.request as ureq, urllib.parse as uparse
            msg = data.get("message", f"New lead: {data.get('email','?')}")
            payload = json.dumps({"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}).encode()
            req = ureq.Request(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                data=payload, headers={"Content-Type": "application/json"}
            )
            ureq.urlopen(req, timeout=5)
        except Exception as ex:
            print(f"[lead] Telegram send failed: {ex}")
    return JSONResponse({"ok": True})


@app.get("/api/nemoclaw-health")
async def api_nemoclaw_health():
    import urllib.request as ureq
    try:
        with ureq.urlopen("http://127.0.0.1:8080/health", timeout=2) as r:
            return JSONResponse(json.loads(r.read()))
    except Exception:
        return JSONResponse({"status": "unreachable", "rails_loaded": False})


@app.get("/api/update-check")
async def api_update_check():
    try:
        local = subprocess.check_output(
            ["git", "-C", str(PROJECT_DIR), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        req = urllib.request.Request(
            "https://api.github.com/repos/Get-Second-Step/clawboard-agent/commits/main",
            headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "ClawBoard"}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        remote = str(data["sha"])
        up_to_date = local == remote
        local_short = local[:7]
        remote_short = remote[:7]
        msg = str(data["commit"]["message"]).splitlines()[0]
        return JSONResponse({
            "up_to_date": up_to_date,
            "local": local_short,
            "remote": remote_short,
            "message": msg,
        })
    except Exception as e:
        return JSONResponse({"up_to_date": True, "error": str(e)})


@app.post("/api/update")
async def api_update():
    try:
        subprocess.check_call(
            ["git", "-C", str(PROJECT_DIR), "fetch", "--quiet"],
            stderr=subprocess.DEVNULL
        )
        subprocess.check_call(
            ["git", "-C", str(PROJECT_DIR), "reset", "--hard", "origin/main", "--quiet"],
            stderr=subprocess.DEVNULL
        )
        # Restart service (works whether running under systemd or directly)
        subprocess.Popen(
            ["bash", "-c", "sleep 1 && (systemctl restart clawboard 2>/dev/null || kill -HUP 1 2>/dev/null || true)"]
        )
        return JSONResponse({"ok": True, "message": "Updated — restarting in 1 second…"})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n  ╔══════════════════════════════════════╗")
    print(f"  ║  ClawBoard Pro  ·  http://0.0.0.0:{port}  ║")
    print(f"  ╚══════════════════════════════════════╝\n")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
