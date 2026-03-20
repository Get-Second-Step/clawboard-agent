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
info "Installing Python dependencies..."
uv pip install --system -r requirements.txt -q 2>/dev/null || \
    uv pip install -e "." -q 2>/dev/null || \
    pip3 install -r requirements.txt -q
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

# ── 5. Set up daily cron heartbeat ────────────────────────────────────────────
CRON_CMD="cd $INSTALL_DIR && uv run python audit_agent.py 'Run daily heartbeat audit' >> $INSTALL_DIR/reports/cron.log 2>&1"
if ! crontab -l 2>/dev/null | grep -q "clawboard\|audit_agent"; then
    (crontab -l 2>/dev/null; echo "0 9 * * * $CRON_CMD  # clawboard-daily") | crontab -
    success "Daily 9am cron job installed"
else
    warn "Cron job already exists — skipping"
fi

# ── 6. Create run alias ───────────────────────────────────────────────────────
SHELL_RC="$HOME/.bashrc"
[ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"

if ! grep -q "clawboard" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# ClawBoard Audit Agent" >> "$SHELL_RC"
    echo "alias clawboard='cd $INSTALL_DIR && uv run python audit_agent.py'" >> "$SHELL_RC"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ClawBoard installed successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${YELLOW}Next steps:${NC}"
echo -e "  1. Add credentials:   ${CYAN}nano $CREDS${NC}"
echo -e "  2. Generate token:    ${CYAN}cd $INSTALL_DIR && python3 scripts/generate_google_token.py${NC}"
echo -e "  3. Run your first audit:"
echo -e "     ${CYAN}cd $INSTALL_DIR && uv run python audit_agent.py \"Audit my Google Ads account\"${NC}"
echo ""
echo -e "  Reports saved to: ${CYAN}$INSTALL_DIR/reports/${NC}"
echo -e "  Logs:             ${CYAN}$INSTALL_DIR/reports/cron.log${NC}"
echo ""
