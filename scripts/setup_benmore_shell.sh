#!/bin/bash
# Setup Benmore API global shell integration

set -e

echo "🚀 Setting up Benmore API global shell integration..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect shell
SHELL_RC="$HOME/.zshrc"
if [[ "$SHELL" == *"bash"* ]]; then
    SHELL_RC="$HOME/.bashrc"
elif [[ "$SHELL" == *"fish"* ]]; then
    SHELL_RC="$HOME/.config/fish/config.fish"
fi

echo -e "${CYAN}Detected shell: $(basename $SHELL)${NC}"
echo -e "${CYAN}Config file: $SHELL_RC${NC}\n"

# Step 1: Verify API key
echo -e "${CYAN}Step 1: Verify API key${NC}"
if [[ -z "$BM_API_KEY" ]]; then
    echo -e "${YELLOW}⚠ BM_API_KEY not set in environment${NC}"
    read -sp "Enter your Benmore API key (bpk_...): " api_key && echo
    export BM_API_KEY="$api_key"
else
    echo -e "${GREEN}✓ API key found in environment${NC}"
fi

# Step 2: Create config file
echo -e "\n${CYAN}Step 2: Create config file${NC}"
mkdir -p ~/.benmore
cat > ~/.benmore/config << EOF
{
  "api_key": "$BM_API_KEY"
}
EOF
chmod 600 ~/.benmore/config
echo -e "${GREEN}✓ Config file created at ~/.benmore/config${NC}"

# Step 3: Add shell aliases
echo -e "\n${CYAN}Step 3: Add shell aliases${NC}"

# Check if alias already exists
if grep -q 'alias benmore=' "$SHELL_RC" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Alias 'benmore' already exists in $SHELL_RC${NC}"
else
    cat >> "$SHELL_RC" << 'EOF'

# Benmore API shortcuts
alias benmore="bm benmore"
alias bchannel="bm benmore channels"
alias bprojects="bm benmore projects"
alias bcontext="bm benmore context"
alias bstatus="bm benmore status"
alias bteam="bm benmore team"
EOF
    echo -e "${GREEN}✓ Added aliases to $SHELL_RC${NC}"
fi

# Step 4: Create command symlink (optional)
echo -e "\n${CYAN}Step 4: Create global command (optional)${NC}"
BM_PATH=$(which bm)
if [[ ! -z "$BM_PATH" ]]; then
    if [[ ! -e /usr/local/bin/benmore ]]; then
        # Try to create symlink
        if sudo ln -s "$BM_PATH" /usr/local/bin/benmore 2>/dev/null; then
            echo -e "${GREEN}✓ Created symlink: /usr/local/bin/benmore${NC}"
        else
            echo -e "${YELLOW}ℹ Could not create /usr/local/bin/benmore (requires sudo)${NC}"
            echo -e "${YELLOW}  You can still use 'bm benmore' or 'benmore' (alias)${NC}"
        fi
    else
        echo -e "${GREEN}✓ Symlink already exists at /usr/local/bin/benmore${NC}"
    fi
fi

# Step 5: Verify installation
echo -e "\n${CYAN}Step 5: Verify installation${NC}"
source "$SHELL_RC"  # Reload shell config
if bm benmore projects &>/dev/null; then
    echo -e "${GREEN}✓ Benmore API is working!${NC}"
    echo -e "${GREEN}✓ You can now use: benmore, bchannel, bprojects, etc.${NC}"
else
    echo -e "${RED}✗ Error: bm benmore failed${NC}"
    echo -e "${YELLOW}  Try: export BM_API_KEY='bpk_...'${NC}"
    exit 1
fi

# Step 6: Show quick start
echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Quick Start Commands${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}List your projects:${NC}"
echo -e "  ${GREEN}benmore projects${NC}"

echo -e "\n${YELLOW}Search projects:${NC}"
echo -e "  ${GREEN}benmore projects --search 'api redesign'${NC}"

echo -e "\n${YELLOW}Get Slack channels:${NC}"
echo -e "  ${GREEN}benmore channels${NC}"

echo -e "\n${YELLOW}Get complete project context:${NC}"
echo -e "  ${GREEN}benmore context <project-id>${NC}"

echo -e "\n${YELLOW}Check project status:${NC}"
echo -e "  ${GREEN}benmore status <project-id>${NC}"

echo -e "\n${YELLOW}List team members:${NC}"
echo -e "  ${GREEN}benmore team <project-id>${NC}"

echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo -e "Reload your shell: ${CYAN}source $SHELL_RC${NC}\n"
