# Claude Skills Organization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Copy and organize all custom Claude skills from `~/.claude/skills` to `/Users/arkashjain/Desktop/guides/skills` with proper documentation and installation instructions.

**Architecture:** This plan systematically copies actual skill directories (excluding symlinks to managed skills), removes any git artifacts, creates proper folder structure, and adds comprehensive documentation including CLAUDE.md updates and installation README.

**Tech Stack:** Bash, Git, Markdown

---

## Task 1: Identify and Catalog Custom Skills

**Files:**
- Create: `/Users/arkashjain/Desktop/guides/docs/skill-inventory.txt`

**Step 1: List all actual skill directories (exclude symlinks)**

Run:
```bash
cd ~/.claude/skills && find . -maxdepth 1 -type d ! -name "." | sed 's|^\./||' > /tmp/skill-dirs.txt
cat /tmp/skill-dirs.txt
```

Expected output: List of directory names (not symlinks)

**Step 2: Create inventory file**

Run:
```bash
cat /tmp/skill-dirs.txt > /Users/arkashjain/Desktop/guides/docs/skill-inventory.txt
echo "Total custom skills: $(wc -l < /tmp/skill-dirs.txt)"
```

Expected: Confirmation of count

---

## Task 2: Copy django-production Skill

**Files:**
- Create: `/Users/arkashjain/Desktop/guides/skills/django-production/`
- Copy: `~/.claude/skills/django-production/` → `/Users/arkashjain/Desktop/guides/skills/django-production/`

**Step 1: Create target directory**

Run:
```bash
mkdir -p /Users/arkashjain/Desktop/guides/skills/django-production
```

**Step 2: Copy skill files**

Run:
```bash
cp -r ~/.claude/skills/django-production/* /Users/arkashjain/Desktop/guides/skills/django-production/
```

**Step 3: Remove git artifacts**

Run:
```bash
find /Users/arkashjain/Desktop/guides/skills/django-production -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
find /Users/arkashjain/Desktop/guides/skills/django-production -name ".gitignore" -type f -delete 2>/dev/null || true
```

**Step 4: Verify skill structure**

Run:
```bash
ls -la /Users/arkashjain/Desktop/guides/skills/django-production/
```

Expected: SKILL.md and any supporting files, no .git directory

---

## Task 3: Copy frontend-productionize Skill

**Files:**
- Create: `/Users/arkashjain/Desktop/guides/skills/frontend-productionize/`

**Step 1: Create target directory and copy**

Run:
```bash
mkdir -p /Users/arkashjain/Desktop/guides/skills/frontend-productionize
cp -r ~/.claude/skills/frontend-productionize/* /Users/arkashjain/Desktop/guides/skills/frontend-productionize/
```

**Step 2: Remove git artifacts**

Run:
```bash
find /Users/arkashjain/Desktop/guides/skills/frontend-productionize -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
find /Users/arkashjain/Desktop/guides/skills/frontend-productionize -name ".gitignore" -type f -delete 2>/dev/null || true
```

**Step 3: Verify**

Run:
```bash
ls -la /Users/arkashjain/Desktop/guides/skills/frontend-productionize/
```

---

## Task 4: Copy dependency-security-audit Skill

**Files:**
- Create: `/Users/arkashjain/Desktop/guides/skills/dependency-security-audit/`

**Step 1: Create and copy**

Run:
```bash
mkdir -p /Users/arkashjain/Desktop/guides/skills/dependency-security-audit
cp -r ~/.claude/skills/dependency-security-audit/* /Users/arkashjain/Desktop/guides/skills/dependency-security-audit/
```

**Step 2: Clean git artifacts**

Run:
```bash
find /Users/arkashjain/Desktop/guides/skills/dependency-security-audit -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
find /Users/arkashjain/Desktop/guides/skills/dependency-security-audit -name ".gitignore" -type f -delete 2>/dev/null || true
```

---

## Task 5: Copy django-auth-react-native Skill

**Files:**
- Create: `/Users/arkashjain/Desktop/guides/skills/django-auth-react-native/`

**Step 1: Create and copy**

Run:
```bash
mkdir -p /Users/arkashjain/Desktop/guides/skills/django-auth-react-native
cp -r ~/.claude/skills/django-auth-react-native/* /Users/arkashjain/Desktop/guides/skills/django-auth-react-native/
```

**Step 2: Clean git artifacts**

Run:
```bash
find /Users/arkashjain/Desktop/guides/skills/django-auth-react-native -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
find /Users/arkashjain/Desktop/guides/skills/django-auth-react-native -name ".gitignore" -type f -delete 2>/dev/null || true
```

---

## Task 6: Copy modern-terminal-setup Skill

**Files:**
- Create: `/Users/arkashjain/Desktop/guides/skills/modern-terminal-setup/`

**Step 1: Create and copy**

Run:
```bash
mkdir -p /Users/arkashjain/Desktop/guides/skills/modern-terminal-setup
cp -r ~/.claude/skills/modern-terminal-setup/* /Users/arkashjain/Desktop/guides/skills/modern-terminal-setup/
```

**Step 2: Clean git artifacts**

Run:
```bash
find /Users/arkashjain/Desktop/guides/skills/modern-terminal-setup -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
find /Users/arkashjain/Desktop/guides/skills/modern-terminal-setup -name ".gitignore" -type f -delete 2>/dev/null || true
```

---

## Task 7: Copy skill-creator Skill

**Files:**
- Create: `/Users/arkashjain/Desktop/guides/skills/skill-creator/`

**Step 1: Create and copy**

Run:
```bash
mkdir -p /Users/arkashjain/Desktop/guides/skills/skill-creator
cp -r ~/.claude/skills/skill-creator/* /Users/arkashjain/Desktop/guides/skills/skill-creator/
```

**Step 2: Clean git artifacts**

Run:
```bash
find /Users/arkashjain/Desktop/guides/skills/skill-creator -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
find /Users/arkashjain/Desktop/guides/skills/skill-creator -name ".gitignore" -type f -delete 2>/dev/null || true
```

---

## Task 8: Copy Additional Custom Skills

**Files:**
- Create directories for: `gh_issue`, `nano_banana`, `stripe_processing`, `presentation_maker`

**Step 1: Batch copy remaining skills**

Run:
```bash
for skill in gh_issue nano_banana stripe_processing presentation_maker; do
  if [ -d ~/.claude/skills/$skill ]; then
    mkdir -p /Users/arkashjain/Desktop/guides/skills/$skill
    cp -r ~/.claude/skills/$skill/* /Users/arkashjain/Desktop/guides/skills/$skill/
    find /Users/arkashjain/Desktop/guides/skills/$skill -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
    find /Users/arkashjain/Desktop/guides/skills/$skill -name ".gitignore" -type f -delete 2>/dev/null || true
    echo "Copied: $skill"
  fi
done
```

Expected: Confirmation messages for each copied skill

---

## Task 9: Create Skills README

**Files:**
- Create: `/Users/arkashjain/Desktop/guides/skills/README.md`

**Step 1: Write comprehensive skills README**

Create file with:
```markdown
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

## Installation

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
```

---

## Task 10: Update Main README

**Files:**
- Modify: `/Users/arkashjain/Desktop/guides/README.md`

**Step 1: Add skills section to main README**

Add after the "Guide Categories" section:

```markdown
### 6. **Claude Code Skills** 🤖
Production-grade skills that extend Claude Code's capabilities with domain expertise.

**Skills included:**
- django-production - Django production best practices
- frontend-productionize - Next.js + Django integration
- dependency-security-audit - Security scanning and CVE fixes
- django-auth-react-native - Mobile app authentication
- modern-terminal-setup - Developer environment setup
- skill-creator - Create your own skills

**Installation:** `cp -r skills/* ~/.claude/skills/`

**Location:** `skills/README.md`
```

**Step 2: Verify README updates**

Run:
```bash
grep -A 5 "Claude Code Skills" /Users/arkashjain/Desktop/guides/README.md
```

Expected: New section visible

---

## Task 11: Update CLAUDE.md

**Files:**
- Modify: `/Users/arkashjain/Desktop/guides/CLAUDE.md`

**Step 1: Add skills documentation to CLAUDE.md**

Add new section:

```markdown
## Claude Code Skills

This repository includes production-grade skills for Claude Code.

### Skill Directory Structure

```
skills/
├── README.md (installation and usage guide)
├── django-production/
├── frontend-productionize/
├── dependency-security-audit/
├── django-auth-react-native/
├── modern-terminal-setup/
├── skill-creator/
└── [other skills]/
```

### Installation

Copy skills to Claude Code's skills directory:

```bash
cp -r skills/* ~/.claude/skills/
```

### Available Skills

See `skills/README.md` for complete documentation on:
- Production deployment skills
- Security and authentication
- Developer tools and utilities
- Skill development

### Creating Custom Skills

Use the skill-creator skill to learn how to create your own skills:

```bash
# In Claude Code
"I want to create a new skill for [task]"
```

Refer to skill-creator/SKILL.md for detailed guidelines.
```

**Step 2: Verify CLAUDE.md updates**

Run:
```bash
grep -A 3 "Claude Code Skills" /Users/arkashjain/Desktop/guides/CLAUDE.md
```

---

## Task 12: Create Skill Inventory Document

**Files:**
- Create: `/Users/arkashjain/Desktop/guides/skills/SKILLS_INVENTORY.md`

**Step 1: Generate inventory**

```bash
cat > /Users/arkashjain/Desktop/guides/skills/SKILLS_INVENTORY.md << 'EOF'
# Skills Inventory

## Custom Skills Included

| Skill Name | Description | Status | Last Updated |
|------------|-------------|--------|--------------|
| django-production | Django production best practices | ✅ Active | 2026-02-09 |
| frontend-productionize | Next.js + Django integration | ✅ Active | 2026-02-09 |
| dependency-security-audit | Security scanning | ✅ Active | 2026-02-09 |
| django-auth-react-native | Mobile app auth | ✅ Active | 2026-02-09 |
| modern-terminal-setup | Terminal setup | ✅ Active | 2026-02-09 |
| skill-creator | Skill development | ✅ Active | 2026-02-09 |
| gh_issue | GitHub issue automation | ✅ Active | 2026-02-09 |
| nano_banana | Image generation | ✅ Active | 2026-02-09 |
| stripe_processing | Stripe payments | ✅ Active | 2026-02-09 |
| presentation_maker | Presentation creation | ✅ Active | 2026-02-09 |

## Managed Skills (Symlinks - Not Included)

These are installed via Claude Code marketplace and managed separately:
- agent-browser
- expo-deployment
- find-skills
- github-pr-review-workflow
- pdf
- qa-test-planner
- remotion-best-practices
- stripe-integration
- ui-ux-pro-max
- vercel-react-best-practices
- web-design-guidelines

## Installation Notes

Custom skills are copied to this repository. Managed skills should be installed via:

```bash
# Claude Code marketplace (when available)
claude skill install <skill-name>
```

Or as symlinks from the agent marketplace directory.
EOF
```

**Step 2: Verify**

Run:
```bash
cat /Users/arkashjain/Desktop/guides/skills/SKILLS_INVENTORY.md | head -20
```

---

## Task 13: Verify All Skills Copied

**Files:**
- None (verification only)

**Step 1: Count skills**

Run:
```bash
echo "Skills copied:"
ls -1 /Users/arkashjain/Desktop/guides/skills/ | grep -v "README\|SKILLS_INVENTORY" | wc -l

echo -e "\nSkill directories:"
ls -1 /Users/arkashjain/Desktop/guides/skills/ | grep -v "README\|SKILLS_INVENTORY"
```

Expected: List of 10 skill directories

**Step 2: Verify no git artifacts remain**

Run:
```bash
echo "Checking for .git directories..."
find /Users/arkashjain/Desktop/guides/skills -name ".git" -type d

echo "Checking for .gitignore files..."
find /Users/arkashjain/Desktop/guides/skills -name ".gitignore" -type f
```

Expected: No output (no git artifacts found)

**Step 3: Verify each skill has SKILL.md**

Run:
```bash
for skill in /Users/arkashjain/Desktop/guides/skills/*/; do
  skill_name=$(basename "$skill")
  if [ "$skill_name" = "README.md" ] || [ "$skill_name" = "SKILLS_INVENTORY.md" ]; then
    continue
  fi
  if [ -f "$skill/SKILL.md" ]; then
    echo "✅ $skill_name has SKILL.md"
  else
    echo "❌ $skill_name missing SKILL.md"
  fi
done
```

Expected: All skills have SKILL.md

---

## Task 14: Commit Skills to Git

**Files:**
- All files in `/Users/arkashjain/Desktop/guides/`

**Step 1: Check git status**

Run:
```bash
cd /Users/arkashjain/Desktop/guides
git status
```

**Step 2: Add all skills**

Run:
```bash
cd /Users/arkashjain/Desktop/guides
git add skills/
git add README.md
git add CLAUDE.md
git add docs/plans/
```

**Step 3: Commit**

Run:
```bash
cd /Users/arkashjain/Desktop/guides
git commit -m "$(cat <<'EOF'
feat: add Claude Code skills collection

- Copy 10 custom skills from ~/.claude/skills
- Remove all git artifacts from copied skills
- Add comprehensive skills README with installation guide
- Update main README with skills section
- Update CLAUDE.md with skills documentation
- Add SKILLS_INVENTORY.md for tracking
- Skills included:
  * django-production
  * frontend-productionize
  * dependency-security-audit
  * django-auth-react-native
  * modern-terminal-setup
  * skill-creator
  * gh_issue, nano_banana, stripe_processing, presentation_maker

Installation: cp -r skills/* ~/.claude/skills/

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

Expected: Commit created successfully

**Step 4: Verify commit**

Run:
```bash
git log -1 --stat
```

Expected: Shows commit with all added files

---

## Task 15: Push to Remote

**Files:**
- None (git operation)

**Step 1: Push to remote**

Run:
```bash
cd /Users/arkashjain/Desktop/guides
git push origin main
```

Expected: All changes pushed successfully

**Step 2: Verify push**

Run:
```bash
cd /Users/arkashjain/Desktop/guides
git log -1
git status
```

Expected: "Your branch is up to date with 'origin/main'"

---

## Summary

**Completed actions:**
1. ✅ Identified all custom skills (10 total)
2. ✅ Copied each skill to guides/skills/
3. ✅ Removed all git artifacts (.git, .gitignore)
4. ✅ Created comprehensive skills README
5. ✅ Updated main README with skills section
6. ✅ Updated CLAUDE.md with skills documentation
7. ✅ Created SKILLS_INVENTORY.md
8. ✅ Verified all skills have SKILL.md
9. ✅ Committed all changes
10. ✅ Pushed to remote

**Installation command for users:**
```bash
git clone https://github.com/yourusername/claude-guides.git
cp -r claude-guides/skills/* ~/.claude/skills/
```

**Skills are now:**
- ✅ Organized in `/Users/arkashjain/Desktop/guides/skills/`
- ✅ Clean (no git artifacts)
- ✅ Documented (README, CLAUDE.md, inventory)
- ✅ Ready for distribution
- ✅ Version controlled
- ✅ Pushed to remote
