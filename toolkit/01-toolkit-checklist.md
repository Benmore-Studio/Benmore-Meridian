# Development Toolkit Checklist

## Core Development Tools

- [ ] **ghostty** - GPU-accelerated terminal emulator
  ```bash
  brew install ghostty
  # or download from https://github.com/ghostty-org/ghostty
  ```

- [ ] **tree** - Directory structure visualization
  ```bash
  brew install tree
  # or: apt-get install tree (Linux)
  ```

- [ ] **uv** - Ultra-fast Python package manager & resolver
  ```bash
  brew install uv
  # or: pip install uv
  # or: curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- [ ] **ripgrep (rg)** - Fast recursive search tool
  ```bash
  brew install ripgrep
  # or: cargo install ripgrep
  # or: apt-get install ripgrep (Linux)
  ```

- [ ] **Rust** - Programming language & ecosystem
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  # Follow prompts to complete installation
  ```

## System Utilities

- [ ] **Rectangle** - Window management for macOS
  ```bash
  brew install rectangle
  # or download from https://rectangleapp.com
  ```

- [ ] **Raycast** - Productivity launcher & command palette
  ```bash
  brew install raycast
  # or download from https://www.raycast.com
  ```

## Version Control & Infrastructure

- [ ] **GitHub** - Version control & collaboration
  ```bash
  brew install gh  # GitHub CLI
  gh auth login    # Authenticate
  ```

## Deployment Platforms

- [ ] **Vercel** - Frontend deployment
  ```bash
  npm install -g vercel
  vercel login
  ```

- [ ] **Heroku** - App deployment & hosting
  ```bash
  brew install heroku
  heroku login
  ```

## External Services & APIs

- [ ] **Sentry** - Error tracking & monitoring
  - Setup: Create account at https://sentry.io
  - Install SDK in your projects (Python, Node.js, etc.)
  ```bash
  pip install sentry-sdk      # Python
  npm install @sentry/node    # Node.js
  ```

- [ ] **Cloudinary** - Image & media management
  - Setup: Create account at https://cloudinary.com
  - Store API credentials in `.env` file

- [ ] **Mailjet** - Email service
  - Setup: Create account at https://www.mailjet.com
  - Install SDK as needed
  ```bash
  pip install mailjet-rest    # Python
  npm install node-mailjet    # Node.js
  ```

- [ ] **Gemini** - Google's AI model integration
  ```bash
  pip install google-generativeai  # Python
  npm install @google/generative-ai # Node.js
  # Get API key from https://ai.google.dev
  ```

## Internal Tools

- [ ] **Portal** - Internal project management
  - Access: https://client.benmore.tech/client/project/e211de09-3ff5-4d57-8262-f8c25ec9f558/portal/
  - Credentials: Use company SSO/credentials

---

## Installation Verification

Run this to verify all tools are installed:

```bash
# Check each tool
ghostty --version
tree --version
uv --version
rg --version
rustc --version
rectangle  # Opens app
raycast    # Opens app
gh --version
vercel --version
heroku --version
```

## Quick Setup Script

Save as `setup-tools.sh`:

```bash
#!/bin/bash
echo "Installing development toolkit..."

# Core tools
brew install ghostty tree uv ripgrep rectangle raycast
brew tap homebrew/cask && brew install heroku

# Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# GitHub CLI
brew install gh
gh auth login

# Vercel
npm install -g vercel

echo "✓ Setup complete!"
```

Run with: `bash setup-tools.sh`
