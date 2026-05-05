# Playwright-CLI Recipes

Common sequences you'll repeat across every client walkthrough. Read this when the browser is fighting you instead of capturing pages.

---

## Recipe 1 — Open, resize, screenshot

The minimum every walkthrough starts with.

```bash
playwright-cli open http://localhost:3000
playwright-cli resize 1440 900
playwright-cli screenshot --filename=/abs/path/docs/screenshots/client-guide/01-landing.png
```

Use **absolute paths** for `--filename`. Relative paths break the moment a `cd` happens — and a `cd` in the same shell will silently invalidate the playwright-cli session because session state lives in `.playwright-cli/` of the cwd.

If the session does break (you'll see "The browser 'default' is not open"), just reopen and re-inject any auth state. Don't waste time debugging the broken session.

---

## Recipe 2 — Mint a real JWT and inject it

For auth-gated pages, never stub a fake token. Mint a real one.

```bash
# 1. Register a demo user via the API
node -e '
fetch("http://localhost:8000/api/v1/auth/register/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "client-demo@example.com",
    password: "DemoPass123!",
    password_confirm: "DemoPass123!",
    first_name: "Demo",
    last_name: "Client",
    role: "athlete"
  })
}).then(r => r.text()).then(console.log)
'

# 2. Log in to get the JWT pair
node -e '
fetch("http://localhost:8000/api/v1/auth/login/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "client-demo@example.com",
    password: "DemoPass123!"
  })
}).then(r => r.json()).then(t => {
  require("fs").writeFileSync("/tmp/jwt.json", JSON.stringify(t));
  console.log("saved");
})
'

# 3. Inject into both localStorage AND cookie (most modern apps check both)
ACCESS=$(node -e 'console.log(JSON.parse(require("fs").readFileSync("/tmp/jwt.json","utf8")).access)')
REFRESH=$(node -e 'console.log(JSON.parse(require("fs").readFileSync("/tmp/jwt.json","utf8")).refresh)')

playwright-cli localstorage-set access_token "$ACCESS"
playwright-cli localstorage-set refresh_token "$REFRESH"
playwright-cli cookie-set access_token "$ACCESS" --domain=localhost
```

Adapt the field names (`access`, `refresh`, `email`, `password_confirm`) to whatever the target API uses. The pattern is always the same: register → login → persist tokens to a temp file → inject into the browser.

---

## Recipe 3 — Find a button without a label

Sometimes the UI has icon-only buttons or generic divs that act as buttons. Take a snapshot, then drill down.

```bash
# Whole-page snapshot to find the right region
playwright-cli --raw snapshot --depth=4 | head -50

# Drill into a specific region
playwright-cli --raw snapshot e22 --depth=8 | head -80
```

The `e22` is a ref from the previous snapshot's output. `--depth` limits how deep the tree expands so you don't drown in noise.

When you find the element you want to click, use the ref:

```bash
playwright-cli click e167
```

---

## Recipe 4 — Walk through a multi-step wizard

A tight loop for capturing every step of an onboarding wizard.

```bash
# Step N
playwright-cli --raw snapshot --depth=4              # find the step heading
playwright-cli --raw snapshot eXX --depth=8          # find the form fields
playwright-cli fill e<input1> "value 1"
playwright-cli fill e<input2> "value 2"
playwright-cli check e<checkbox>                     # for required acceptance
playwright-cli screenshot --filename=/abs/NN-stepN-filled.png
playwright-cli click e<continue-button>              # advance
# repeat for next step
```

Capture **two states** of high-information steps: empty and filled. The empty state shows the user what they're walking into; the filled state shows them what their version will look like.

---

## Recipe 5 — Dismiss and re-open a welcome modal

Welcome modals fire once per browser session. To capture both the modal *and* the underlying page, screenshot first, then dismiss.

```bash
# Modal is showing — screenshot it
playwright-cli screenshot --filename=/abs/01-welcome-modal.png

# Dismiss by clicking the affirmative button
playwright-cli click e<continue-button>

# Now the underlying page is visible
playwright-cli screenshot --filename=/abs/02-landing-after-modal.png
```

If the modal needs to come back later (to capture a different choice), clear localStorage and reload:

```bash
playwright-cli localstorage-clear
playwright-cli reload
```

---

## Recipe 6 — Scroll-and-capture down a long landing

For landing pages that need 3–5 screenshots stacked:

```bash
playwright-cli screenshot --filename=/abs/02-landing-hero.png
playwright-cli eval "() => window.scrollTo(0, 800)"
playwright-cli screenshot --filename=/abs/03-landing-trusted.png
playwright-cli eval "() => window.scrollTo(0, 1800)"
playwright-cli screenshot --filename=/abs/04-landing-features.png
playwright-cli eval "() => window.scrollTo(0, 3200)"
playwright-cli screenshot --filename=/abs/05-landing-pricing.png
playwright-cli eval "() => window.scrollTo(0, document.body.scrollHeight)"
playwright-cli screenshot --filename=/abs/06-landing-cta-footer.png
```

Pick scroll offsets that align with section breaks (use the snapshot's bounding-box info — `--boxes` flag — if you need precise coordinates).

---

## Recipe 7 — Capture a verification-gate or error state intentionally

Error states are part of the UX. Trigger them on purpose and capture them.

```bash
# Try to do something the user is not yet authorized to do
playwright-cli click e<send-invitations-button>

# The error banner now renders — screenshot it
playwright-cli screenshot --filename=/abs/22-verify-gate.png
```

Don't write around these states. Document them. They prevent customer surprise three weeks into deployment.

---

## Recipe 8 — Multi-page tour with consistent naming

For walking through every dashboard sub-page in one go:

```bash
for path in calculators tasks learning documents settings business-formation; do
  playwright-cli goto http://localhost:3000/dashboard/$path
  sleep 1
  playwright-cli screenshot --filename=/abs/path/3X-dashboard-$path.png
done
```

Then renumber the `3X-` prefix to actual numbers (`31-`, `32-`, …) afterward. Renumbering is faster than counting in your head while looping.

---

## Common pitfalls

- **CWD shifts break the session.** A `cd` (especially `cd /tmp`) makes `playwright-cli` look for the session state file in a different `.playwright-cli/` and fail with "browser not open." Stay in one cwd, or always `playwright-cli open` again.
- **Relative `--filename` is unreliable.** It's resolved against the cwd, which is exactly what changes when you don't expect it to.
- **Console errors are usually fine.** Most apps log development noise. Don't waste time chasing every red squiggle in the console — only investigate if a screenshot itself looks wrong.
- **Reflows take a moment.** If a click triggers a route change with a fade animation, a 300–500ms `sleep` between the click and the screenshot avoids capturing a half-rendered page.
- **Modals hide the page.** Always check the snapshot for an unexpected `dialog` element before screenshotting — what you intended to capture may be obscured.
