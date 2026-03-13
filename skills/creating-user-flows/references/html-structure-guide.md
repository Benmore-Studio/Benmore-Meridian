# HTML Structure Guide for User Flow Deliverables

## Template

Read `assets/template.html` for the complete Benmore dark theme HTML/CSS template. Copy its full `<style>` block and `<script type="module">` block into every generated HTML file.

## Mermaid Dark Theme Configuration

Embed this in `<script type="module">` inside `<head>`:

```javascript
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
        mainBkg: '#1e3a5f',
        secondBkg: '#0f2744',
        border1: '#3b82f6',
        border2: '#1e40af',
        arrowheadColor: '#60a5fa',
        fontFamily: 'Inter, sans-serif',
        fontSize: '14px',
        textColor: '#ffffff',
        nodeTextColor: '#ffffff'
    }
});
```

## File Naming

`[Subject]-[Type]-v[version].html`

Examples:
- `Mediator-Onboarding-Flow-v1.html`
- `SalesRep-Primary-Intake-v2.html`
- `Admin-Portal-Workflow-v1.html`
- `Transaction-Lifecycle.html`

## Required HTML Sections

Every HTML file must include these sections (in this order):

1. **Header** — Project name, flow name as subtitle, version badge
2. **Key Workflow Principles** — `highlight-card` with bullet points summarizing design decisions
3. **Diagrams** — `diagram-container` for each Mermaid chart (use multi-diagram pattern from `references/multi-diagram-patterns.md` if complex)
4. **Workflow Steps Breakdown** — Numbered `flow-step` elements with descriptions
5. **Feature/Detail Sections** — Cards explaining each major feature area
6. **Design Principles** — `warning-card` elements for important constraints
7. **Color Legend** — Always include at the bottom, explaining what each color means in the diagrams
8. **Technical Notes** — Cards for implementation considerations (if relevant)

## Card Types — Use ONLY These 5

**CRITICAL:** Do NOT invent custom card classes. Every piece of content maps to one of these five:

| Card Class | Color | Use For | Example Content |
|------------|-------|---------|-----------------|
| `.card` | Blue | General information, technical details | "API integration points", "Data flow" |
| `.feature-card` | Green | Features, capabilities, positive states | "Profile creation", "Search functionality" |
| `.warning-card` | Amber | Constraints, important notes, design principles | "Offline-first requirement", "No dropdowns" |
| `.error-card` | Red | Error handling, failure states, critical warnings | "Payment failure", "Validation errors" |
| `.highlight-card` | Blue accent (left border) | Key takeaways, executive summary | "Key Workflow Principles" at top of page |

### Card Selection Decision Tree

Ask these questions in order:

1. Is it a key takeaway or executive summary? → `.highlight-card`
2. Is it a positive capability, feature, or success state? → `.feature-card`
3. Is it a constraint, limitation, or important design note? → `.warning-card`
4. Is it an error state, failure mode, or critical warning? → `.error-card`
5. Everything else (general info, technical detail, process description) → `.card`

### Common Mapping Mistakes — Do NOT Do These

| Content Type | Wrong (invented class) | Correct |
|--------------|----------------------|---------|
| Email notifications | `.email-card` | `.card` or `.feature-card` |
| Payment flows | `.payment-card` | `.feature-card` |
| System alerts | `.alert-card` | `.warning-card` |
| Admin actions | `.admin-card` | `.card` |
| API integrations | `.api-card` | `.card` |
| User permissions | `.permission-card` | `.warning-card` |

## Layout Helpers

### Grids

```html
<div class="grid">          <!-- 2 columns -->
<div class="grid grid-3">   <!-- 3 columns -->
<div class="grid grid-4">   <!-- 4 columns -->
```

Use grids for side-by-side cards when content is naturally parallel (e.g., comparing two user types, listing metrics).

### Stat Cards (inside grids)

```html
<div class="grid grid-3">
    <div class="stat-card">
        <div class="stat-value">24</div>
        <div class="stat-label">Weeks Timeline</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">3</div>
        <div class="stat-label">User Types</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">12</div>
        <div class="stat-label">Core Screens</div>
    </div>
</div>
```

### Flow Steps

```html
<div class="flow-step">
    <div class="flow-number">1</div>
    <div class="flow-content">
        <h4>Step Title</h4>
        <p>Step description explaining what happens and why.</p>
    </div>
</div>
```

### Dividers

```html
<div class="divider"></div>
```

Use between major sections to create visual separation.

### Section Headers

```html
<div class="section">
    <div class="section-header">Section Name</div>
    <!-- content -->
</div>
```

The `section-header` auto-generates a gradient line extending to the right.

## Self-Contained Requirement

Every HTML file must be fully self-contained:
- All CSS inline in `<style>` tags (no external stylesheets except fonts)
- Mermaid.js loaded via CDN (`https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs`)
- Inter font from Google Fonts
- Benmore logo in header: `https://benmore.tech/static/images/og_image.png`
- Responsive design with mobile breakpoint at 768px
- Print styles for white-background printing
- Must render correctly when opened directly in any browser (no build step)
