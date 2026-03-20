#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
#  ClawBoard — Website Deploy Script
#  Deploys landing pages to clawboard.pro on the VPS
#  Run on the VPS: bash deploy-web.sh
# ──────────────────────────────────────────────────────────────────────────────
set -e

DOMAIN="clawboard.pro"
WEB_ROOT="/var/www/clawboard.pro"
REPO_DIR="$HOME/clawboard-agent"

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${CYAN}[deploy]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }

echo ""
echo -e "${CYAN}  Deploying clawboard.pro${NC}"
echo ""

# ── 1. Install nginx + deps ───────────────────────────────────────────────────
if ! command -v nginx &>/dev/null; then
    info "Installing nginx..."
    apt-get update -qq && apt-get install -y -qq nginx
fi
if ! command -v dig &>/dev/null; then
    apt-get install -y -qq dnsutils 2>/dev/null || true
fi
success "nginx ready"

# ── 2. Remove old ClawBoard pages (green-themed) ─────────────────────────────
info "Removing old landing pages..."

# Wipe default nginx page
rm -f /var/www/html/index.nginx-debian.html /var/www/html/index.html

# Remove any previous clawboard web roots
for OLD_ROOT in /var/www/html/clawboard /var/www/clawboard /var/www/clawboard-landing /root/clawboard-landing /root/clawboard-vps; do
    [ -d "$OLD_ROOT" ] && rm -rf "$OLD_ROOT" && info "Removed $OLD_ROOT"
done

# Disable old nginx site configs (keep default disabled)
for OLD_CONF in /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/clawboard /etc/nginx/sites-enabled/clawboard-landing; do
    [ -L "$OLD_CONF" ] && rm -f "$OLD_CONF" && info "Disabled old config: $OLD_CONF"
done

success "Old pages cleared"

# ── 3. Pull latest from GitHub ────────────────────────────────────────────────
info "Pulling latest from GitHub..."
git -C "$REPO_DIR" pull --quiet
success "Repo up to date"

# ── 4. Copy web files to web root ─────────────────────────────────────────────
info "Copying files to $WEB_ROOT..."
rm -rf "$WEB_ROOT"
mkdir -p "$WEB_ROOT/docs"
cp "$REPO_DIR/index.html"   "$WEB_ROOT/index.html"
cp "$REPO_DIR/upgrade.html" "$WEB_ROOT/upgrade.html"
cp "$REPO_DIR/docs/installation.html"  "$WEB_ROOT/docs/installation.html"
cp "$REPO_DIR/docs/how-it-works.html"  "$WEB_ROOT/docs/how-it-works.html"
success "Web files copied"

# ── 5. Write nginx site config ────────────────────────────────────────────────
info "Configuring nginx for $DOMAIN..."
cat > /etc/nginx/sites-available/clawboard.pro <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    root $WEB_ROOT;
    index index.html;

    # Landing pages
    location / {
        try_files \$uri \$uri/ \$uri.html =404;
    }

    # Docs subdirectory
    location /docs/ {
        try_files \$uri \$uri/ =404;
    }

    # Clean URLs — /upgrade → /upgrade.html
    location = /upgrade {
        rewrite ^ /upgrade.html last;
    }
    location = /docs/installation {
        rewrite ^ /docs/installation.html last;
    }
    location = /docs/how-it-works {
        rewrite ^ /docs/how-it-works.html last;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Gzip
    gzip on;
    gzip_types text/html text/css application/javascript;
}
EOF

ln -sf /etc/nginx/sites-available/clawboard.pro /etc/nginx/sites-enabled/clawboard.pro
nginx -t && systemctl reload nginx
success "nginx configured and reloaded"

# ── 6. SSL with Let's Encrypt ─────────────────────────────────────────────────
if ! command -v certbot &>/dev/null; then
    info "Installing certbot..."
    apt-get install -y -qq certbot python3-certbot-nginx
fi

# Only run certbot if DNS is already pointing to this server
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null)
DOMAIN_IP=$(dig +short "$DOMAIN" 2>/dev/null | head -1)

if [ "$SERVER_IP" = "$DOMAIN_IP" ]; then
    info "DNS confirmed — requesting SSL certificate..."
    certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" \
        --non-interactive --agree-tos --email admin@getsecondstep.com \
        --redirect
    success "SSL certificate installed — https://$DOMAIN is live"
else
    warn "DNS not yet pointed to this server ($SERVER_IP)."
    warn "Point clawboard.pro → $SERVER_IP in your Hostinger DNS panel, then re-run this script."
    echo ""
    echo -e "  ${CYAN}Site is live over HTTP at:${NC} http://$SERVER_IP"
    echo -e "  ${CYAN}Run after DNS propagates:${NC} certbot --nginx -d $DOMAIN -d www.$DOMAIN"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Website deployed!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  Pages live at:"
echo -e "  ${GREEN}➜${NC}  http://$DOMAIN/"
echo -e "  ${GREEN}➜${NC}  http://$DOMAIN/upgrade.html"
echo -e "  ${GREEN}➜${NC}  http://$DOMAIN/docs/installation.html"
echo -e "  ${GREEN}➜${NC}  http://$DOMAIN/docs/how-it-works.html"
echo ""
echo -e "  ClawBoard agent UI still at: http://$SERVER_IP:3000"
echo ""
