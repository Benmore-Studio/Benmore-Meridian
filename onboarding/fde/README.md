# 🚀 Forward Deployed Engineer (FDE) Onboarding

Welcome to Benmore! This guide gets you fully set up as a Forward Deployed Engineer. Work through these steps in order — the `bm` CLI does most of the heavy lifting.

---

## 📚 Before You Start — Read These First

| Resource | Link | Time |
|----------|------|------|
| **FDE Principles** | [Developer Onboarding Presentation](../../Developer-Onboarding-Presentation.html) | 20 min |
| **FDE Book** | [Forward Deployed PDF](../../forward_deployed.pdf) | 1–2 hrs |
| **This Repo** | [Benmore-Meridian on GitHub](https://github.com/Benmore-Studio/Benmore-Meridian) | Explore as needed |

---

## 🛠️ Step 1 — Recommended Tools

Install these first, before running the CLI setup:

| Tool | Purpose | Install |
|------|---------|---------|
| **[Ghostty](https://ghostty.org/)** | Modern GPU-accelerated terminal | Download from ghostty.org |
| **[Raycast](https://www.raycast.com/)** | Spotlight replacement — fast launcher & snippets | Download from raycast.com |

---

## ⚙️ Step 2 — Run the bm CLI Setup

The `bm` CLI installs everything else automatically (tree, zoxide, lazygit, gh, and all Claude Code skills):

```bash
# Clone the repo
git clone https://github.com/Benmore-Studio/Benmore-Meridian.git
cd Benmore-Meridian

# Install bm (one-time)
pip install -e ./bm

# Run full setup — installs all skills, tools, and plugins
bm setup --yes
```

This single command installs:
- **Developer CLI tools:** `tree`, `zoxide`, `lazygit`, `gh`, `ripgrep`, `bat`, `eza`, `fzf`, `delta`
- **All Claude Code skills** — production Django, auth, security, mobile, CI/CD, and more
- **Plugins** — Superpowers and Double Shot Latte for Claude Code

Verify everything is working:

```bash
bm doctor        # full health check
bm              # dashboard showing skills, tools, plugins
```

---

## 🔍 Step 3 — Understand How We Work

### PR Review Process

Read how we do code review: [`review/01-pr-review-workflow.md`](../../review/01-pr-review-workflow.md)

### Training Videos

Watch the discovery process walkthrough:
[▶ Training Videos on Google Drive](https://drive.google.com/file/d/1_xkNGce9JNLlqY-SEWWlg6XHc3YKge8h/view?usp=drive_link)

These show how we run discovery sessions with clients.

---

## 📋 Onboarding Checklist

```
[ ] Read FDE Principles presentation
[ ] Read FDE Book (forward_deployed.pdf)
[ ] Install Ghostty terminal
[ ] Install Raycast
[ ] Clone Benmore-Meridian repo
[ ] Run: pip install -e ./bm
[ ] Run: bm setup --yes
[ ] Run: bm doctor (confirm no issues)
[ ] Read PR review workflow
[ ] Watch training videos
[ ] Schedule 1pm CT kickoff call with your lead
```

---

## 📁 Key Repo Areas

| Path | What's In It |
|------|-------------|
| [`toolkit/`](../../toolkit/) | Full development environment setup checklist |
| [`django/`](../../django/) | Django production readiness guides |
| [`development/`](../../development/) | End-to-end dev workflow, CI/CD, Claude Code ecosystem |
| [`review/`](../../review/) | PR review process |
| [`deployment/`](../../deployment/) | Heroku, DigitalOcean, CI/CD, mobile deployment |
| `skills/` | All Claude Code skills (installed via `bm`) |

---

## 💬 First Day

When you're all set up, ping your lead to schedule a **1pm CT kickoff call** — we'll walk through your first set of deliverables together.
