# Customization Reference

## FZF Themes

### Default (Green accent)
```bash
export FZF_DEFAULT_OPTS="--border --color 'pointer:#B3E1A7,bg+:-1,fg+:#B3E1A7'"
```

### Catppuccin Mocha
```bash
export FZF_DEFAULT_OPTS="--border --color 'bg+:#313244,spinner:#f5e0dc,hl:#f38ba8,fg:#cdd6f4,header:#f38ba8,info:#cba6f7,pointer:#f5e0dc,marker:#f5e0dc,fg+:#cdd6f4,prompt:#cba6f7,hl+:#f38ba8'"
```

### Tokyo Night
```bash
export FZF_DEFAULT_OPTS="--border --color 'fg:#c0caf5,bg:#1a1b26,hl:#bb9af7,fg+:#c0caf5,bg+:#292e42,hl+:#7dcfff,info:#7aa2f7,prompt:#7dcfff,pointer:#7dcfff,marker:#9ece6a,spinner:#9ece6a,header:#9ece6a'"
```

## Starship Prompt Presets

Apply a preset: `starship preset <name> -o ~/.config/starship.toml`

Available presets: `nerd-font-symbols`, `bracketed-segments`, `plain-text-symbols`, `no-nerd-font`, `pure-preset`, `tokyo-night`

## Git Delta Themes

Add to `~/.gitconfig`:
```ini
[delta]
    navigate = true
    side-by-side = true
    # Themes: "Dracula", "Monokai Extended", "Nord", "ansi"
    syntax-theme = Dracula
```

## Terminal Emulator Recommendations

| Terminal | Platform | Notable Features |
|----------|----------|-----------------|
| **Ghostty** | macOS/Linux | GPU-accelerated, native feel, fast |
| **WezTerm** | Cross-platform | Lua config, multiplexer built-in |
| **Alacritty** | Cross-platform | Minimal, GPU-accelerated |
| **iTerm2** | macOS | Feature-rich, tmux integration |
| **Kitty** | macOS/Linux | GPU-accelerated, image support |
