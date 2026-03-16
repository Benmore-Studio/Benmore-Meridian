---
name: presentation-maker
description: Enhanced Presentation Formatter Skill
context: fork
---

# Enhanced Presentation Formatter Skill

## Purpose

Instantly transform raw inputs (meeting notes, research, summaries, specs, briefs, any markdown document) into polished, professional HTML presentations with rich visual hierarchy and color-coded content types. No questions asked - just format and deliver.

## When to Use

User provides unstructured content or markdown document and wants it formatted for sharing, documentation, or presentation with enhanced visual appeal.

## Design System

### Visual Identity

Premium, immersive aesthetic with multi-tone navy gradients, glassmorphism effects, color-coded content cards, and subtle glow accents.

### Color Palette

| Element             | Value                                                                                      |
| ------------------- | ------------------------------------------------------------------------------------------ |
| Background gradient | `linear-gradient(135deg, #0a1628 0%, #1a2744 25%, #0f2d4a 50%, #1a3a5c 75%, #0d1a2d 100%)` |
| Primary text        | `#ffffff`                                                                                  |
| Secondary text      | `rgba(255, 255, 255, 0.85)`                                                                |
| Muted text          | `rgba(255, 255, 255, 0.5)`                                                                 |
| Accent blue         | `#60a5fa`                                                                                  |
| Accent blue light   | `#93c5fd`                                                                                  |
| Success green       | `#34d399`                                                                                  |
| Warning amber       | `#fbbf24`                                                                                  |
| Error red           | `#f87171`                                                                                  |
| Special purple      | `#a78bfa`                                                                                  |
| Card background     | `linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%)`    |
| Card border         | `rgba(255, 255, 255, 0.08)`                                                                |

### Typography

- **Font:** `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- **Title:** 2.75rem, 700 weight, gradient text fill, tight letter-spacing (-0.02em)
- **Section headers:** 0.85rem, 600 weight, uppercase, letter-spacing (0.1em), accent color
- **Card headers:** 1.15rem, 600 weight, color varies by card type
- **Subheaders:** 1rem, 500 weight, light blue (#93c5fd)
- **Body:** 1rem, 400 weight, 1.7 line-height

### Design Principles

- Rounded corners (12px border-radius)
- Gradient backgrounds on cards
- Backdrop blur for glassmorphism effect
- Top gradient line on cards for depth
- Radial glow effects on header and dividers
- Color-coded cards based on content type
- Status/priority badges with gradient backgrounds
- No emojis - use minimal symbols only (`→`, `•`)

---

## Card Type Selection Rules

**Automatically select card type based on content:**

| Card Type                       | Use When Content Contains                                                             |
| ------------------------------- | ------------------------------------------------------------------------------------- |
| `.card` (Blue)                  | General information, descriptions, explanations, default for most content             |
| `.feature-card` (Green)         | Features, capabilities, benefits, strengths, positives, what's included, deliverables |
| `.warning-card` (Amber)         | Warnings, cautions, important notes, compliance, security, restrictions, limitations  |
| `.error-card` (Red)             | Errors, critical issues, blockers, risks, what NOT to do, failures                    |
| `.special-card` (Purple)        | Future features, AI-related, advanced topics, "coming soon", roadmap items            |
| `.highlight-card` (Blue accent) | Key takeaways, summaries, executive summaries, conclusions, TL;DR                     |
| `.role-card` (With badge)       | People, roles, personas, team members, user types                                     |

**Keyword triggers for card selection:**

- **Green (feature-card):** "feature", "capability", "benefit", "advantage", "strength", "include", "deliver", "provide", "offer", "support"
- **Amber (warning-card):** "warning", "caution", "important", "note", "compliance", "security", "restrict", "limit", "require", "must"
- **Red (error-card):** "error", "critical", "risk", "block", "fail", "don't", "never", "avoid", "issue", "problem"
- **Purple (special-card):** "future", "coming soon", "roadmap", "AI", "planned", "phase 2", "later", "advanced", "vision"
- **Role card:** "role", "user", "persona", "team", "member", "admin", "manager", "owner"

---

## Diagram Guidelines

### Mermaid.js Theme Configuration

Always use dark theme with this configuration:

```javascript
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'primaryColor': '#1e3a5f',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#60a5fa',
    'lineColor': '#60a5fa',
    'secondaryColor': '#0f2744',
    'tertiaryColor': '#162d50',
    'background': '#0a1628',
    'mainBkg': '#1e3a5f',
    'secondBkg': '#0f2744',
    'border1': '#3b82f6',
    'border2': '#1e40af',
    'arrowheadColor': '#60a5fa',
    'fontFamily': 'Inter, sans-serif',
    'fontSize': '14px',
    'textColor': '#ffffff',
    'nodeTextColor': '#ffffff'
  }
}}%%
```

#### Mermaid Color Palette (use these only)

| Purpose          | Color     | Use For                      |
| ---------------- | --------- | ---------------------------- |
| Primary nodes    | `#1e3a5f` | Main elements, key steps     |
| Secondary nodes  | `#0f2744` | Supporting elements          |
| Tertiary nodes   | `#162d50` | Groupings, subprocesses      |
| Accent/highlight | `#3b82f6` | Important nodes, decisions   |
| Success states   | `#059669` | Completed, approved, success |
| Warning states   | `#d97706` | Caution, pending             |
| Error states     | `#dc2626` | Errors, blocked              |
| Borders/lines    | `#60a5fa` | All connections              |
| Text             | `#ffffff` | All labels                   |

### Chart.js Configuration

Always use dark theme configuration:

```javascript
const darkTheme = {
  backgroundColor: "transparent",
  scales: {
    x: {
      grid: {
        color: "rgba(255, 255, 255, 0.08)",
        borderColor: "rgba(255, 255, 255, 0.15)",
      },
      ticks: { color: "rgba(255, 255, 255, 0.7)", font: { family: "Inter" } },
    },
    y: {
      grid: {
        color: "rgba(255, 255, 255, 0.08)",
        borderColor: "rgba(255, 255, 255, 0.15)",
      },
      ticks: { color: "rgba(255, 255, 255, 0.7)", font: { family: "Inter" } },
    },
  },
  plugins: {
    legend: {
      labels: {
        color: "rgba(255, 255, 255, 0.85)",
        font: { family: "Inter", size: 12 },
      },
    },
    tooltip: {
      backgroundColor: "#1e3a5f",
      titleColor: "#ffffff",
      bodyColor: "rgba(255, 255, 255, 0.85)",
      borderColor: "#60a5fa",
      borderWidth: 1,
    },
  },
};
```

#### Chart.js Color Palette

```javascript
const chartColors = {
  primary: ["#60a5fa", "#3b82f6", "#1e40af", "#1e3a5f"],
  extended: ["#60a5fa", "#34d399", "#a78bfa", "#fbbf24", "#f87171"],
  backgrounds: [
    "rgba(96, 165, 250, 0.2)",
    "rgba(52, 211, 153, 0.2)",
    "rgba(167, 139, 250, 0.2)",
    "rgba(251, 191, 36, 0.2)",
  ],
  borders: ["#60a5fa", "#34d399", "#a78bfa", "#fbbf24"],
};
```

---

## HTML Template

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
        mermaid.initialize({
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {
                primaryColor: '#1e3a5f',
                primaryTextColor: '#ffffff',
                primaryBorderColor: '#60a5fa',
                lineColor: '#60a5fa',
                secondaryColor: '#0f2744',
                tertiaryColor: '#162d50',
                background: '#0a1628',
                fontFamily: 'Inter, sans-serif',
                fontSize: '13px'
            }
        });
    </script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0a1628 0%, #1a2744 25%, #0f2d4a 50%, #1a3a5c 75%, #0d1a2d 100%);
            background-attachment: fixed;
            min-height: 100vh;
            padding: 60px 30px;
            color: #ffffff;
            line-height: 1.7;
        }

        .container { max-width: 1200px; margin: 0 auto; }

        /* Header with Glow */
        .header {
            text-align: center;
            margin-bottom: 50px;
            padding-bottom: 40px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            position: relative;
        }

        .header::before {
            content: '';
            position: absolute;
            top: -60px;
            left: 50%;
            transform: translateX(-50%);
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(96, 165, 250, 0.1) 0%, transparent 70%);
            pointer-events: none;
        }

        .logo { margin-bottom: 24px; }
        .logo img { width: 60px; height: 60px; opacity: 0.9; }

        h1 {
            font-size: 2.75rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 12px;
            background: linear-gradient(135deg, #ffffff 0%, #60a5fa 50%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.5);
            font-weight: 400;
            letter-spacing: 0.02em;
        }

        .version-badge {
            display: inline-block;
            padding: 6px 16px;
            background: linear-gradient(135deg, rgba(96, 165, 250, 0.2) 0%, rgba(96, 165, 250, 0.1) 100%);
            border: 1px solid rgba(96, 165, 250, 0.3);
            border-radius: 20px;
            font-size: 0.85rem;
            color: #60a5fa;
            margin-top: 16px;
        }

        /* Sections */
        .section { margin-bottom: 40px; }

        .section-header {
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #60a5fa;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .section-header::after {
            content: '';
            flex: 1;
            height: 1px;
            background: linear-gradient(90deg, rgba(96, 165, 250, 0.4) 0%, rgba(96, 165, 250, 0.1) 50%, transparent 100%);
        }

        /* Base Card (Blue) */
        .card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 28px 32px;
            margin-bottom: 16px;
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, rgba(96, 165, 250, 0.3) 50%, transparent 100%);
        }

        .card h3 { font-size: 1.15rem; font-weight: 600; color: #60a5fa; margin-bottom: 14px; }
        .card h4 { font-size: 1rem; font-weight: 500; color: #93c5fd; margin-bottom: 10px; margin-top: 16px; }
        .card h4:first-of-type { margin-top: 0; }
        .card p { color: rgba(255, 255, 255, 0.85); margin-bottom: 12px; }
        .card p:last-child { margin-bottom: 0; }

        /* Feature Card (Green) - for features, benefits, positives */
        .feature-card {
            background: linear-gradient(135deg, rgba(52, 211, 153, 0.08) 0%, rgba(16, 185, 129, 0.03) 100%);
            border: 1px solid rgba(52, 211, 153, 0.2);
            border-radius: 12px;
            padding: 24px 28px;
            margin-bottom: 16px;
        }
        .feature-card h3 { color: #34d399; font-size: 1.15rem; font-weight: 600; margin-bottom: 14px; }

        /* Warning Card (Amber) - for warnings, cautions, important notes */
        .warning-card {
            background: linear-gradient(135deg, rgba(251, 191, 36, 0.08) 0%, rgba(245, 158, 11, 0.03) 100%);
            border: 1px solid rgba(251, 191, 36, 0.2);
            border-radius: 12px;
            padding: 24px 28px;
            margin-bottom: 16px;
        }
        .warning-card h3 { color: #fbbf24; font-size: 1.15rem; font-weight: 600; margin-bottom: 14px; }

        /* Error Card (Red) - for errors, risks, critical issues */
        .error-card {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(220, 38, 38, 0.03) 100%);
            border: 1px solid rgba(239, 68, 68, 0.2);
            border-radius: 12px;
            padding: 24px 28px;
            margin-bottom: 16px;
        }
        .error-card h3 { color: #f87171; font-size: 1.15rem; font-weight: 600; margin-bottom: 14px; }

        /* Special Card (Purple) - for future, AI, advanced topics */
        .special-card {
            background: linear-gradient(135deg, rgba(167, 139, 250, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
            border: 1px solid rgba(167, 139, 250, 0.25);
            border-radius: 12px;
            padding: 24px 28px;
            margin-bottom: 16px;
        }
        .special-card h3 { color: #a78bfa; font-size: 1.15rem; font-weight: 600; margin-bottom: 14px; }

        /* Role Card with Badge - for people, roles, personas */
        .role-card {
            background: linear-gradient(135deg, rgba(96, 165, 250, 0.08) 0%, rgba(30, 58, 95, 0.3) 100%);
            border: 1px solid rgba(96, 165, 250, 0.2);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 16px;
            position: relative;
        }

        .role-card .role-badge {
            position: absolute;
            top: -10px;
            left: 20px;
            background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
            padding: 4px 14px;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .role-card h3 { margin-top: 8px; }

        /* Highlight Card - for key takeaways, summaries */
        .highlight-card {
            background: linear-gradient(135deg, rgba(96, 165, 250, 0.12) 0%, rgba(96, 165, 250, 0.05) 100%);
            border-left: 3px solid #60a5fa;
            border-radius: 0 12px 12px 0;
            padding: 24px 28px;
            margin-bottom:
```
