#!/bin/bash
# Modern Terminal Setup — Install Script
# Idempotent: safe to re-run. Skips already-installed tools.
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $1"; }
skip() { echo -e "${YELLOW}⏭${NC} $1 (already installed)"; }
fail() { echo -e "${RED}✗${NC} $1"; }

# --- Detect package manager ---
if command -v brew >/dev/null 2>&1; then
    PM="brew"
    INSTALL="brew install"
elif command -v apt-get >/dev/null 2>&1; then
    PM="apt"
    INSTALL="sudo apt-get install -y"
elif command -v dnf >/dev/null 2>&1; then
    PM="dnf"
    INSTALL="sudo dnf install -y"
else
    fail "No supported package manager found (brew, apt, dnf)"
    exit 1
fi

echo "Using package manager: $PM"
echo "================================="

# --- Core CLI tools ---
TOOLS=(
    bat         # cat replacement
    eza         # ls replacement
    ripgrep     # grep replacement (provides 'rg')
    fd          # find replacement
    fzf         # fuzzy finder
    zoxide      # cd replacement
    starship    # prompt
    lazygit     # git TUI
    git-delta   # diff viewer (provides 'delta')
    tree        # directory tree
)

# apt uses different package names for some tools
declare -A APT_NAMES=(
    [ripgrep]="ripgrep"
    [fd]="fd-find"
    [git-delta]="git-delta"
    [eza]="eza"
)

# Binary names to check (some differ from package names)
declare -A BIN_NAMES=(
    [ripgrep]="rg"
    [fd]="fd"
    [git-delta]="delta"
    [bat]="bat"
    [eza]="eza"
    [fzf]="fzf"
    [zoxide]="zoxide"
    [starship]="starship"
    [lazygit]="lazygit"
    [tree]="tree"
)

for tool in "${TOOLS[@]}"; do
    bin="${BIN_NAMES[$tool]:-$tool}"
    if command -v "$bin" >/dev/null 2>&1; then
        skip "$tool ($bin)"
    else
        pkg="$tool"
        if [[ "$PM" == "apt" ]] && [[ -v "APT_NAMES[$tool]" ]]; then
            pkg="${APT_NAMES[$tool]}"
        fi
        echo -n "Installing $tool... "
        if $INSTALL "$pkg" >/dev/null 2>&1; then
            ok "$tool"
        else
            fail "$tool — install manually"
        fi
    fi
done

# --- Nerd Font (for icons) ---
echo ""
echo "================================="
echo "Nerd Font Check"
echo "================================="
if [[ "$PM" == "brew" ]]; then
    if brew list --cask font-jetbrains-mono-nerd-font >/dev/null 2>&1; then
        skip "JetBrains Mono Nerd Font"
    else
        echo -n "Installing JetBrains Mono Nerd Font... "
        if brew install --cask font-jetbrains-mono-nerd-font >/dev/null 2>&1; then
            ok "JetBrains Mono Nerd Font"
            echo "  → Set this font in your terminal emulator settings"
        else
            fail "Font install failed — download from https://www.nerdfonts.com/"
        fi
    fi
else
    echo "  → Download a Nerd Font from https://www.nerdfonts.com/"
    echo "  → Set it in your terminal emulator settings"
fi

echo ""
echo "================================="
echo "Done! Next step: run configure-shell.sh"
echo "================================="
