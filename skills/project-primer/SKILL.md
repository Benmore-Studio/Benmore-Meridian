---
name: project-primer
description: >
  Creates a pre-kickoff project primer for a Benmore Technologies client engagement.
  Use when preparing to meet a new client for the first time — before the kickoff call.
  Triggered by phrases like "create a primer", "write a primer for project", "pre-kickoff
  primer", "client primer", or "prepare a primer for [client/project]".

  Gathers sales team notes, researches the client's industry and market (with cited sources),
  incorporates the user's complexity thoughts and value proposition hypotheses, writes a
  structured PRIMER.md in the project's Discovery directory, then generates a polished
  PRIMER_PRESENTATION.html using the embedded design system below.
---

# Project Primer

Produces two files before a client kickoff call:
1. `Active_Projects/[ProjectDir]/Discovery/PRIMER.md` — structured markdown document
2. `Active_Projects/[ProjectDir]/Discovery/PRIMER_PRESENTATION.html` — polished visual presentation

---

## Workflow

### Step 1 — Gather Inputs

Ask in a **single message** for anything not already provided:

- **Project directory** — e.g., `174-DrewLauten`
- **Sales team notes** — emails, call notes, Slack summaries, description of the client's idea
- **Supporting docs** — prototype links, decks, anything the client shared (optional)
- **Your complexity thoughts** — hypotheses on value props, pain points, open questions to hash out at kickoff

Do not ask for information already in the conversation. Do not ask questions one at a time.

### Step 2 — Identify Industry & Market

From the notes, extract:
- The **industry** (e.g., vacation rentals, fintech, legal tech, healthcare)
- The **specific market segment** (e.g., short-term rental operators, solo attorneys)
- **Adjacent markets** the product touches

### Step 3 — Research the Market

Use WebSearch to find **current, cited data**. Run at least 3–5 searches across:

| Area | What to find |
|---|---|
| Market size | Global + US value, year, CAGR, projected value + year |
| Trends | Key tailwinds driving the market right now |
| Pain points | Industry surveys, operator reports, documented frustrations |
| Competitors | Analogous platforms — name, founding year, focus, pricing |
| User motivations | Behavioural data on the target user |

Cite every statistic with an inline markdown link `([Source Name](url))`. Do not fabricate numbers. Prioritize: industry reports (Fortune Business Insights, Mordor Intelligence, Statista, IBISWorld), government data (BLS, Census), credible trade publications.

### Step 4 — Write PRIMER.md

Save to: `Active_Projects/[ProjectDir]/Discovery/PRIMER.md`

Follow this exact structure:

```
# [Product Name] — Pre-Kickoff Project Primer
**Prepared by:** Benmore Technologies
**Date:** [Today's date]
**Client:** [Client full name]
**Project Code:** BEN-[XXX]

---

## What We Understand You're Building
[2–4 paragraphs. Plain language. Explain the product, who it's for, and the core value
exchange. Describe the core loop as a numbered list of 3–5 steps. Write so the client
reads it and nods. No jargon. No bullets in the opening paragraphs.]

From [prototype / our conversation / the materials you shared], we can see the core loop clearly:

1. **[Actor 1]** [action + what they provide/get]
2. **[Actor 2]** [action + what they provide/get]
3. [Continue through full cycle]

---

## Industry & Market Context

### [Primary Market Name]
[Product] sits at the intersection of [N] markets, each with significant tailwinds.

**[Market 1]** [Stats with inline citations.] ([Source](url))
**[Market 2]** [Stats with inline citations.] ([Source](url))
**[Market 3]** [Stats with inline citations.] ([Source](url))

### [Secondary Theme — e.g. user motivations, operator pain point]
[2–3 paragraphs on user-side context with citations.]

### Existing [Alternatives / Competitors / Analogous Platforms]
[1–2 framing sentences.]

| Platform | Founded | Focus | Pricing |
|----------|---------|-------|---------|
| **[Name]** | [Year] | [Description] | [Price] |

**The key gap these platforms leave:** [What none of them do that this product would do.]
This is [Client Name]'s opportunity.

---

## What We Think the Core Value Propositions Are

### For [User Type 1]
- **[Benefit]** — [1-sentence explanation]
- **[Benefit]** — [1-sentence explanation]

### For [User Type 2]
- **[Benefit]** — [1-sentence explanation]
- **[Benefit]** — [1-sentence explanation]

---

## Open Questions We Want to Discuss With You

[Intro sentence about using the kickoff call to align before scoping.]

### Tier 1 — Core Functionality Decisions

**1. [Question title]**
[Context + options + why it matters for scope.]
- [Option A]
- [Option B]

[Continue for 4–6 Tier 1 questions drawn from the user's complexity thoughts.]

### Tier 2 — Complexity & Scope Decisions

**[N]. [Question title]**
[Same pattern. 2–4 questions.]

---

## Our Initial Read on Complexity

[1–2 sentences characterising the product type and core design challenge.]

[Bullet list of 4–6 design dimensions that will shape timeline and cost.]

None of these are blockers — they're design decisions. But they'll significantly shape timeline and cost.

---

## What We'd Like to Accomplish in Our Kickoff Call

1. [Goal]
2. [Goal]
3. [Goal]
4. [Goal]
5. [Goal]

---

## Next Steps from Benmore's Side

After our kickoff call, we'll produce:

- [ ] Technical Requirements Document
- [ ] MVP Features List (with clear in/out of scope line)
- [ ] User Flow Diagrams ([actor 1] journey + [actor 2] journey)
- [ ] Quote, Associated Fees & Timeline

[1–2 closing sentences on what's compelling about the opportunity.]

---

*Prepared by Benmore Technologies — [benmoretechnologies.com](https://benmoretechnologies.com)*
*Technical Lead: Aditya Niture*
```

Writing rules:
- Confident, clear, no jargon — written for the client, not internal use
- All stats cited inline
- Open questions drawn from the user's complexity thoughts (Step 1), not generic filler

### Step 5 — Generate HTML Presentation

After writing PRIMER.md, generate `PRIMER_PRESENTATION.html` in the same directory using the design system below. The HTML must be fully self-contained (no external dependencies except Google Fonts and CDN-hosted Mermaid/Chart.js).

---

## HTML Design System

Use this design system to turn the PRIMER.md into a polished one-pager.

### Visual Identity
Dark navy glassmorphism. Multi-tone navy gradient background, color-coded content cards, subtle glow accents. No emojis — use `→` and `•` only.

### Color Palette

| Element | Value |
|---|---|
| Background | `linear-gradient(135deg, #0a1628 0%, #1a2744 25%, #0f2d4a 50%, #1a3a5c 75%, #0d1a2d 100%)` |
| Primary text | `#ffffff` |
| Secondary text | `rgba(255,255,255,0.85)` |
| Muted text | `rgba(255,255,255,0.5)` |
| Accent blue | `#60a5fa` |
| Accent blue light | `#93c5fd` |
| Success green | `#34d399` |
| Warning amber | `#fbbf24` |
| Error red | `#f87171` |
| Special purple | `#a78bfa` |
| Card background | `linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)` |
| Card border | `rgba(255,255,255,0.08)` |

### Typography
- Font: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- H1: 2.75rem, 700, gradient text fill, letter-spacing -0.02em
- Section headers: 0.85rem, 600, uppercase, letter-spacing 0.1em, accent blue
- Card headers: 1.15rem, 600, color varies by card type
- Body: 1rem, 400, line-height 1.7

### Card Type Rules

Select card type automatically based on content:

| Card Class | Color | Use When |
|---|---|---|
| `.card` | Blue | General info, descriptions, default |
| `.feature-card` | Green | Features, benefits, capabilities, deliverables |
| `.warning-card` | Amber | Warnings, requirements, important notes |
| `.error-card` | Red | Risks, blockers, critical issues, what NOT to do |
| `.special-card` | Purple | Future features, AI, roadmap, advanced topics |
| `.highlight-card` | Blue accent + left border | Key takeaways, summaries, TL;DR |
| `.role-card` | Blue tinted + badge | People, roles, user types, personas |

### HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Document Title]</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({ startOnLoad: true, theme: 'dark', themeVariables: { primaryColor: '#1e3a5f', primaryTextColor: '#ffffff', primaryBorderColor: '#60a5fa', lineColor: '#60a5fa', secondaryColor: '#0f2744', background: '#0a1628', fontFamily: 'Inter, sans-serif', fontSize: '13px' } });
    </script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, sans-serif; background: linear-gradient(135deg, #0a1628 0%, #1a2744 25%, #0f2d4a 50%, #1a3a5c 75%, #0d1a2d 100%); background-attachment: fixed; min-height: 100vh; padding: 60px 30px; color: #ffffff; line-height: 1.7; }
        .container { max-width: 1200px; margin: 0 auto; }

        /* Header */
        .header { text-align: center; margin-bottom: 50px; padding-bottom: 40px; border-bottom: 1px solid rgba(255,255,255,0.1); position: relative; }
        .header::before { content: ''; position: absolute; top: -60px; left: 50%; transform: translateX(-50%); width: 400px; height: 400px; background: radial-gradient(circle, rgba(96,165,250,0.1) 0%, transparent 70%); pointer-events: none; }
        .project-badge { display: inline-block; padding: 5px 14px; background: linear-gradient(135deg, rgba(167,139,250,0.2), rgba(167,139,250,0.08)); border: 1px solid rgba(167,139,250,0.3); border-radius: 20px; font-size: 0.75rem; font-weight: 600; color: #a78bfa; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 20px; }
        h1 { font-size: 2.75rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 12px; background: linear-gradient(135deg, #ffffff 0%, #60a5fa 50%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .subtitle { font-size: 1rem; color: rgba(255,255,255,0.5); }
        .meta-row { display: flex; justify-content: center; gap: 24px; margin-top: 20px; flex-wrap: wrap; }
        .meta-item { font-size: 0.85rem; color: rgba(255,255,255,0.5); }
        .meta-item .label { color: rgba(255,255,255,0.3); text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.08em; margin-right: 6px; }
        .meta-item .value { color: rgba(255,255,255,0.75); font-weight: 500; }

        /* Sections */
        .section { margin-bottom: 40px; }
        .section-header { font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #60a5fa; margin-bottom: 20px; display: flex; align-items: center; gap: 12px; }
        .section-header::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, rgba(96,165,250,0.4) 0%, rgba(96,165,250,0.1) 50%, transparent 100%); }

        /* Grids */
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
        @media (max-width: 768px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } h1 { font-size: 2rem; } }

        /* Base Card */
        .card { background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 28px 32px; margin-bottom: 16px; backdrop-filter: blur(10px); position: relative; overflow: hidden; }
        .card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, rgba(96,165,250,0.3), transparent); }
        .card h3 { font-size: 1.15rem; font-weight: 600; color: #60a5fa; margin-bottom: 14px; }
        .card h4 { font-size: 1rem; font-weight: 500; color: #93c5fd; margin-bottom: 10px; margin-top: 16px; }
        .card p { color: rgba(255,255,255,0.85); margin-bottom: 12px; }
        .card p:last-child { margin-bottom: 0; }
        .card ul { padding-left: 18px; color: rgba(255,255,255,0.85); }
        .card ul li { margin-bottom: 8px; }

        /* Feature Card (Green) */
        .feature-card { background: linear-gradient(135deg, rgba(52,211,153,0.08), rgba(16,185,129,0.03)); border: 1px solid rgba(52,211,153,0.2); border-radius: 12px; padding: 24px 28px; margin-bottom: 16px; }
        .feature-card h3 { color: #34d399; font-size: 1.15rem; font-weight: 600; margin-bottom: 14px; }
        .feature-card p, .feature-card ul { color: rgba(255,255,255,0.85); }
        .feature-card ul { padding-left: 18px; }
        .feature-card ul li { margin-bottom: 8px; }

        /* Warning Card (Amber) */
        .warning-card { background: linear-gradient(135deg, rgba(251,191,36,0.08), rgba(245,158,11,0.03)); border: 1px solid rgba(251,191,36,0.2); border-radius: 12px; padding: 24px 28px; margin-bottom: 16px; }
        .warning-card h3 { color: #fbbf24; font-size: 1.15rem; font-weight: 600; margin-bottom: 14px; }
        .warning-card p, .warning-card ul { color: rgba(255,255,255,0.85); }
        .warning-card ul { padding-left: 18px; }
        .warning-card ul li { margin-bottom: 8px; }

        /* Error Card (Red) */
        .error-card { background: linear-gradient(135deg, rgba(239,68,68,0.08), rgba(220,38,38,0.03)); border: 1px solid rgba(239,68,68,0.2); border-radius: 12px; padding: 24px 28px; margin-bottom: 16px; }
        .error-card h3 { color: #f87171; font-size: 1.15rem; font-weight: 600; margin-bottom: 14px; }
        .error-card p, .error-card ul { color: rgba(255,255,255,0.85); }
        .error-card ul { padding-left: 18px; }
        .error-card ul li { margin-bottom: 8px; }

        /* Special Card (Purple) */
        .special-card { background: linear-gradient(135deg, rgba(167,139,250,0.1), rgba(139,92,246,0.05)); border: 1px solid rgba(167,139,250,0.25); border-radius: 12px; padding: 24px 28px; margin-bottom: 16px; }
        .special-card h3 { color: #a78bfa; font-size: 1.15rem; font-weight: 600; margin-bottom: 14px; }
        .special-card p, .special-card ul { color: rgba(255,255,255,0.85); }
        .special-card ul { padding-left: 18px; }
        .special-card ul li { margin-bottom: 8px; }

        /* Highlight Card */
        .highlight-card { background: linear-gradient(135deg, rgba(96,165,250,0.12), rgba(96,165,250,0.05)); border-left: 3px solid #60a5fa; border-radius: 0 12px 12px 0; padding: 24px 28px; margin-bottom: 16px; }
        .highlight-card h3 { color: #60a5fa; font-size: 1.15rem; font-weight: 600; margin-bottom: 14px; }
        .highlight-card p, .highlight-card ul { color: rgba(255,255,255,0.85); }
        .highlight-card ul { padding-left: 18px; }
        .highlight-card ul li { margin-bottom: 8px; }

        /* Role Card */
        .role-card { background: linear-gradient(135deg, rgba(96,165,250,0.08), rgba(30,58,95,0.3)); border: 1px solid rgba(96,165,250,0.2); border-radius: 12px; padding: 24px; margin-bottom: 16px; position: relative; }
        .role-card .role-badge { position: absolute; top: -10px; left: 20px; background: linear-gradient(135deg, #3b82f6, #1e40af); padding: 4px 14px; border-radius: 12px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
        .role-card h3 { margin-top: 8px; color: #93c5fd; font-size: 1.1rem; font-weight: 600; margin-bottom: 12px; }
        .role-card p, .role-card ul { color: rgba(255,255,255,0.85); }
        .role-card ul { padding-left: 18px; }
        .role-card ul li { margin-bottom: 6px; }

        /* Stat Boxes */
        .stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px; }
        @media (max-width: 768px) { .stat-row { grid-template-columns: 1fr; } }
        .stat-box { background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 20px 24px; text-align: center; position: relative; overflow: hidden; }
        .stat-box::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, rgba(96,165,250,0.4), transparent); }
        .stat-box .stat-value { font-size: 1.8rem; font-weight: 700; letter-spacing: -0.02em; background: linear-gradient(135deg, #ffffff, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .stat-box .stat-label { font-size: 0.8rem; color: rgba(255,255,255,0.5); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.06em; }
        .stat-box .stat-sub { font-size: 0.75rem; color: rgba(255,255,255,0.35); margin-top: 4px; }

        /* Table */
        table { width: 100%; border-collapse: collapse; margin-top: 4px; }
        th { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; color: rgba(255,255,255,0.4); padding: 10px 14px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.08); }
        td { padding: 12px 14px; font-size: 0.9rem; color: rgba(255,255,255,0.8); border-bottom: 1px solid rgba(255,255,255,0.05); vertical-align: top; }
        td strong { color: #ffffff; }
        tr:last-child td { border-bottom: none; }

        /* Diagram */
        .diagram-container { background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 28px; margin-bottom: 16px; overflow-x: auto; }

        /* Checklist */
        .checklist { list-style: none; padding: 0; }
        .checklist li { display: flex; align-items: flex-start; gap: 12px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); color: rgba(255,255,255,0.8); font-size: 0.95rem; }
        .checklist li:last-child { border-bottom: none; }
        .checklist li::before { content: '→'; color: #60a5fa; font-weight: 600; flex-shrink: 0; margin-top: 1px; }

        /* Footer */
        .footer { text-align: center; margin-top: 60px; padding-top: 30px; border-top: 1px solid rgba(255,255,255,0.07); }
        .footer p { font-size: 0.85rem; color: rgba(255,255,255,0.3); }
        .footer a { color: #60a5fa; text-decoration: none; }
    </style>
</head>
<body>
<div class="container">
    <!-- Build header, sections, and cards here based on PRIMER.md content -->
    <!-- Use .project-badge for BEN-XXX, h1 for product name, .subtitle for tagline -->
    <!-- Use .meta-row + .meta-item for Client / Date / Lead / Prepared by -->
    <!-- Use .stat-row + .stat-box for key market stats (3 per row) -->
    <!-- Use .diagram-container + mermaid block for the core loop if applicable -->
    <!-- Use table inside .card for competitor comparison -->
    <!-- Use .role-card for each user type value proposition -->
    <!-- Use .warning-card for complexity/trust issues -->
    <!-- Use .error-card for risks and critical decisions -->
    <!-- Use .special-card for future scope / phase 2 items -->
    <!-- Use .feature-card for deliverables and next steps -->
    <!-- Use .highlight-card for the opening "what we understand" summary -->
    <!-- Close with .footer -->
</div>
</body>
</html>
```

When generating the HTML, replace the comment block with real sections and populated cards drawn directly from the PRIMER.md content. Every section of the markdown maps to HTML sections and appropriately typed cards.

---

## Output

Confirm both files to the user when complete:

| File | Path |
|---|---|
| `PRIMER.md` | `Active_Projects/XXX-ClientName/Discovery/PRIMER.md` |
| `PRIMER_PRESENTATION.html` | `Active_Projects/XXX-ClientName/Discovery/PRIMER_PRESENTATION.html` |
