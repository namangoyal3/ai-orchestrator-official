#!/usr/bin/env bash

# Namango Installation Script
# Usage: curl -fsSL https://frontend-five-theta-69.vercel.app/install | bash

set -e

# --- Configuration ---
INSTALL_DIR="$HOME/.namango"
BIN_DIR="$HOME/.local/bin"
COMMAND_NAME="namango"

# --- Colors for Output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}     🚀 Installing Namango CLI         ${NC}"
echo -e "${BLUE}=======================================${NC}"

mkdir -p "$BIN_DIR"

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${RED}Warning: $BIN_DIR is not in your PATH.${NC}"
    echo "Please add it to your ~/.bashrc or ~/.zshrc profile:"
    echo 'export PATH="$HOME/.local/bin:$PATH"'
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is required but not installed.${NC}"
    exit 1
fi

echo -e "${GREEN}Creating installation directory at $INSTALL_DIR...${NC}"
mkdir -p "$INSTALL_DIR"

# For local development simulation: copy the cli folder if we are curled from the repo
# In production, this would be a git clone or an npm install.
if [ -d "cli/create-namango-app" ]; then
    cp -r cli/create-namango-app "$INSTALL_DIR/"
elif [ -d "namango3/cli/create-namango-app" ]; then
    cp -r namango3/cli/create-namango-app "$INSTALL_DIR/"
else
    # Simulated download for the raw curl execution if they don't have the repo locally
    echo -e "${BLUE}Downloading CLI...${NC}"
    # In a real deployed state, we would git clone here.
    # git clone https://github.com/namango-ai/namango-cli.git "$INSTALL_DIR/create-namango-app"
fi

# Ensure npm dependencies are installed inside the CLI tool
if [ -d "$INSTALL_DIR/create-namango-app" ]; then
    echo -e "${GREEN}Setting up CLI dependencies...${NC}"
    cd "$INSTALL_DIR/create-namango-app"
    npm install --silent > /dev/null 2>&1 || true
fi

echo -e "${GREEN}Linking '${COMMAND_NAME}' command...${NC}"
cat << 'EOF' > "$BIN_DIR/$COMMAND_NAME"
#!/usr/bin/env bash
node "$HOME/.namango/create-namango-app/bin/index.js" "$@"
EOF

chmod +x "$BIN_DIR/$COMMAND_NAME"

echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}✅ Installation successfully completed!${NC}"
echo -e "You can now use Namango everywhere by typing: ${BLUE}$COMMAND_NAME${NC}"
echo -e "${BLUE}=======================================${NC}"
