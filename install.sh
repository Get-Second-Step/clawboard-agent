#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
#  ClawBoard Audit Agent — VPS Installer
#  Usage: curl -fsSL https://raw.githubusercontent.com/Get-Second-Step/clawboard-agent/main/install.sh | bash
# ──────────────────────────────────────────────────────────────────────────────
set -e

REPO="https://github.com/Get-Second-Step/clawboard-agent.git"
INSTALL_DIR="$HOME/clawboard-agent"
PYTHON_VERSION="3.11"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[ClawBoard]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
die()     { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo -e "${CYAN}  ██████╗██╗      █████╗ ██╗    ██╗██████╗  ██████╗  █████╗ ██████╗ ██████╗${NC}"
echo -e "${CYAN} ██╔════╝██║     ██╔══██╗██║    ██║██╔══██╗██╔═══██╗██╔══██╗██╔══██╗██╔══██╗${NC}"
echo -e "${YELLOW} ██║     ██║     ███████║██║ █╗ ██║██████╔╝██║   ██║███████║██████╔╝██║  ██║${NC}"
echo -e "${YELLOW} ██║     ██║     ██╔══██║██║███╗██║██╔══██╗██║   ██║██╔══██║██╔══██╗██║  ██║${NC}"
echo -e "${YELLOW} ╚██████╗███████╗██║  ██║╚███╔███╔╝██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝${NC}"
echo -e "${NC}  ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ${NC}"
echo ""
echo -e "  ${YELLOW}AI Agent Audit Engine${NC} — Installing on $(hostname)"
echo ""

# ── 1. System dependencies ────────────────────────────────────────────────────
info "Checking system dependencies..."

if ! command -v python3 &>/dev/null; then
    info "Installing Python $PYTHON_VERSION..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y -qq python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python3-pip
    elif command -v yum &>/dev/null; then
        sudo yum install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-pip
    else
        die "Cannot install Python automatically. Please install Python $PYTHON_VERSION manually."
    fi
fi
success "Python: $(python3 --version)"

# Install uv (fast Python package manager)
if ! command -v uv &>/dev/null; then
    info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    source "$HOME/.cargo/env" 2>/dev/null || true
fi
success "uv: $(uv --version)"

# Install git
if ! command -v git &>/dev/null; then
    info "Installing git..."
    sudo apt-get install -y -qq git 2>/dev/null || sudo yum install -y git 2>/dev/null || die "Please install git manually."
fi
success "git: $(git --version | head -1)"

# Chrome / Chromium (for PDF generation)
if ! command -v google-chrome &>/dev/null && ! command -v chromium-browser &>/dev/null && ! command -v chromium &>/dev/null; then
    warn "Chrome not found — PDF generation will be skipped (HTML reports still work)."
    warn "To enable PDFs: sudo apt-get install -y chromium-browser"
else
    success "Chrome/Chromium found"
fi

# ── 2. Clone repo ─────────────────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
    info "Updating existing installation..."
    git -C "$INSTALL_DIR" pull --quiet
else
    info "Cloning ClawBoard agent..."
    git clone --quiet "$REPO" "$INSTALL_DIR"
fi
success "Repo ready at $INSTALL_DIR"

# ── 3. Install Python dependencies ───────────────────────────────────────────
cd "$INSTALL_DIR"
info "Setting up Python virtual environment..."
VENV_DIR="$INSTALL_DIR/.venv"
if command -v uv &>/dev/null; then
    uv venv "$VENV_DIR" -q
else
    python3 -m venv "$VENV_DIR"
fi
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
success "Virtualenv ready at $VENV_DIR"

info "Installing Python dependencies..."
if command -v uv &>/dev/null; then
    uv pip install --python "$VENV_PYTHON" -r requirements.txt -q
else
    "$VENV_PIP" install -r requirements.txt -q
fi

# Install NemoClaw dependencies (guardrails security layer)
info "Installing NemoClaw security layer..."
if command -v uv &>/dev/null; then
    uv pip install --python "$VENV_PYTHON" fastapi uvicorn "nemoguardrails>=0.8.0" pydantic -q 2>/dev/null || \
        warn "NemoClaw optional deps skipped — will run in validation-only mode"
else
    "$VENV_PIP" install fastapi uvicorn "nemoguardrails>=0.8.0" pydantic -q 2>/dev/null || \
        warn "NemoClaw optional deps skipped — will run in validation-only mode"
fi
success "Dependencies installed"

# ── 4. Credentials setup ─────────────────────────────────────────────────────
CREDS="$INSTALL_DIR/config/credentials.env"
if [ ! -f "$CREDS" ] || grep -q "your_google_ai_api_key_here" "$CREDS"; then
    cp "$INSTALL_DIR/config/credentials.env.example" "$CREDS" 2>/dev/null || true
    echo ""
    warn "Credentials not configured yet."
    echo ""
    echo -e "  Edit your credentials file:"
    echo -e "  ${CYAN}nano $CREDS${NC}"
    echo ""
    echo -e "  Required keys:"
    echo -e "  • GOOGLE_AI_API_KEY        — aistudio.google.com"
    echo -e "  • GOOGLE_ADS_DEVELOPER_TOKEN"
    echo -e "  • GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET"
    echo -e "  • GOOGLE_REFRESH_TOKEN     — run: python3 scripts/generate_google_token.py"
    echo -e "  • TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID  (optional but recommended)"
    echo ""
fi

# ── 5. Start NemoClaw security layer (port 8080, internal) ───────────────────
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

if command -v systemctl &>/dev/null; then
    cat > /etc/systemd/system/nemoclaw.service <<EOF
[Unit]
Description=NemoClaw — NVIDIA NeMo Guardrails Security Layer
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$INSTALL_DIR/nemoclaw
ExecStart=$VENV_DIR/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8080
Restart=always
RestartSec=5
Environment=PATH=$VENV_DIR/bin:$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin
Environment=LOG_LEVEL=info

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable nemoclaw --quiet
    systemctl restart nemoclaw
    # Give NemoClaw 3s to start before openclaw tries to use it
    sleep 3
    success "NemoClaw security layer started (internal port 8080)"
else
    pkill -f "uvicorn main:app" 2>/dev/null || true
    nohup "$VENV_DIR/bin/python" -m uvicorn main:app --host 127.0.0.1 --port 8080 \
        > "$INSTALL_DIR/reports/nemoclaw.log" 2>&1 &
    sleep 3
    success "NemoClaw started (nohup, internal port 8080)"
fi

# ── Start OpenClaw connect server (port 3000) ─────────────────────────────────
if command -v systemctl &>/dev/null; then
    cat > /etc/systemd/system/clawboard.service <<EOF
[Unit]
Description=ClawBoard Connect Server (OpenClaw)
After=network.target nemoclaw.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$INSTALL_DIR
ExecStart=$VENV_DIR/bin/python -m uvicorn server:app --host 0.0.0.0 --port 3000
Restart=always
RestartSec=5
Environment=PATH=$VENV_DIR/bin:$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin
Environment=NEMOCLAW_URL=http://127.0.0.1:8080

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable clawboard --quiet
    systemctl restart clawboard
    success "OpenClaw gateway started on port 3000"
else
    pkill -f "uvicorn server:app" 2>/dev/null || true
    NEMOCLAW_URL=http://127.0.0.1:8080 nohup "$VENV_DIR/bin/python" -m uvicorn server:app --host 0.0.0.0 --port 3000 \
        > "$INSTALL_DIR/reports/server.log" 2>&1 &
    success "OpenClaw started on port 3000 (nohup)"
fi

# Open firewall port 3000 if ufw is active
if command -v ufw &>/dev/null && ufw status | grep -q "active"; then
    ufw allow 3000/tcp --quiet 2>/dev/null || true
    success "Firewall: port 3000 opened"
fi

# ── 6. Set up daily cron audit ────────────────────────────────────────────────
CRON_CMD="cd $INSTALL_DIR && $VENV_DIR/bin/python audit_agent.py 'Run daily performance marketing audit' >> $INSTALL_DIR/reports/cron.log 2>&1"
if ! crontab -l 2>/dev/null | grep -q "clawboard\|audit_agent"; then
    (crontab -l 2>/dev/null; echo "0 9 * * * $CRON_CMD  # clawboard-daily") | crontab -
    success "Daily 9am audit cron installed"
else
    warn "Cron job already exists — skipping"
fi

# ── 7. Create run alias ───────────────────────────────────────────────────────
SHELL_RC="$HOME/.bashrc"
[ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"

if ! grep -q "clawboard" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# ClawBoard" >> "$SHELL_RC"
    echo "alias clawboard='cd $INSTALL_DIR && $VENV_DIR/bin/python audit_agent.py'" >> "$SHELL_RC"
    echo "alias clawboard-logs='tail -f $INSTALL_DIR/reports/cron.log'" >> "$SHELL_RC"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ClawBoard installed successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${YELLOW}Open this in your browser:${NC}"
echo -e "  ${GREEN}  ➜  http://${SERVER_IP}:3000${NC}"
echo ""
echo -e "  From there you can:"
echo -e "  • Connect Google Ads, Meta Ads and GA4 with one click"
echo -e "  • Add API keys in Settings (no terminal needed)"
echo -e "  • Run audits and view PDF reports"
echo ""
echo -e "  ${YELLOW}Services running:${NC}"
echo -e "  • ${GREEN}OpenClaw${NC}   — http://${SERVER_IP}:3000  (web UI + agent gateway)"
echo -e "  • ${GREEN}NemoClaw${NC}   — 127.0.0.1:8080           (security layer, internal)"
echo -e "  • ${GREEN}Deep Agents${NC} — on-demand via audit_agent.py"
echo ""
echo -e "  Verify NemoClaw: ${CYAN}curl http://127.0.0.1:8080/health${NC}"
echo -e "  ${YELLOW}Logs:${NC} ${CYAN}tail -f $INSTALL_DIR/reports/cron.log${NC}"
echo ""
