#!/bin/bash
# Modern Terminal Setup — Shell Configuration
# Appends modern aliases, fzf integration, and git history browsers to shell rc.
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Detect shell
SHELL_NAME=$(basename "$SHELL")
if [[ "$SHELL_NAME" == "zsh" ]]; then
    RC_FILE="$HOME/.zshrc"
elif [[ "$SHELL_NAME" == "bash" ]]; then
    RC_FILE="$HOME/.bashrc"
else
    echo "Unsupported shell: $SHELL_NAME (supports bash/zsh)"
    exit 1
fi

MARKER="# === MODERN TERMINAL SETUP ==="

# Check if already configured
if grep -q "$MARKER" "$RC_FILE" 2>/dev/null; then
    echo -e "${YELLOW}⏭${NC} Already configured in $RC_FILE"
    echo "  To re-apply, remove the block between '$MARKER' markers and re-run."
    exit 0
fi

# Backup
cp "$RC_FILE" "${RC_FILE}.backup.$(date +%Y%m%d%H%M%S)"
echo -e "${GREEN}✓${NC} Backed up $RC_FILE"

# Detect fzf path
FZF_DIR=""
if [[ -d /opt/homebrew/opt/fzf ]]; then
    FZF_DIR="/opt/homebrew/opt/fzf"
elif [[ -d /usr/local/opt/fzf ]]; then
    FZF_DIR="/usr/local/opt/fzf"
elif [[ -d "$HOME/.fzf" ]]; then
    FZF_DIR="$HOME/.fzf"
fi

# Determine bind command based on shell
if [[ "$SHELL_NAME" == "zsh" ]]; then
    BIND_SYNTAX="zsh"
else
    BIND_SYNTAX="bash"
fi

cat >> "$RC_FILE" << 'ENDCONFIG'

# === MODERN TERMINAL SETUP ===
# Installed by modern-terminal-setup skill

# --- Shell Options (bash only) ---
if [ -n "$BASH_VERSION" ]; then
    shopt -s histappend cmdhist checkwinsize cdspell
    if [ "${BASH_VERSINFO[0]:-3}" -ge 4 ]; then
        shopt -s globstar autocd
    fi
fi

# --- History ---
export HISTSIZE=50000
export HISTFILESIZE=100000
export HISTCONTROL=ignoredups:erasedups
export HISTIGNORE="ls:cd:pwd:exit:history:clear"
export HISTTIMEFORMAT="%F %T "

# --- Modern Aliases ---
alias cat='bat'
alias ls='eza --icons --group-directories-first'
alias ll='eza -la --icons --group-directories-first --git'
alias lt='eza --tree --icons -L 3 -I node_modules'
alias lg='lazygit'
alias preview="fzf --preview 'bat --color=always --style=numbers --line-range=:500 {}'"
alias rgf="rg --files | fzf --preview 'bat --color=always {}'"

# --- Git Aliases ---
alias gac='git add --all && git commit -m'
alias gsw='git switch'
alias gswc='git switch -c'
alias gp='git push'

# --- FZF ---
export FZF_DEFAULT_OPTS="--border --color 'pointer:#B3E1A7,bg+:-1,fg+:#B3E1A7'"
export FZF_CTRL_R_OPTS="
  --preview 'echo {}'
  --preview-window up:3:hidden:wrap
  --bind 'ctrl-/:toggle-preview'
  --bind 'ctrl-y:execute-silent(echo -n {2..} | pbcopy)+abort'
  --color header:italic
  --header 'Ctrl+Y copy | Ctrl+/ preview'"
ENDCONFIG

# Source fzf integration based on location
if [[ -n "$FZF_DIR" ]]; then
    if [[ "$SHELL_NAME" == "bash" ]]; then
        echo "[ -f \"$FZF_DIR/shell/key-bindings.bash\" ] && source \"$FZF_DIR/shell/key-bindings.bash\"" >> "$RC_FILE"
    else
        echo "[ -f \"$FZF_DIR/shell/key-bindings.zsh\" ] && source \"$FZF_DIR/shell/key-bindings.zsh\"" >> "$RC_FILE"
    fi
fi

cat >> "$RC_FILE" << 'ENDCONFIG'

# --- Starship Prompt ---
if command -v starship >/dev/null 2>&1; then
    eval "$(starship init ${0##*/})"
fi

# --- Zoxide ---
if command -v zoxide >/dev/null 2>&1; then
    eval "$(zoxide init ${0##*/})"
fi

# --- Git Pager Helper ---
_git_pager() {
    if command -v delta >/dev/null 2>&1; then
        delta
    elif command -v bat >/dev/null 2>&1; then
        bat --color=always --style=numbers --language=diff
    else
        cat
    fi
}

# --- Git Log Browser (Ctrl+G) ---
_fzf_git_log() {
    git rev-parse --git-dir > /dev/null 2>&1 || { echo "Not a git repo"; return 1; }
    local pager_cmd
    if command -v delta >/dev/null 2>&1; then pager_cmd="delta"
    elif command -v bat >/dev/null 2>&1; then pager_cmd="bat --color=always --style=numbers --language=diff"
    else pager_cmd="cat"; fi
    local commit
    commit=$(git log --color=always --format="%C(auto)%h%d %s %C(black)%C(bold)%cr" |
        fzf --ansi --no-sort --reverse --tiebreak=index \
            --preview="git show --color=always {1} | $pager_cmd" \
            --preview-window=right:60% \
            --bind="ctrl-d:preview-page-down,ctrl-u:preview-page-up" \
            --bind="ctrl-y:execute-silent(echo {1} | pbcopy)+abort" \
            --header="Enter=show | Ctrl+Y=copy hash | Ctrl+D/U=scroll")
    [ -n "$commit" ] && git show --color=always "$(echo "$commit" | awk '{print $1}')" | _git_pager
}

# --- File History Browser (Ctrl+Alt+H) ---
_fzf_git_file_history() {
    git rev-parse --git-dir > /dev/null 2>&1 || { echo "Not a git repo"; return 1; }
    local file
    file=$(git ls-files | fzf --preview 'bat --color=always {}' --preview-window=right:50%)
    [ -z "$file" ] && return 0
    local commit
    commit=$(git log --color=always --format="%C(auto)%h%d %s %C(black)%C(bold)%cr" -- "$file" |
        fzf --ansi --no-sort --reverse \
            --preview="git show --color=always {1}:$file | bat --color=always --style=numbers" \
            --preview-window=right:60% \
            --bind="ctrl-d:preview-page-down,ctrl-u:preview-page-up" \
            --header="History of: $file")
    [ -n "$commit" ] && git show --color=always "$(echo "$commit" | awk '{print $1}'):$file" | bat --color=always --style=numbers
}

# --- Git Diff Browser (Ctrl+Alt+D) ---
_fzf_git_diff() {
    git rev-parse --git-dir > /dev/null 2>&1 || { echo "Not a git repo"; return 1; }
    local pager_cmd
    if command -v delta >/dev/null 2>&1; then pager_cmd="delta"
    elif command -v bat >/dev/null 2>&1; then pager_cmd="bat --color=always --style=numbers --language=diff"
    else pager_cmd="cat"; fi
    local file
    file=$(git -c color.status=always status --short |
        fzf --ansi \
            --preview="f=\$(echo {} | awk '{print \$NF}'); git diff --cached --color=always \"\$f\" 2>/dev/null || git diff --color=always \"\$f\" | $pager_cmd" \
            --preview-window=right:60% \
            --header="Enter=show diff | Ctrl+D/U=scroll")
    if [ -n "$file" ]; then
        local fn=$(echo "$file" | awk '{print $NF}')
        git diff --cached --color=always "$fn" 2>/dev/null || git diff --color=always "$fn" | _git_pager
    fi
}

# --- Branch Switcher (Ctrl+Alt+B) ---
_fzf_git_branch() {
    git rev-parse --git-dir > /dev/null 2>&1 || { echo "Not a git repo"; return 1; }
    local branch
    branch=$(git branch --all --color=always | grep -v HEAD |
        fzf --ansi --preview='git log --color=always --oneline {1} | head -20' \
            --preview-window=right:60% --header="Enter=checkout")
    [ -n "$branch" ] && git checkout "$(echo "$branch" | sed 's/^[* ]*//' | sed 's#remotes/origin/##')"
}
ENDCONFIG

# Add keybindings based on shell type
if [[ "$SHELL_NAME" == "bash" ]]; then
    cat >> "$RC_FILE" << 'ENDCONFIG'

# --- Keybindings (bash) ---
bind -x '"\C-g": _fzf_git_log'
bind -x '"\e\C-h": _fzf_git_file_history'
bind -x '"\e\C-d": _fzf_git_diff'
bind -x '"\e\C-b": _fzf_git_branch'
ENDCONFIG
else
    cat >> "$RC_FILE" << 'ENDCONFIG'

# --- Keybindings (zsh) ---
zle -N _fzf_git_log
zle -N _fzf_git_file_history
zle -N _fzf_git_diff
zle -N _fzf_git_branch
bindkey '^G' _fzf_git_log
bindkey '\e^H' _fzf_git_file_history
bindkey '\e^D' _fzf_git_diff
bindkey '\e^B' _fzf_git_branch
ENDCONFIG
fi

echo "" >> "$RC_FILE"
echo "# === END MODERN TERMINAL SETUP ===" >> "$RC_FILE"

echo -e "${GREEN}✓${NC} Configuration appended to $RC_FILE"
echo ""
echo "Run 'exec $SHELL_NAME' to reload, or open a new terminal."
