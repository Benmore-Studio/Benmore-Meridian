# Agent Teams in Claude Code

> **Author:** Rainer Nsa
> **Date:** 2026-02-21

---

## The Core Idea

Agent teams = dispatch multiple Task agents **in parallel** for independent problems. Claude coordinates them; each agent works in isolation with its own context window.

```
You (Orchestrator)
    │
    ├──► Agent 1 (Haiku)  — explore frontend
    ├──► Agent 2 (Haiku)  — explore backend       ← all at once
    └──► Agent 3 (Sonnet) — write plan
```

---

## 3 Agent Types to Know

| Agent | Best for | Speed | Cost |
|-------|----------|-------|------|
| **Haiku** | Exploration, file reading, searches | Fastest | Cheapest |
| **Sonnet** | Writing code, fixing bugs, analysis | Medium | Medium |
| **Opus** | Brainstorming, architecture, planning | Slowest | Most |

**Rule of thumb:** Haiku explores, Sonnet implements, Opus thinks.

---

## When to Use Parallel Agents

**Use them when tasks are independent:**
- Exploring frontend AND backend at the same time
- Writing multiple docs simultaneously
- Fixing bugs in unrelated files

**Don't use them when tasks share state:**
- Editing the same file
- One task depends on another's output
- Sequential steps (e.g. migrate DB → start server)

---

## Decision Tree

```
New task arrives
      │
      ▼
Independent from current work?
      │
   yes│              no
      ▼               ▼
 >30 seconds?    Do it inline
      │
   yes│              no
      ▼               ▼
 Background       Foreground
 Task()           Task()
```

---

## The Pattern

### Step 1 — Exploration (parallel Haiku agents)

```
Task("Explore frontend pages and routes", subagent_type="Explore")
Task("Explore backend API views",         subagent_type="Explore")
# Both run at the same time
```

### Step 2 — Planning (single focused agent)

```
# Read both results → write a coherent plan
# One agent, single output
```

### Step 3 — Execution (parallel if independent)

```
Task("Write docs/case-scenarios.md")
Task("Write docs/wiki-methodology.md")
# Both run at the same time
```

---

## Writing a Good Agent Prompt

The prompt quality determines the result. A vague prompt wastes the entire agent run.

**Always include:**
1. What the agent has access to (running services, relevant files)
2. One specific task — no ambiguity
3. What NOT to touch
4. Exactly what to return

**Example:**
```
The frontend (Next.js) and backend (Django) are currently running.
Explore the legal assistant at /path/to/project.

Return ASCII flows for:
1. All frontend page navigation paths + user decisions
2. All backend API endpoints + request/response shapes

Use Haiku sub-agents for speed. Do NOT modify any files.
```

**Common mistakes:**

| Wrong | Right |
|-------|-------|
| "Fix all the tests" | "Fix the 3 failures in auth.test.ts" |
| "Fix the race condition" | Paste the exact error messages |
| No constraints | "Do NOT change production code" |
| "Fix it" | "Return: root cause + what you changed" |

---

## Foreground vs Background

```python
# Foreground — block until done, then use the result
result = Task("Explore codebase", block=True)

# Background — fire and continue working
task_id = Task("Run slow analysis", run_in_background=True)
# ... do other work ...
TaskOutput(task_id)  # check when ready
```

**Use background when** the task takes >30 seconds and you have other work to do in parallel.

---

## Available Agent Types

| Type | Use for |
|------|---------|
| `Explore` | Finding files, reading code, mapping structure |
| `Plan` | Architecture decisions, trade-off analysis |
| `Bash` | Running commands, git operations |
| `general-purpose` | Complex multi-step research |
| `feature-dev:code-explorer` | Deep analysis of existing features |
| `feature-dev:code-architect` | Designing new feature architecture |

---

## Context Window Protection

The most underrated benefit of agent teams.

When a Haiku agent reads 50 files, that token cost stays **inside the sub-agent**. Your main conversation stays clean. The agent returns a summary, not raw file contents.

This matters especially when exploring large codebases — node_modules, virtual environments, and generated files would blow the main context if read directly. Dispatch a Haiku agent instead.

---

## Reviewing Agent Output

When agents return:

1. **Read each summary** — understand what changed or was found
2. **Check for conflicts** — did two agents touch the same file?
3. **Verify integration** — run tests or checks that cover all agents' work
4. **Spot systematic errors** — agents can make the same mistake repeatedly

---

## Real Example — Civicum Session (2026-02-20)

**Task:** Explore a full-stack legal app, generate ASCII flows, identify bugs, write 10 business scenarios.

**What was dispatched in parallel:**
- Haiku Explore agent → frontend page structure, routing, state management
- Haiku Explore agent → backend API endpoints, models, services

**Result:** Both returned in parallel. Main agent synthesised the outputs into:
- Frontend ASCII navigation flow
- Backend API sequence flow
- 10 documented business case scenarios
- 1 routing bug identified and fixed

**Time saved:** Two independent codebases explored simultaneously instead of sequentially.

---

## Related Docs

- [`development/03-claude-code-ecosystem.md`](./03-claude-code-ecosystem.md) — Claude Code overview
- [`development/06-business-scenarios-methodology.md`](./06-business-scenarios-methodology.md) — How agent teams were used for scenario generation
- [`development/agent-teams-guide.html`](./agent-teams-guide.html) — Visual walkthrough with diagrams
