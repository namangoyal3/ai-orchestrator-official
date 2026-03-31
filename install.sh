#!/usr/bin/env bash
# Namango CLI — One-line installer
# Usage: curl -fsSL https://raw.githubusercontent.com/namangoyal3/ai-orchestrator-official/main/install.sh | bash

set -e

GATEWAY="https://ai-gateway-backend-production.up.railway.app"
REPO="https://github.com/namangoyal3/ai-orchestrator-official.git"
INSTALL_DIR="$HOME/.namango"
BIN_DIR="$HOME/.local/bin"

# ── colours ───────────────────────────────────────────────────────────────────
BOLD='\033[1m'; CYAN='\033[0;36m'; GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
info() { echo -e "${CYAN}  ->  ${NC}$*"; }
ok()   { echo -e "${GREEN}  OK  ${NC}$*"; }
die()  { echo -e "${RED}  ERR $*${NC}"; exit 1; }

echo ""
echo -e "${BOLD}${CYAN}  +--------------------------------------+${NC}"
echo -e "${BOLD}${CYAN}  |   NAMANGO  AI Gateway Installer     |${NC}"
echo -e "${BOLD}${CYAN}  +--------------------------------------+${NC}"
echo ""

# ── 1. check node ─────────────────────────────────────────────────────────────
command -v node >/dev/null 2>&1 || die "Node.js is required. Install from https://nodejs.org"
NODE_MAJOR=$(node -e "process.stdout.write(process.versions.node.split('.')[0])")
[ "$NODE_MAJOR" -ge 18 ] 2>/dev/null || die "Node.js v18+ required (found $(node -v))"
ok "Node.js $(node -v)"

# ── 2. check backend reachable ────────────────────────────────────────────────
info "Checking gateway..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 "$GATEWAY/health" 2>/dev/null || echo "000")
[ "$STATUS" = "200" ] || die "Gateway unreachable (HTTP $STATUS). Check your connection."
ok "Gateway online at $GATEWAY"

# ── 3. clone / update ─────────────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/src/.git" ]; then
    info "Updating existing install..."
    git -C "$INSTALL_DIR/src" pull --quiet
else
    info "Cloning CLI from GitHub..."
    rm -rf "$INSTALL_DIR/src"
    git clone --quiet --depth 1 "$REPO" "$INSTALL_DIR/src"
fi
ok "CLI source ready"

# ── 4. npm install ────────────────────────────────────────────────────────────
info "Installing npm dependencies..."
cd "$INSTALL_DIR/src/cli/create-namango-app"
npm install --silent --no-fund --no-audit 2>/dev/null
ok "Dependencies installed"

# ── 5. link the namango binary ────────────────────────────────────────────────
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/namango" << 'BINEOF'
#!/usr/bin/env bash
exec node "$HOME/.namango/src/cli/create-namango-app/bin/index.js" "$@"
BINEOF
chmod +x "$BIN_DIR/namango"
ok "namango command linked -> $BIN_DIR/namango"

# ── 6. auto-provision an API key ─────────────────────────────────────────────
CONFIG_FILE="$HOME/.namango/config.json"
SKIP_PROVISION=""

# Reuse existing key if it still works
if [ -f "$CONFIG_FILE" ]; then
    EXISTING=$(node -e "try{const c=require('$CONFIG_FILE');process.stdout.write(c.apiKey||'')}catch(e){}" 2>/dev/null || true)
    if [ -n "$EXISTING" ]; then
        HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 \
            -H "X-API-Key: $EXISTING" "$GATEWAY/v1/marketplace/agents" 2>/dev/null || echo "000")
        if [ "$HTTP" = "200" ]; then
            SKIP_PROVISION=1
            ok "Existing API key is valid"
        fi
    fi
fi

if [ -z "$SKIP_PROVISION" ]; then
    info "Provisioning your gateway API key..."

    # unique slug: username + truncated timestamp
    BASE=$(echo "${USER:-user}${HOSTNAME:-host}" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9' | cut -c1-12)
    SLUG="${BASE}-$(date +%s | rev | cut -c1-5 | rev)"

    ORG=$(curl -s --max-time 10 -X POST "$GATEWAY/admin/organizations" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"${USER:-user}\",\"slug\":\"$SLUG\",\"plan\":\"starter\"}" 2>/dev/null)
    ORG_ID=$(node -e "try{process.stdout.write(JSON.parse('$ORG').id||'')}catch(e){}" 2>/dev/null || true)
    [ -n "$ORG_ID" ] || die "Could not create org. Response: $ORG"

    KEY_RESP=$(curl -s --max-time 10 -X POST "$GATEWAY/admin/api-keys" \
        -H "Content-Type: application/json" \
        -d "{\"org_id\":\"$ORG_ID\",\"name\":\"cli\",\"permissions\":[\"read\",\"write\"]}" 2>/dev/null)
    API_KEY=$(node -e "try{process.stdout.write(JSON.parse('$KEY_RESP').key||'')}catch(e){}" 2>/dev/null || true)
    [ -n "$API_KEY" ] || die "Could not get API key. Response: $KEY_RESP"

    mkdir -p "$HOME/.namango"
    printf '{"apiKey":"%s"}\n' "$API_KEY" > "$CONFIG_FILE"
    ok "API key provisioned and saved"
fi

# ── 7. add BIN_DIR to PATH permanently ───────────────────────────────────────
export PATH="$BIN_DIR:$PATH"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    SHELL_RC="$HOME/.zshrc"
    [ -f "$HOME/.bashrc" ] && [ ! -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.bashrc"
    if ! grep -q "$BIN_DIR" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"  # namango" >> "$SHELL_RC"
        ok "PATH updated in $SHELL_RC"
    fi
fi

# ── 8. smoke test ─────────────────────────────────────────────────────────────
echo ""
"$BIN_DIR/namango" whoami
echo ""
echo -e "${BOLD}${GREEN}  Namango is ready. Try these:${NC}"
echo ""
echo -e "  ${CYAN}namango agents${NC}              # browse 100+ AI agents"
echo -e "  ${CYAN}namango run \"your task\"${NC}      # route any task to the best LLM"
echo -e "  ${CYAN}namango architect${NC}            # design your AI product stack"
echo -e "  ${CYAN}namango interactive${NC}          # full interactive mode"
echo ""
echo -e "  ${BOLD}Note:${NC} open a new terminal (or run ${CYAN}source ~/.zshrc${NC}) for PATH to take effect."
echo ""
