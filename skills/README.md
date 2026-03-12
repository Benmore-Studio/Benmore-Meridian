# Claude Code Skills Collection

> Production-grade skills that extend Claude Code's capabilities for Django, Next.js, authentication, security, and developer tooling.

## What Are Skills?

**Skills are not npm packages.** They are specialized instruction sets that transform Claude Code from a general-purpose AI agent into a domain expert. Think of them as "onboarding manuals" that give Claude procedural knowledge, best practices, and ready-to-use templates for specific tasks.

When you install a skill, Claude automatically knows:
- **When to use it** (via trigger descriptions)
- **How to execute it** (via step-by-step instructions)
- **What resources are available** (scripts, templates, references)

Skills trigger automatically based on your task descriptions—no commands to memorize.

---

## Quick Install (Recommended)

```bash
# 1. Install bm CLI (once, from repo root)
pipx install ./bm

# 2. Install all skills as symlinks
bm install

# 3. Check plugin requirements (Superpowers, Double Shot Latte)
bm plugins

# 4. Full health check
bm doctor
```

Skills are symlinked from this repo into `~/.claude/skills/` — edits here instantly reflect in Claude Code.
Use `bm install --rsync` to force file copies instead.

---

## Installation (Manual)

### Prerequisites

Skills require **Claude Code** (Anthropic's official CLI).

**macOS/Linux:**
```bash
brew install claude
```

**Verify installation:**
```bash
claude --version
```

### Method 1: Clone and Copy (Recommended)

```bash
# Clone this repository
git clone https://github.com/yourusername/claude-guides.git /tmp/claude-guides

# Copy all skills to Claude's directory
cp -r /tmp/claude-guides/skills/* ~/.claude/skills/

# Verify installation
ls ~/.claude/skills/
```

### Method 2: Manual Installation (Individual Skills)

For installing a single skill:

1. **Navigate to Claude's skills directory:**
   ```bash
   cd ~/.claude/skills
   ```

2. **Create a folder for the skill:**
   ```bash
   mkdir skill-name
   ```

3. **Copy the SKILL.md file:**
   - Download or copy the `SKILL.md` from this repository
   - Place it in `~/.claude/skills/skill-name/SKILL.md`

4. **Verify:**
   ```bash
   ls ~/.claude/skills/skill-name/
   # Should show: SKILL.md and any supporting files
   ```

### Method 3: Using Code Editor

1. **Open Claude's skills directory:**
   ```bash
   cd ~/.claude
   code .  # For VS Code
   # or
   cursor .  # For Cursor
   ```

2. **Create skill folder:**
   - In the `.claude/skills/` directory, create a new folder with your skill name
   - Example: `skills/django-production/`

3. **Add SKILL.md:**
   - Copy the `SKILL.md` file from this repository into the folder
   - Add any supporting files (scripts, templates, etc.)

4. **Save and verify:**
   - Close the editor
   - Run: `claude` and verify the skill is available

---

## Available Skills

### 🚀 Production & Deployment

#### django-production
Production-ready Django setup with modern tooling (uv, ruff, pytest, Docker, drf-spectacular).

**Use when:**
- Auditing Django codebases for production readiness
- Implementing production best practices
- Setting up new Django projects with proper tooling

**Triggers:** "productionize Django", "audit Django", "Django production setup"

---

#### frontend-productionize
Next.js + Django integration with OpenAPI TypeScript codegen for type-safe API integration.

**Use when:**
- Starting development on Next.js + Django projects
- Before staging/production deployment
- Setting up CI/CD for Next.js
- Type-safe API integration needed

**Triggers:** "productionize Next.js", "Next.js production", "setup CI/CD"

---

### 🔒 Security & Authentication

#### dependency-security-audit
Comprehensive dependency security auditing and automated fixing for npm, pnpm, yarn, pip, poetry projects.

**Use when:**
- Security audits needed
- Checking for CVEs
- Fixing Dependabot issues
- Before production deployment

**Triggers:** "audit security", "check vulnerabilities", "scan dependencies"

---

#### django-auth-react-native
Complete Django authentication system for React Native with JWT, email verification, and OTP.

**Use when:**
- Building Django + React Native projects with authentication
- Implementing JWT-based authentication
- Adding email verification and OTP functionality
- Multi-device session management

**Triggers:** "Django React Native auth", "JWT authentication", "mobile app auth"

---

### 🛠️ Developer Tools

#### modern-terminal-setup
Set up modern macOS/Linux terminal with curated CLI tools, fzf-powered keybindings, and beautiful prompt.

**Use when:**
- Setting up a new development environment
- Installing modern CLI tools
- Configuring bash/zsh with modern replacements

**Tools included:** bat, eza, ripgrep, fzf, zoxide, starship, lazygit, delta

**Triggers:** "setup terminal", "modern CLI tools", "terminal productivity"

---

#### skill-creator
Guide for creating effective Claude Code skills.

**Use when:**
- Creating new skills
- Updating existing skills
- Learning skill development best practices

**Triggers:** "create skill", "skill development", "write skill"

---

### 📝 Utilities

#### gh_issue
GitHub issue management and automation.

#### nano_banana
Image generation using Gemini 2.5 Flash Image model.

#### stripe_processing
Stripe payment processing with email notifications.

#### presentation_maker
Create presentations programmatically.

---

## Verification

After installation, verify skills are loaded:

```bash
# Start Claude Code
claude

# In Claude Code session, type:
# "What skills do you have available?"
```

Claude will list all available skills and their trigger conditions.

---

## Skill Structure

Each skill follows this structure:

```
skill-name/
├── SKILL.md           # Main skill instruction file (required)
├── templates/         # Optional: code templates
├── scripts/          # Optional: automation scripts
└── examples/         # Optional: usage examples
```

---

## Customizing Skills

Skills are plain markdown files with embedded instructions. To customize:

1. Open the skill file in your editor
2. Modify triggers, instructions, or templates
3. Save and restart Claude Code
4. The updated skill takes effect immediately

---

## Contributing

Have a skill to share? Consider:

1. Following the skill structure above
2. Including clear triggers and use cases
3. Adding examples and templates
4. Testing thoroughly before sharing

---

## Troubleshooting

**Skill not triggering:**
- Check the skill file is named `SKILL.md`
- Verify folder location is `~/.claude/skills/skill-name/`
- Restart Claude Code
- Try explicitly mentioning the skill name

**Permission issues:**
```bash
chmod -R 755 ~/.claude/skills
```

**Skills directory doesn't exist:**
```bash
mkdir -p ~/.claude/skills
```

---

## License

Skills are provided as-is for educational and development purposes.

---

**Happy coding! 🚀**
