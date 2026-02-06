# Claude Code Ecosystem: MCP Tools, Plugins & Skills

## 📋 Overview

Claude Code's power comes from its ecosystem of extensions. This guide covers everything you need to set up and use:

| Layer | What It Is | Examples |
|-------|-----------|---------|
| **MCP Servers** | Background tools that give Claude access to external data/APIs | Context7, Hyperbrowser |
| **Plugins** | Curated behavior packages from marketplaces | Superpowers, Double Shot Latte, Code Review |
| **Skills** | Markdown-based instructions that teach Claude workflows | skills.sh skills, custom `.claude/skills/` |
| **Subagents** | Parallel worker agents Claude spawns for tasks | Task tool, Agent Teams |

---

## 1. MCP Servers (Model Context Protocol)

MCP servers run as background processes that give Claude access to external tools. They're configured in your `settings.json`.

### Context7 — Live Documentation Lookup

**What:** Fetches up-to-date, version-specific documentation and code examples for any library. When Claude needs to check the latest API for React, Django, Stripe, etc., Context7 pulls the real docs instead of relying on training data.

**Why:** Claude's training data has a knowledge cutoff. Context7 ensures you get *current* documentation, not outdated syntax or deprecated APIs.

**API Key:** Get a free key at [context7.com/dashboard](https://context7.com/dashboard)
- Keys follow the format: `ctx7sk_*`
- Free tier has rate limits; API key removes them

**Setup (add to `~/.claude/settings.json`):**

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

**With API key (recommended for higher rate limits):**

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest", "--api-key", "ctx7sk_YOUR_KEY"]
    }
  }
}
```

**Usage:** Add `use context7` to your prompt and Claude will automatically fetch relevant docs:
```
Build a Stripe checkout page. use context7
```

**Docs:** [github.com/upstash/context7](https://github.com/upstash/context7)

---

### Hyperbrowser — Cloud Browser Automation

**What:** Cloud-hosted browser automation for web scraping, crawling, structured data extraction, and browser-based agent tasks. Unlike Playwright (which runs locally), Hyperbrowser runs browsers in the cloud.

**Why:** Use for tasks that need browser automation without installing Chromium locally. Good for scraping, extracting structured data from web pages, and running browser agents at scale.

**API Key:** Get a key at [hyperbrowser.ai](https://www.hyperbrowser.ai/)
- Free tier available
- Current key format: `hb_*`

**Setup (add to `~/.claude/settings.json`):**

```json
{
  "mcpServers": {
    "hyperbrowser": {
      "command": "npx",
      "args": ["-y", "hyperbrowser-mcp"],
      "env": {
        "HYPERBROWSER_API_KEY": "hb_YOUR_KEY_HERE"
      }
    }
  }
}
```

**Available tools once connected:**
- `scrape_webpage` — Extract formatted content from any URL
- `crawl_webpages` — Navigate and crawl multiple pages
- `extract_structured_data` — Convert HTML to structured JSON
- `search_with_bing` — Web search from within Claude
- `browser_use_agent` — Full browser automation agent

**Docs:** [docs.hyperbrowser.ai/guides/model-context-protocol](https://docs.hyperbrowser.ai/guides/model-context-protocol)

---

### Agent Browser — Local Browser Automation

**What:** A local alternative to Hyperbrowser. Runs a headless Chromium browser on your machine for testing, form filling, screenshots, and data extraction.

**Why:** Use when you want browser automation without cloud dependencies, especially during development to test your own app.

**Setup:**
```bash
npm install -g agent-browser
agent-browser install           # Downloads Chromium
npx playwright install          # Alternative: install via Playwright
```

**No API key needed** — runs locally.

---

### Where MCP Config Lives

MCP servers are configured in **one of two places**:

| Scope | File | When to Use |
|-------|------|-------------|
| **Global** (all projects) | `~/.claude/settings.json` | Tools you want everywhere (Context7, Hyperbrowser) |
| **Project** (per-repo) | `.claude/settings.json` in repo root | Project-specific tools |

To view your current MCP config:
```bash
cat ~/.claude/settings.json | jq '.mcpServers'
```

---

## 2. Plugins & Marketplaces

Plugins are curated packages that add slash commands, modify Claude's behavior, and provide specialized capabilities.

### How Plugins Work

Plugins install from **marketplaces** — curated registries of plugins. There are two main marketplaces:

| Marketplace | Repository | What's In It |
|------------|-----------|-------------|
| **Official (Anthropic)** | `anthropics/claude-plugins-official` | Code review, commit commands, output styles |
| **Superpowers** | `obra/superpowers-marketplace` | TDD, brainstorming, plan writing, debugging |

### Installing Plugins

**From inside Claude Code**, run these commands:

#### Step 1: Add a marketplace

```
/plugin marketplace add anthropics/claude-plugins-official
/plugin marketplace add obra/superpowers-marketplace
```

#### Step 2: Browse available plugins

```
/plugin marketplace browse
```

#### Step 3: Install plugins

```
/plugin install superpowers@superpowers-marketplace
/plugin install code-review@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
/plugin install double-shot-latte@superpowers-marketplace
/plugin install explanatory-output-style@claude-plugins-official
```

#### Step 4: Manage installed plugins

```
/plugin                    # Opens plugin manager (Installed tab)
/plugin list               # List all installed plugins
/plugin enable <name>      # Enable a plugin
/plugin disable <name>     # Disable a plugin
/plugin uninstall <name>   # Remove a plugin
```

### Recommended Plugins

| Plugin | Marketplace | What It Does |
|--------|------------|-------------|
| **superpowers** | superpowers-marketplace | TDD, brainstorming, subagent development, plan writing, debugging |
| **code-review** | claude-plugins-official | `/code-review` slash command for PR reviews |
| **commit-commands** | claude-plugins-official | `/commit`, `/commit-push-pr` for git workflows |
| **double-shot-latte** | superpowers-marketplace | Auto-accepts tool calls, uses minimal tokens — keeps Claude running |
| **explanatory-output-style** | claude-plugins-official | Educational insights in Claude's responses |
| **code-simplifier** | claude-plugins-official | Simplifies and refines code for clarity |
| **ralph-wiggum** | claude-plugins-official | Fun personality plugin |

### What Plugins Look Like in settings.json

After installing, your `settings.json` will have an `enabledPlugins` section:

```json
{
  "enabledPlugins": {
    "superpowers@superpowers-marketplace": true,
    "code-review@claude-plugins-official": true,
    "commit-commands@claude-plugins-official": true,
    "double-shot-latte@superpowers-marketplace": true,
    "explanatory-output-style@claude-plugins-official": true,
    "code-simplifier@claude-plugins-official": true
  }
}
```

---

## 3. Skills

Skills are markdown-based instructions that teach Claude specialized workflows. They come from three sources:

### 3a. Skills.sh — Open Ecosystem

[skills.sh](https://skills.sh) is an open registry where developers publish skills for AI agents.

**Browse skills:**
- Go to [skills.sh](https://skills.sh) to search available skills
- Or use the `/find-skills` command in Claude Code

**Install a skill:**
```bash
npx skills add <skill-name>
# or
npx add-skill <repo-name>
```

This installs the skill into your `.claude/skills/` directory.

**Docs:** [skills.sh](https://skills.sh)

---

### 3b. Superpowers Skills (via Plugin)

When you install the Superpowers plugin, you get 20+ built-in skills accessible as slash commands:

| Skill | Command | What It Does |
|-------|---------|-------------|
| **Brainstorming** | `/superpowers:brainstorming` | Explores user intent, requirements, and design before implementation |
| **Write Plan** | `/superpowers:writing-plans` | Creates structured implementation plans from specs |
| **Execute Plan** | `/superpowers:executing-plans` | Executes plans in batches with review checkpoints |
| **TDD** | `/superpowers:test-driven-development` | Red/green test-driven development workflow |
| **Debugging** | `/superpowers:systematic-debugging` | Systematic root cause analysis |
| **Subagent Dev** | `/superpowers:subagent-driven-development` | Parallel task execution with subagents |
| **Code Review** | `/superpowers:requesting-code-review` | Requests thorough code review |
| **Git Worktrees** | `/superpowers:using-git-worktrees` | Isolated feature branches |
| **Finish Branch** | `/superpowers:finishing-a-development-branch` | Guides merge/PR/cleanup decisions |
| **Verify** | `/superpowers:verification-before-completion` | Evidence-based completion verification |
| **Dispatch Agents** | `/superpowers:dispatching-parallel-agents` | Parallel agent orchestration |

**Usage:** Just type the command in Claude Code:
```
/superpowers:brainstorming
```

---

### 3c. Custom Skills (Per-Project)

Create your own skills in your project's `.claude/skills/` directory:

```
.claude/skills/
├── debug/
│   └── SKILL.md
├── deploy/
│   └── SKILL.md
└── review/
    └── SKILL.md
```

Each `SKILL.md` is a markdown file with instructions Claude follows when the skill is invoked. See [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills) for the full spec.

---

## 4. Subagents & Agent Teams

### Subagents (Built-in)

Subagents are focused worker agents Claude spawns within a single session. They execute tasks and report results back.

**When to use:** Quick, focused tasks where only the result matters.

**Example prompt:**
```
Use 3 parallel task agents: one to fix type errors, one to fix import errors,
one to fix null checks. Report back when each completes.
```

### Agent Teams (Experimental)

Agent Teams are multiple Claude Code instances that work together, communicate with each other, and share a task list.

**When to use:** Complex work requiring discussion and collaboration between agents.

**Enable in `settings.json`:**
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

**Start a team:**
```
Create an agent team to review PR #142. Spawn three reviewers:
- One focused on security implications
- One checking performance impact
- One validating test coverage
Have them each review and report findings.
```

**Key controls:**
- **Shift+Up/Down** — Select teammates
- **Shift+Tab** — Toggle delegate mode (lead coordinates only, doesn't code)
- **Ctrl+T** — Toggle shared task list

**Best practices:**
- Give teammates enough context in spawn prompts (they don't inherit conversation history)
- Break work so each teammate owns different files (avoid conflicts)
- 5-6 tasks per teammate keeps everyone productive
- Always clean up teams via the lead when done

| Feature | Subagents | Agent Teams |
|---------|-----------|-------------|
| Context | Own window, results return to caller | Own window, fully independent |
| Communication | Report back to main only | Teammates message each other |
| Coordination | Main agent manages all | Shared task list, self-coordination |
| Token cost | Lower | Higher |
| Best for | Focused tasks | Complex collaborative work |

---

## 5. Complete Setup Checklist

### API Keys You Need

| Tool | Key Format | Where to Get |
|------|-----------|-------------|
| **Context7** | `ctx7sk_*` | [context7.com/dashboard](https://context7.com/dashboard) |
| **Hyperbrowser** | `hb_*` | [hyperbrowser.ai](https://www.hyperbrowser.ai/) |
| **Anthropic** | `sk-ant-*` | [console.anthropic.com](https://console.anthropic.com/) |

### MCP Servers
- [ ] Context7 added to `~/.claude/settings.json`
- [ ] Hyperbrowser added to `~/.claude/settings.json`
- [ ] Agent Browser installed globally (`npm install -g agent-browser`)

### Plugins
- [ ] Superpowers marketplace added (`/plugin marketplace add obra/superpowers-marketplace`)
- [ ] Official marketplace added (`/plugin marketplace add anthropics/claude-plugins-official`)
- [ ] Superpowers plugin installed
- [ ] Code Review plugin installed
- [ ] Commit Commands plugin installed
- [ ] Double Shot Latte plugin installed

### Skills
- [ ] Superpowers skills accessible (type `/superpowers:brainstorming` to verify)
- [ ] skills.sh available (`npx skills --help`)
- [ ] Custom skills directory exists if needed (`.claude/skills/`)

### Agent Teams
- [ ] `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` set to `"1"` in settings.json

### Verification Command

Run this inside Claude Code to verify your setup:
```
/plugin list
```
You should see all installed plugins listed with their enabled/disabled status.

---

## 🔗 Related Guides

- [CI/CD Bots Setup](./02-ci-cd-bots-setup.md) — Sentry, Vercel, GitHub Actions, Claude Bot
- [Developer Workflow](./00-developer-workflow.md) — End-to-end development process
- [PR Review Workflow](./01-pr-review-workflow.md) — How to review PRs with AI
- [Dev Toolkit](../toolkit/) — Development environment setup
