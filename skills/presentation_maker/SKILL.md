---
name: presentation_maker
description: Enhanced Presentation Formatter Skill
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
| Element | Value |
|---------|-------|
| Background gradient | `linear-gradient(135deg, #0a1628 0%, #1a2744 25%, #0f2d4a 50%, #1a3a5c 75%, #0d1a2d 100%)` |
| Primary text | `#ffffff` |
| Secondary text | `rgba(255, 255, 255, 0.85)` |
| Muted text | `rgba(255, 255, 255, 0.5)` |
| Accent blue | `#60a5fa` |
| Accent blue light | `#93c5fd` |
| Success green | `#34d399` |
| Warning amber | `#fbbf24` |
| Error red | `#f87171` |
| Special purple | `#a78bfa` |
| Card background | `linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%)` |
| Card border | `rgba(255, 255, 255, 0.08)` |

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

| Card Type | Use When Content Contains |
|-----------|---------------------------|
| `.card` (Blue) | General information, descriptions, explanations, default for most content |
| `.feature-card` (Green) | Features, capabilities, benefits, strengths, positives, what's included, deliverables |
| `.warning-card` (Amber) | Warnings, cautions, important notes, compliance, security, restrictions, limitations |
| `.error-card` (Red) | Errors, critical issues, blockers, risks, what NOT to do, failures |
| `.special-card` (Purple) | Future features, AI-related, advanced topics, "coming soon", roadmap items |
| `.highlight-card` (Blue accent) | Key takeaways, summaries, executive summaries, conclusions, TL;DR |
| `.role-card` (With badge) | People, roles, personas, team members, user types |

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
| Purpose | Color | Use For |
|---------|-------|---------|
| Primary nodes | `#1e3a5f` | Main elements, key steps |
| Secondary nodes | `#0f2744` | Supporting elements |
| Tertiary nodes | `#162d50` | Groupings, subprocesses |
| Accent/highlight | `#3b82f6` | Important nodes, decisions |
| Success states | `#059669` | Completed, approved, success |
| Warning states | `#d97706` | Caution, pending |
| Error states | `#dc2626` | Errors, blocked |
| Borders/lines | `#60a5fa` | All connections |
| Text | `#ffffff` | All labels |

### Chart.js Configuration

Always use dark theme configuration:

```javascript
const darkTheme = {
  backgroundColor: 'transparent',
  scales: {
    x: {
      grid: { color: 'rgba(255, 255, 255, 0.08)', borderColor: 'rgba(255, 255, 255, 0.15)' },
      ticks: { color: 'rgba(255, 255, 255, 0.7)', font: { family: 'Inter' } }
    },
    y: {
      grid: { color: 'rgba(255, 255, 255, 0.08)', borderColor: 'rgba(255, 255, 255, 0.15)' },
      ticks: { color: 'rgba(255, 255, 255, 0.7)', font: { family: 'Inter' } }
    }
  },
  plugins: {
    legend: { labels: { color: 'rgba(255, 255, 255, 0.85)', font: { family: 'Inter', size: 12 } } },
    tooltip: { backgroundColor: '#1e3a5f', titleColor: '#ffffff', bodyColor: 'rgba(255, 255, 255, 0.85)', borderColor: '#60a5fa', borderWidth: 1 }
  }
};
```

#### Chart.js Color Palette
```javascript
const chartColors = {
  primary: ['#60a5fa', '#3b82f6', '#1e40af', '#1e3a5f'],
  extended: ['#60a5fa', '#34d399', '#a78bfa', '#fbbf24', '#f87171'],
  backgrounds: ['rgba(96, 165, 250, 0.2)', 'rgba(52, 211, 153, 0.2)', 'rgba(167, 139, 250, 0.2)', 'rgba(251, 191, 36, 0.2)'],
  borders: ['#60a5fa', '#34d399', '#a78bfa', '#fbbf24']
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
            margin-bottom: 30px;
        }

        .highlight-card .label {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #60a5fa;
            margin-bottom: 12px;
        }

        /* Alert Card (Red left border) - for critical warnings */
        .alert-card {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(220, 38, 38, 0.03) 100%);
            border-left: 3px solid #ef4444;
            border-radius: 0 12px 12px 0;
            padding: 20px 24px;
            margin-bottom: 16px;
        }

        .alert-card .label {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #ef4444;
            margin-bottom: 10px;
        }

        /* Lists */
        ul { list-style: none; padding: 0; }
        li { padding: 8px 0; padding-left: 22px; position: relative; color: rgba(255, 255, 255, 0.85); }
        li::before { content: "→"; position: absolute; left: 0; color: #60a5fa; font-size: 0.9rem; }

        /* Grids */
        .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
        .grid-3 { grid-template-columns: repeat(3, 1fr); }
        .grid-4 { grid-template-columns: repeat(4, 1fr); }

        /* Stat Card with Bottom Accent */
        .stat-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .stat-card::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #60a5fa 0%, #3b82f6 50%, #1e40af 100%);
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #60a5fa 0%, #93c5fd 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 6px;
        }

        .stat-label {
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.5);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Flow Steps - for processes, workflows, steps */
        .flow-step {
            display: flex;
            align-items: flex-start;
            gap: 16px;
            padding: 16px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .flow-step:last-child { border-bottom: none; }

        .flow-number {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
            font-weight: 700;
            flex-shrink: 0;
        }

        .flow-content h4 { font-size: 1rem; font-weight: 500; color: #ffffff; margin-bottom: 6px; }
        .flow-content p { font-size: 0.95rem; color: rgba(255, 255, 255, 0.65); margin: 0; }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .badge-p0 { background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.1) 100%); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
        .badge-p1 { background: linear-gradient(135deg, rgba(251, 191, 36, 0.2) 0%, rgba(245, 158, 11, 0.1) 100%); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
        .badge-p2 { background: linear-gradient(135deg, rgba(96, 165, 250, 0.2) 0%, rgba(59, 130, 246, 0.1) 100%); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.3); }
        .badge-p3 { background: linear-gradient(135deg, rgba(167, 139, 250, 0.2) 0%, rgba(139, 92, 246, 0.1) 100%); color: #a78bfa; border: 1px solid rgba(167, 139, 250, 0.3); }
        .badge-success { background: linear-gradient(135deg, rgba(52, 211, 153, 0.2) 0%, rgba(16, 185, 129, 0.1) 100%); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }
        .badge-warning { background: linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.2); }
        .badge-error { background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.05) 100%); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.2); }

        /* Data Table */
        .data-table { width: 100%; border-collapse: collapse; }
        .data-table th, .data-table td { padding: 14px 16px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, 0.06); }
        .data-table th { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #60a5fa; background: rgba(96, 165, 250, 0.05); }
        .data-table td { color: rgba(255, 255, 255, 0.85); font-size: 0.95rem; }
        .data-table tr:hover td { background: rgba(96, 165, 250, 0.03); }

        /* Technical Requirements Box */
        .tech-req {
            background: rgba(96, 165, 250, 0.05);
            border: 1px solid rgba(96, 165, 250, 0.15);
            border-radius: 8px;
            padding: 16px 20px;
            margin-top: 16px;
        }

        .tech-req h5 { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #60a5fa; margin-bottom: 10px; }
        .tech-req ul { margin: 0; }
        .tech-req li { padding: 4px 0; padding-left: 22px; font-size: 0.9rem; }

        /* Divider with Glow */
        .divider {
            height: 2px;
            background: linear-gradient(90deg, transparent 0%, rgba(96, 165, 250, 0.3) 20%, rgba(96, 165, 250, 0.3) 80%, transparent 100%);
            margin: 50px 0;
            position: relative;
        }

        .divider::before {
            content: '';
            position: absolute;
            top: -20px;
            left: 50%;
            transform: translateX(-50%);
            width: 200px;
            height: 40px;
            background: radial-gradient(ellipse, rgba(96, 165, 250, 0.15) 0%, transparent 70%);
        }

        /* Diagram Container */
        .diagram-container {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 24px;
            margin: 20px 0;
            overflow-x: auto;
        }

        .diagram-container pre { color: rgba(255, 255, 255, 0.7); font-family: 'Fira Code', 'Monaco', monospace; font-size: 0.85rem; line-height: 1.6; white-space: pre; margin: 0; }

        /* Quote */
        .quote { border-left: 2px solid #60a5fa; padding-left: 24px; margin: 20px 0; font-style: italic; color: rgba(255, 255, 255, 0.8); }
        .quote cite { display: block; margin-top: 8px; font-style: normal; font-size: 0.9rem; color: rgba(255, 255, 255, 0.5); }

        /* Action Items */
        .action-item { display: flex; align-items: flex-start; gap: 12px; padding: 14px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.06); }
        .action-item:last-child { border-bottom: none; }
        .action-number { background: linear-gradient(135deg, rgba(96, 165, 250, 0.2) 0%, rgba(59, 130, 246, 0.1) 100%); color: #60a5fa; padding: 4px 12px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; white-space: nowrap; }
        .action-owner { background: rgba(96, 165, 250, 0.15); color: #60a5fa; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 500; white-space: nowrap; }
        .action-text { flex: 1; color: rgba(255, 255, 255, 0.85); }
        .action-text strong { color: #ffffff; }

        /* Timeline */
        .timeline-item { display: flex; gap: 20px; padding: 16px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.06); }
        .timeline-item:last-child { border-bottom: none; }
        .timeline-marker { width: 32px; height: 32px; background: rgba(96, 165, 250, 0.15); border: 1px solid rgba(96, 165, 250, 0.3); border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 600; color: #60a5fa; flex-shrink: 0; }
        .timeline-content h3 { font-size: 1rem; font-weight: 500; color: #ffffff; margin-bottom: 4px; }
        .timeline-content p { font-size: 0.95rem; color: rgba(255, 255, 255, 0.6); margin: 0; }

        /* Complexity Colors */
        .complexity-low { color: #34d399; }
        .complexity-medium { color: #fbbf24; }
        .complexity-high { color: #f87171; }

        /* Responsive */
        @media (max-width: 768px) {
            body { padding: 40px 20px; }
            h1 { font-size: 2rem; }
            .grid, .grid-3, .grid-4 { grid-template-columns: 1fr; }
            .card { padding: 20px; }
        }

        /* Print */
        @media print {
            body { background: white; color: #1a1a1a; padding: 20px; }
            .card, .highlight-card, .role-card, .feature-card, .warning-card, .special-card, .error-card, .alert-card { background: #f8f9fa; border-color: #dee2e6; }
            h1 { background: none; -webkit-text-fill-color: #1a1a1a; color: #1a1a1a; }
            .section-header, .card h3, .stat-value { color: #1a4480; -webkit-text-fill-color: #1a4480; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <img src="https://benmore.tech/static/images/og_image.png" alt="Benmore">
            </div>
            <h1>[Document Title]</h1>
            <p class="subtitle">[Subtitle or Context]</p>
            <!-- Include version-badge only if relevant -->
        </div>

        <!-- Key Takeaways (always include) -->
        <div class="highlight-card">
            <div class="label">Key Takeaways</div>
            <ul>
                <li>First major point</li>
                <li>Second major point</li>
            </ul>
        </div>

        <!-- Content Sections -->
        <div class="section">
            <div class="section-header">Section Title</div>
            <div class="card">
                <h3>Card Title</h3>
                <p>Content goes here...</p>
            </div>
        </div>
    </div>
</body>
</html>
```

---

## Section Components

### Key Takeaways (always include if applicable)
```html
<div class="highlight-card">
    <div class="label">Key Takeaways</div>
    <ul>
        <li>Point one</li>
        <li>Point two</li>
    </ul>
</div>
```

### Standard Card (Blue)
```html
<div class="card">
    <h3>Card Title</h3>
    <p>Content here...</p>
</div>
```

### Feature Card (Green)
```html
<div class="feature-card">
    <h3>Feature Name</h3>
    <p>Description...</p>
</div>
```

### Warning Card (Amber)
```html
<div class="warning-card">
    <h3>Important Note</h3>
    <p>Description...</p>
</div>
```

### Error Card (Red)
```html
<div class="error-card">
    <h3>Risk / Issue</h3>
    <p>Description...</p>
</div>
```

### Special Card (Purple)
```html
<div class="special-card">
    <h3>Future Feature</h3>
    <p>Description...</p>
</div>
```

### Role Card with Badge
```html
<div class="role-card">
    <span class="role-badge">Role Type</span>
    <h3>Role Name</h3>
    <p>Description...</p>
</div>
```

### Alert Card (Red left border)
```html
<div class="alert-card">
    <div class="label">Critical</div>
    <p>Critical information...</p>
</div>
```

### Stats Row
```html
<div class="grid grid-4">
    <div class="stat-card">
        <div class="stat-value">47</div>
        <div class="stat-label">Metric</div>
    </div>
</div>
```

### Flow Steps
```html
<div class="flow-step">
    <div class="flow-number">1</div>
    <div class="flow-content">
        <h4>Step Title</h4>
        <p>Step description</p>
    </div>
</div>
```

### Technical Requirements Box
```html
<div class="tech-req">
    <h5>Technical Requirements</h5>
    <ul>
        <li>Requirement one</li>
        <li>Requirement two</li>
    </ul>
</div>
```

### Data Table
```html
<table class="data-table">
    <thead><tr><th>Column 1</th><th>Column 2</th></tr></thead>
    <tbody><tr><td>Data</td><td>Data</td></tr></tbody>
</table>
```

### Timeline
```html
<div class="timeline-item">
    <div class="timeline-marker">1</div>
    <div class="timeline-content">
        <h3>Phase Name</h3>
        <p>Description</p>
    </div>
</div>
```

### Action Items
```html
<div class="action-item">
    <span class="action-owner">@Owner</span>
    <span class="action-text">Task description</span>
</div>
```

### Quote
```html
<div class="quote">
    "Important statement..."
    <cite>- Person Name</cite>
</div>
```

### Badges
```html
<span class="badge badge-p0">P0</span>
<span class="badge badge-p1">P1</span>
<span class="badge badge-p2">P2</span>
<span class="badge badge-success">Success</span>
<span class="badge badge-warning">Warning</span>
<span class="badge badge-error">Error</span>
```

### Grids
```html
<div class="grid">...</div>       <!-- 2 columns -->
<div class="grid grid-3">...</div>  <!-- 3 columns -->
<div class="grid grid-4">...</div>  <!-- 4 columns -->
```

---

## Workflow

1. **Receive raw content** (markdown, notes, any document)
2. **Auto-analyze:**
   - Identify document type (meeting, research, spec, summary, etc.)
   - Extract key points, decisions, conclusions for Key Takeaways
   - Identify numeric data for stat cards
   - Find action items, owners, deadlines
   - Locate quotes or notable statements
   - Detect tables, lists, hierarchical content
3. **Auto-structure:**
   - Title from main topic or # heading
   - Subtitle from date, version, or context
   - Key Takeaways from conclusions/decisions
   - Group related content into sections
   - **Auto-select card types based on content keywords**
4. **Generate HTML** using appropriate components
5. **Add diagrams** if data warrants visualization (use dark theme)
6. **Output** clean, immersive presentation

---

## Content Transformation Rules

### Meeting Notes
- **Title:** "[Topic] - Meeting Summary"
- **Key Takeaways:** Decisions made, action items summary
- **Sections:** Discussion topics grouped
- **Components:** Action items with owners, timeline for next steps, quotes for notable statements
- **Card types:** Use warning-card for blockers, feature-card for agreements

### Research/Analysis
- **Title:** "[Subject] Analysis"
- **Key Takeaways:** Main findings, recommendations
- **Sections:** Findings by category
- **Components:** Stats row for metrics, tables for comparisons, charts for trends
- **Card types:** Use feature-card for opportunities, warning-card for risks, error-card for threats

### Project Summaries
- **Title:** "[Project Name] Overview"
- **Key Takeaways:** Current status, key milestones
- **Sections:** By workstream, phase, or team
- **Components:** Timeline for milestones, stats for progress, role-cards for team
- **Card types:** Use feature-card for completed items, warning-card for at-risk items

### Technical Specs / Documentation
- **Title:** "[Feature/System] Specification"
- **Key Takeaways:** Core requirements, scope
- **Sections:** Components, integrations, requirements
- **Components:** Flow steps for processes, tech-req boxes, tables for schemas/endpoints
- **Card types:** Use feature-card for features, warning-card for constraints, special-card for future work

### Product/Feature Lists
- **Title:** "[Product] Features"
- **Key Takeaways:** Core value proposition
- **Sections:** By feature category or user type
- **Components:** Role-cards for user types, feature-cards for capabilities
- **Card types:** Use feature-card for features, warning-card for limitations, special-card for roadmap

### Status Reports
- **Title:** "[Project] Status Report"
- **Key Takeaways:** Overall status, blockers
- **Sections:** By workstream or milestone
- **Components:** Stats for metrics, timeline for schedule, action items
- **Card types:** Use feature-card for green items, warning-card for yellow, error-card for red

---

## DO's
- Auto-format without asking questions
- Include Benmore logo
- Extract key takeaways from content
- **Auto-select card types based on content keywords**
- Use gradient backgrounds and glow effects
- Use stat cards with bottom accent bars for numbers
- Use flow steps for sequential processes
- Include tech-req boxes for technical content
- Use badges for priorities and status
- Preserve ALL information from the original document
- Break walls of text into logical sections

## DON'Ts
- Don't ask questions - just format
- Don't use emojis
- Don't use colors outside the palette
- Don't add content not in the original
- Don't skip the key takeaways section
- Don't make walls of text - break into sections
- Don't use rainbow colors in diagrams
- Don't use more than 5 colors in any visualization
- Don't use the wrong card type for content (follow keyword rules)

## Output
Single HTML file with:
- Inter font from Google Fonts
- Multi-tone navy gradient background (fixed)
- Glassmorphism card effects
- **Color-coded content cards (auto-selected)**
- Gradient stat cards with accent bars
- Flow step components for processes
- Technical requirements boxes
- Priority badges
- Radial glow effects
- Dark-themed diagrams and charts
- All content organized and formatted
- Print styles included
- Mobile responsive
