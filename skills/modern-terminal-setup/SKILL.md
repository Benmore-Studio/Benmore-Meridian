---
name: modern-terminal-setup
description: >
  Set up a modern, productive macOS/Linux terminal with curated CLI tools,
  fzf-powered keybindings, git history browsers, and a beautiful prompt.
  Use when the user asks to set up a terminal, install CLI tools, configure
  bash/zsh with modern replacements (bat, eza, ripgrep, fzf, zoxide, starship,
  lazygit, delta), or wants fzf-based keybindings for shell history and git.
  Also triggers on: "set up my terminal", "modern CLI tools", "better terminal",
  "fzf setup", "terminal productivity", "dev environment setup".
context: fork
---

# Modern Terminal Setup

Transform a stock macOS/Linux terminal into a fast, beautiful, productive dev environment.

## Prerequisites

- macOS with Homebrew, or Linux with a package manager
- Bash 4+ or Zsh (macOS ships bash 3.x — install newer via `brew install bash`)
- A Nerd Font installed in your terminal emulator (for icons in eza/starship)

## Tool Stack

| Tool | Replaces | Why |
|------|----------|-----|
| **bat** | cat | Syntax highlighting, line numbers, git integration |
| **eza** | ls | Icons, git status, tree view |
| **ripgrep** | grep | 15x faster, respects .gitignore |
| **fd** | find | 7x faster, intuitive syntax |
| **fzf** | Ctrl+R | Fuzzy finder for everything |
| **zoxide** | cd | Learns frequent dirs, `z foo` jumps there |
| **starship** | PS1 | Fast Rust prompt with git/lang context |
| **lazygit** | git CLI | TUI for staging, committing, rebasing |
| **delta** | diff | Side-by-side diffs with syntax highlighting |
| **tree** | ls -R | Directory tree visualization |

## Quick Start

Run the install script then the shell configurator:

```bash
bash scripts/install.sh        # Install all tools (idempotent)
bash scripts/configure-shell.sh  # Append config to ~/.bashrc or ~/.zshrc
exec bash                        # Reload shell
```

## Keybindings Reference

### Shell & Files
| Key | Action |
|-----|--------|
| **Ctrl+R** | Fuzzy shell history (replaces reverse-i-search) |
| **Ctrl+T** | Fuzzy file picker |
| **Alt+C** | Fuzzy cd into directory |
| **Alt+F** | File picker with bat preview |

### Git History Browsers
| Key | Action |
|-----|--------|
| **Ctrl+G** | Commit log with diff preview |
| **Ctrl+Alt+H** | File history — pick file, browse commits |
| **Ctrl+Alt+D** | Uncommitted changes browser |
| **Ctrl+Alt+B** | Branch switcher with log preview |

In-browser: Ctrl+D/U scroll, Ctrl+Y copy hash, Enter select.

## Aliases

```bash
cat → bat | ls → eza --icons | ll → eza -la --git | lt → eza --tree
lg → lazygit | gac → git add+commit | gsw → git switch | gp → git push
```

## Customization

- **FZF theme**: Set `FZF_DEFAULT_OPTS` — see `references/customization.md`
- **Starship prompt**: Edit `~/.config/starship.toml`
- **Git delta**: Add `[core] pager = delta` to `~/.gitconfig`

## Troubleshooting

- **Icons missing**: Install a Nerd Font and set it in terminal settings
- **Ctrl+R shows old reverse-i-search**: Source fzf keybindings AFTER history config
- **bash globstar error**: You're on bash 3.x, run `brew install bash`
