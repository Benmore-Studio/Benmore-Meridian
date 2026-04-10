# Benmore Reporting API Reference

> Internal staff-only API for querying projects and assets.
> Designed for automated report generation and Claude Code scheduled tasks.

**Base URL:** `https://client.benmore.tech/api/v1`

---

## Path Mapping

The Benmore API exposes two URL schemes for several endpoints. Both resolve to the same backend views:

| Reporting Path (this reference) | Client Path (`benmore_client`) |
|---------------------------------|-------------------------------|
| `/reports/my-projects/` | `/projects/` |
| `/reports/active-projects-summary/` | `/projects/summary/` |
| `/reports/project-status/<id>/` | `/projects/<id>/status/` |
| `/reports/project-assets/<id>/` | `/projects/<id>/assets/` |
| `/reports/project-team/<id>/` | `/projects/<id>/team/` |
| `/reports/project-slack/<id>/` | `/projects/<id>/comms/` |
| `/reports/project-slack/<id>/messages/` | `/projects/<id>/comms/messages/` |
| `/reports/project-slack/<id>/thread/<ts>/` | `/projects/<id>/comms/thread/<ts>/` |
| `/reports/project-github/<id>/repos/` | `/projects/<id>/github/repos/` |

This reference documents the **reporting paths** (canonical API surface). The Python client uses the **client paths** (simplified aliases). Both work identically — use whichever matches your context.

---

## Authentication

All requests require an API key in the `X-API-KEY` header.

```bash
curl -H "X-API-KEY: bpk_your_key_here" \
    https://client.benmore.tech/api/v1/reports/my-projects/
```

### API Key Scopes

| Scope | Access |
|-------|--------|
| `projects:read` | Read project data, context, comms, meetings, assets, GitHub, Slack, team |
| `projects:write` | Create/update/delete assets, tickets, team, connect integrations |
| `flash-documents:read` | Read flash documents |
| `flash-documents:write` | Create, update, and delete flash documents |

---

## Projects

### List My Projects

```
GET /reports/my-projects/
```

Returns all projects assigned to the authenticated user with asset counts.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `detail` | boolean | Expanded data (invoices, tickets) |
| `active` | boolean | Only active projects (excludes stalled, completed, no_longer_engaged) |
| `phase` | string | Filter by phase: `pre_kickoff`, `discovery`, `implementation`, `placement`, `stalled`, `completed`, `no_longer_engaged` |

**Scope:** `projects:read`

**Response Fields:**

- `id` (UUID) — Project ID
- `title` (string) — Project name
- `description` (string) — Project description
- `phase` (string) — Phase code (e.g. `implementation`)
- `phase_display` (string) — Human-readable phase
- `kickoff_date` (date|null) — Discovery/sales kickoff date
- `implementation_date` (date|null) — Development start date
- `completion_date` (date|null) — Project completion date
- `is_deployed` (boolean) — Whether the project is deployed
- `github_repo_url` (url|null) — GitHub repository URL
- `working_on` (string) — Current work description
- `created_at` (datetime) — When the project was created
- `team_members` (array) — Staff assigned: `{username, name, title}`
- `asset_counts` (object) — Counts: `invoices`, `tickets`, `tasks`, `documents`, `presentations`, `signature_documents`, `dynamic_assets`

**Example Response:**

```json
[
  {
    "id": "a1b2c3d4-...",
    "title": "Project Alpha",
    "phase": "implementation",
    "phase_display": "Implementation",
    "github_repo_url": "https://github.com/org/repo",
    "working_on": "API integration",
    "team_members": [{"username": "jdoe", "name": "Jane Doe", "title": "Lead Developer"}],
    "asset_counts": {"invoices": 3, "tickets": 12, "tasks": 8, "documents": 5, "presentations": 2, "signature_documents": 1, "dynamic_assets": 0}
  }
]
```

---

### Active Projects Summary

```
GET /reports/active-projects-summary/
```

Lightweight overview of all active projects (phases: `pre_kickoff`, `discovery`, `implementation`, `placement`) with health indicators and external service references. **Use as the entry point for scheduled tasks.**

**Scope:** `projects:read`

**Response Fields:**

- `count` (int) — Number of active projects
- `active_projects` (array):
  - `id` (UUID) — Project ID
  - `title` (string) — Project name
  - `phase` (string) — Phase code
  - `slack_channel_id` (string|null) — Slack channel for MCP connector
  - `github_repo_url` (url|null) — GitHub repo URL
  - `github_repo_owner` (string|null) — GitHub org/user
  - `github_repo_name` (string|null) — GitHub repo name
  - `team_count` (int) — Number of team members
  - `health` (string|null) — Intelligence health: `green`, `yellow`, or `red`
  - `days_since_last_meeting` (int|null) — Days since most recent meeting
  - `meetings_past_7_days` (int) — Meetings in the past week
  - `open_action_items` (int) — Open/in-progress action items
  - `overdue_invoices` (int) — Overdue invoice count

**Example Response:**

```json
{
  "count": 3,
  "active_projects": [
    {
      "id": "9027dd6c-...",
      "title": "JB Pro [BEN-146]",
      "phase": "implementation",
      "phase_display": "Implementation",
      "slack_channel_id": "C0123ABC",
      "github_repo_url": "https://github.com/org/jb-pro",
      "github_repo_owner": "org",
      "github_repo_name": "jb-pro",
      "team_count": 6,
      "health": "yellow",
      "days_since_last_meeting": 4,
      "meetings_past_7_days": 2,
      "open_action_items": 3,
      "overdue_invoices": 0
    }
  ]
}
```

---

### Projects Summary (Client Alias)

```
GET /projects/summary/
```

Alias for `/reports/active-projects-summary/` used by the Python client's `projects_summary()` method. Returns the same response. See [Active Projects Summary](#active-projects-summary) above.

**Scope:** `projects:read`

---

### Search Projects

```
GET /projects/search/
```

Search by title, description, or phase. Case-insensitive partial matching, up to 50 results ordered by creation date (newest first). Staff see all projects; non-staff see only assigned.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Search query (title, description, phase) |
| `phase` | string | Filter by exact phase |

**Scope:** `projects:read`

**Response Fields:** `id`, `title`, `phase`, `description`, `kickoff_date`, `implementation_date`, `completion_date`, `is_deployed`, `created_at`

---

### Search Users' Projects (Superuser Only)

```
GET /projects/users/
```

Search for any user's projects by username, email, or name.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `q` | string (required) | Search by username, email, first name, or last name (min 2 chars) |

**Scope:** `projects:read`

**Response Fields:** `query`, `count`, `results[]` with `{id, username, email, first_name, last_name, projects[]}`

---

### Create Project

```
POST /projects/create/
```

Create a new project in the portal.

**Body Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `title` | string (required) | Project title (e.g. "My Project [BEN-900]") |
| `description` | string | Project description |
| `phase` | string | Phase (default: `pre_kickoff`) |

**Scope:** `projects:write`

**Response:** Returns the created project object with `id`, `title`, `phase`, `phase_display`, `description`, `created_at`.

---

### Update Project

```
PATCH /projects/<project_id>/update/
```

Update project fields.

**Body Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `phase` | string | Project phase |
| `working_on` | string | Current work description |
| `description` | string | Project description |

**Scope:** `projects:write`

**Response:** Returns the updated project object.

---

### Project Context

```
GET /projects/<project_id>/context/
```

Single-call project brief for Claude Code sessions. Returns project info, team, meetings (with optional raw transcripts via `?full=true`), Slack pulse, GitHub progress, blockers, and financials.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `full` | boolean | Include raw meeting transcripts (default `false`) |
| `days` | int | Limit history to last N days (default `30`) |

**Scope:** `projects:read`

**Response Structure:** Returns `project` (info + dates), `team`, `meetings` (with summaries, optional transcripts), `slack` (channel activity), `github` (board status, recent items), `blockers`, `financials` (invoices, totals).

---

### Project Status (Comprehensive)

```
GET /reports/project-status/<project_id>/
```

Comprehensive per-project status. User must be assigned to the project or be a superuser.

**Scope:** `projects:read`

**Response Structure:**

- **`project`** — `id`, `title`, `phase`, `phase_display`, `working_on`, `kickoff_date`, `implementation_date`, `completion_date`, `is_deployed`, `do_app_health_status`
- **`team_members`** — `username`, `name`, `title`
- **`meetings`**
  - `past_30_days` (array) — Full meeting summaries: `id`, `title`, `date_time`, `fireflies_transcript_id`, `has_transcript`, `duration_minutes`, `summary`
  - `count_past_7_days`, `count_past_30_days`, `total_all_time`
- **`action_items`**
  - `open`, `in_progress`, `recently_completed` (last 10) — `id`, `task`, `owner`, `due_date`, `status`, `source_meeting_id`
  - `total_open`
- **`blockers`** — `unresolved[]` with `id`, `issue`, `owner`, `severity` (high/medium/low), `resolved_at`, `resolution`
- **`decisions`** — Last 10: `id`, `decision_text`, `made_by`, `context`
- **`open_questions`** — Unanswered: `id`, `question`, `raised_by`, `answered_at`, `answer`
- **`kanban`**
  - `summary` — Counts by status: `todo`, `backlog`, `in_progress`, `completed`, `blocked`
  - `total_tickets`, `blocked_tickets[]`, `recent_activity[]` (last 20)
- **`financials`** — `total_billed`, `total_paid`, `total_outstanding`, `overdue[]`, `upcoming[]`, `all_invoices[]` (last 20)
- **`intelligence`** — `health`, `health_reasons[]`, `current_phase`, `summary`, `total_meetings_analyzed`, `last_updated`
- **`external_refs`** — `slack_channel_id`, `github_repo_url`, `github_repo_owner`, `github_repo_name`, `github_repo_branch`

---

### Project Assets (All-in-One)

```
GET /reports/project-assets/<project_id>/
```

Aggregates all assets into a single response. User must be assigned or superuser.

**Scope:** `projects:read`

**Response Structure:**

- **`project`** — `id`, `title`, `phase`, `phase_display`, `description`, `working_on`, dates, `is_deployed`
- **`meetings`** — `id`, `title`, `date_time`, `duration_minutes`, `summary`, `transcript_text`, `fireflies_transcript_id`
- **`documents`** — `id`, `title`, `slug`, `content`, `category`, `status`
- **`dynamic_assets`** — `id`, `title`, `html_content`
- **`presentations`** — `id`, `title`, `slides[]` with `order`, `title`, `html_content`
- **`signature_documents`** — `id`, `title`, `content`, `status` (draft/published/signed)
- **`flash_documents`** — `id`, `title`, `content`, `sharing_scope`
- **`invoices`** — `invoice_number`, `status`, `total`, `amount_paid`, `amount_due`
- **`intelligence`** — `action_items[]`, `blockers[]`, `decisions[]`, `open_questions[]`
- **`counts`** — Asset counts per type

---

## Team Management

### List / Add / Remove Team Members

```
GET    /reports/project-team/<project_id>/
POST   /reports/project-team/<project_id>/
DELETE /reports/project-team/<project_id>/
```

GET lists current members. POST adds the authenticated user (or specific users if superuser via `usernames` body param). DELETE removes similarly.

**Body Parameters (POST/DELETE):**

| Param | Type | Description |
|-------|------|-------------|
| `usernames` | array[string] | Usernames to add/remove. Superuser only. Omit to add/remove yourself. |

**Scope:** `projects:write`

**Response Fields:** `project_id`, `project_title`, `team_members[]` with `username`, `name`, `title`

---

## Slack Integration

### Channel Summary & Update

```
GET   /reports/project-slack/<project_id>/
PATCH /reports/project-slack/<project_id>/
```

GET fetches channel summary (info, pinned messages, recent messages, files, activity stats). PATCH connects/updates the Slack channel.

**Query Parameters (GET):**

| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | Max recent messages (default 50, max 200) |

**Body Parameters (PATCH):**

| Param | Type | Description |
|-------|------|-------------|
| `slack_channel_id` | string (required) | Slack channel ID (e.g. `C085JMC1XAT`). The Python client sends this as `channel_id`. |

**Scope:** `projects:read` (GET), `projects:write` (PATCH)

**Response Fields:** `channel_info`, `pinned[]`, `recent_messages[]`, `files[]`, `activity`

---

### Message History & Send Messages

```
GET  /reports/project-slack/<project_id>/messages/
POST /reports/project-slack/<project_id>/messages/
```

GET: Paginated message history with cursor/oldest/latest params.
POST: Send a message; optionally reply to a thread with `thread_ts`.

**Query Parameters (GET):**

| Param | Type | Description |
|-------|------|-------------|
| `cursor` | string | Pagination cursor |
| `limit` | int | Max messages (default 50) |
| `oldest` | string | Unix timestamp lower bound |
| `latest` | string | Unix timestamp upper bound |

**Body Parameters (POST):**

| Param | Type | Description |
|-------|------|-------------|
| `text` | string (required) | Message text |
| `thread_ts` | string | Thread timestamp to reply to |

**Scope:** `projects:read` (GET), `projects:write` (POST)

---

### Thread Replies

```
GET /reports/project-slack/<project_id>/thread/<thread_ts>/
```

Get all replies in a Slack message thread.

**Scope:** `projects:read`

---

## Meetings / Communications

### List & Create Meetings

```
GET  /projects/<project_id>/comms/meetings/
POST /projects/<project_id>/comms/meetings/
```

GET: List meetings with summaries. `?full=true` includes raw transcripts. `?days=N` limits to last N days.
POST: Create a meeting record.

**Body Parameters (POST):**

| Param | Type | Description |
|-------|------|-------------|
| `title` | string (required) | Meeting title |
| `date_time` | datetime (required) | ISO 8601 datetime |
| `notes` | string | Meeting notes |

**Scope:** `projects:read` (GET), `projects:write` (POST)

---

## GitHub Integration

### GitHub Project Board

```
GET   /projects/<project_id>/github/
PATCH /projects/<project_id>/github/
```

GET: Fetch GitHub Projects v2 summary (status counts, current iteration, recent items).
PATCH: Update `github_project_owner` and `github_project_number`.

**Scope:** `projects:read` (GET), `projects:write` (PATCH)

**Response Fields:** `project_info`, `status_counts`, `current_iteration`, `recent_items[]`, `total_items`

---

### GitHub Project Items

```
POST   /projects/<project_id>/github/items/
PATCH  /projects/<project_id>/github/items/
DELETE /projects/<project_id>/github/items/
```

POST: Create a draft issue. PATCH: Update a field value. DELETE: Remove an item.

**Body Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `title` | string (required) | (POST) Item title |
| `body` | string | (POST) Item description |
| `status` | string | Status value (e.g. "Todo", "In Progress", "Done") |
| `priority` | string | Priority value (e.g. "P0", "P1", "P2") |
| `size` | string | Size value (e.g. "XS", "S", "M", "L", "XL") |
| `item_id` | string (required) | (PATCH/DELETE) GitHub item node ID |
| `field` | string (required) | (PATCH) Field name to update |
| `value` | string (required) | (PATCH) New value |

**Scope:** `projects:write`

---

### Create GitHub Project

```
POST /github/create-project/
```

Create a new GitHub Project v2 under the given org/user. Optionally link it to a portal project.

**Body Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `owner` | string (required) | GitHub org or user login |
| `title` | string (required) | Title for the new GitHub Project |
| `project_id` | UUID | Portal project ID to link to |

**Scope:** `projects:write`

---

### Linked Repos

```
GET    /reports/project-github/<project_id>/repos/
POST   /reports/project-github/<project_id>/repos/
DELETE /reports/project-github/<project_id>/repos/
```

GET: List repos with full stats (contributors, commits, PRs, code frequency).
POST: Link a repo. DELETE: Unlink a repo.

**Body Parameters (POST/DELETE):**

| Param | Type | Description |
|-------|------|-------------|
| `repo` | string (required) | Full repo name, e.g. `"Benmore-Studio/client-portal"` |

**Scope:** `projects:read` (GET), `projects:write` (POST, DELETE)

---

## Documents

### Project Documents

```
GET    /projects/<project_id>/documents/
POST   /projects/<project_id>/documents/
GET    /projects/<project_id>/documents/<id>/
PATCH  /projects/<project_id>/documents/<id>/
DELETE /projects/<project_id>/documents/<id>/
```

Full CRUD for project documents. POST supports `multipart/form-data` for file attachments. Author set automatically. Only staff or author can update/delete.

**Scope:** `projects:read` (GET), `projects:write` (POST, PATCH, DELETE)

**Response Fields:** `id`, `title`, `slug`, `description`, `category`, `status`, `version`, `tags`, `author`, `has_attachment`, `created_at`, `updated_at`

---

### Dynamic Assets

```
GET    /projects/<project_id>/dynamic-assets/
POST   /projects/<project_id>/dynamic-assets/
GET    /projects/<project_id>/dynamic-assets/<id>/
PATCH  /projects/<project_id>/dynamic-assets/<id>/
DELETE /projects/<project_id>/dynamic-assets/<id>/
```

Dynamic assets contain complete HTML content (with optional `<style>` and `<script>` tags). Tailwind CSS available by default. Only staff or creator can update/delete.

**Scope:** `projects:read` (GET), `projects:write` (POST, PATCH, DELETE)

**Response Fields:** `id`, `title`, `description`, `created_by`, `created_at`, `updated_at`; detail includes `html_content`

---

### Signature Documents

```
GET    /projects/<project_id>/signature-documents/
POST   /projects/<project_id>/signature-documents/
GET    /projects/<project_id>/signature-documents/<id>/
PATCH  /projects/<project_id>/signature-documents/<id>/
DELETE /projects/<project_id>/signature-documents/<id>/
POST   /projects/<project_id>/signature-documents/<id>/sign/
```

Staff-only CRUD. Cannot update/delete if already signed. The `/sign/` endpoint captures IP address for audit trail.

**Scope:** `projects:read` (GET), `projects:write` (POST, PATCH, DELETE, sign)

**Response Fields:** `id`, `title`, `slug`, `description`, `status` (draft/published/signed), `created_by`, `signed_by`, `signed_at`, `created_at`, `updated_at`; detail includes `content`

---

## QA Logs

### QA Log CRUD

```
GET    /projects/<project_id>/qa/
POST   /projects/<project_id>/qa/
PATCH  /projects/<project_id>/qa/
DELETE /projects/<project_id>/qa/
```

Track QA issues with optional GitHub sync. POST syncs to GitHub Project. PATCH updates status (`open`/`resolved`).

**Body Parameters (POST):**

| Param | Type | Description |
|-------|------|-------------|
| `body` | string (required) | QA note body text |
| `page_url` | string | Page URL where the issue was found |
| `visitor_name` | string | Reporter name |
| `visitor_email` | string | Reporter email |
| `element_selector` | string | CSS selector of the element |
| `screenshot` | string | Screenshot as base64 data URI or URL |

**Body Parameters (PATCH):**

| Param | Type | Description |
|-------|------|-------------|
| `status` | string (required) | `"open"` or `"resolved"` |

**Scope:** `projects:read` (GET), `projects:write` (POST, PATCH, DELETE)

**Response Fields:** `id`, `body`, `status`, `page_url`, `visitor_name`, `visitor_email`, `element_selector`, `screenshot`, `github_item_id`, `created_at`, `resolved_at`, `resolved_by`

---

### Sync QA Logs to GitHub

```
POST /projects/<project_id>/qa/sync-github/
```

Sync all existing QA logs without a `github_item_id` to the linked GitHub Project.

**Scope:** `projects:write`

**Response Fields:** `synced`, `failed`, `skipped`

---

## Diagrams

### Mermaid Diagrams

```
GET  /projects/<project_id>/diagrams/
POST /projects/<project_id>/diagrams/
```

User flow diagrams with Mermaid.js. POST auto-parses mermaid code into interactive FlowNode and NodeConnection records.

**Body Parameters (POST):**

| Param | Type | Description |
|-------|------|-------------|
| `title` | string (required) | Diagram title |
| `description` | string | Diagram description |
| `mermaid_diagram` | string (required) | Mermaid.js code (e.g. `"graph TD\n A[Start] --> B[End]"`) |

**Scope:** `projects:read` (GET), `projects:write` (POST)

**Response Fields:** `id`, `title`, `mermaid_diagram`, `node_count`

---

## Flash Documents

### List Flash Documents

```
GET /flash-documents/
```

List all flash documents accessible to the authenticated user.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `sharing_scope` | string | Filter: `private`, `specific_users`, `project_members`, `staff_only`, `all_users` |
| `is_pinned` | boolean | Filter pinned only |
| `search` | string | Search in title and content |

**Scope:** `flash-documents:read`

**Response Fields:** `id`, `title`, `slug`, `url` (full absolute URL to rendered page), `sharing_scope`, `is_pinned`, `creator`, `created_at`, `updated_at`

---

### Create Flash Document

```
POST /flash-documents/
```

**Body Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `title` | string (required) | Document title |
| `content` | string (required) | Markdown content |
| `sharing_scope` | string | Access level (default: `private`) |
| `shared_with_user_ids` | array[int] | User IDs (required when `sharing_scope=specific_users`) |
| `project` | UUID | Project ID (required when `sharing_scope=project_members`) |
| `metadata` | object | Freeform JSON metadata |
| `is_pinned` | boolean | Pin the document (default: `false`) |

**Scope:** `flash-documents:write`

**Example Response:**

```json
{
  "id": "a1b2c3d4-...",
  "title": "Daily Status Report",
  "slug": "daily-status-report",
  "url": "https://example.com/flash/daily-status-report/",
  "content": "# Status\n\n- Task A: complete",
  "sharing_scope": "private",
  "creator": {"id": 1, "username": "admin"},
  "created_at": "2026-03-08T10:00:00Z"
}
```

---

### Get / Update / Delete Flash Document

```
GET    /flash-documents/<slug>/
PATCH  /flash-documents/<slug>/
DELETE /flash-documents/<slug>/
```

Only the creator can update or delete. PATCH supports partial updates.

**Scope:** `flash-documents:read` (GET), `flash-documents:write` (PATCH, DELETE)

**GET Response Fields:** `id`, `title`, `slug`, `url`, `content`, `sharing_scope`, `is_pinned`, `creator`, `project_id`, `project_title`, `metadata`, `shared_with[]`, `created_at`, `updated_at`

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad request (missing/invalid parameters) |
| 401 | Invalid, expired, or deactivated API key |
| 403 | Missing required scope, not on project, or endpoint restricted to superusers |
| 404 | Project not found |
| 429 | Rate limited — honor `Retry-After` header and retry after the indicated delay |
| 500 | Internal server error |
| 502 | Bad gateway — transient infrastructure issue, safe to retry |
| 503 | Service unavailable — server is down or restarting, safe to retry |
| 504 | Gateway timeout — upstream is slow, safe to retry |

**Note:** Some endpoints return HTTP 200 with `{"error": "..."}` for "no resource connected" cases (no Slack channel, no GitHub Project). The Python client raises `BenmoreAPIError` for these.

**Retry behavior:** The Python client auto-retries GET requests on 429/502/503/504 with exponential backoff (3 retries, honors `Retry-After`). POST/PATCH/DELETE are never retried to avoid duplicates.

---

## Scheduled Task Workflow

The recommended flow for a daily/weekly owner dashboard report:

```bash
# Step 1: Get all active projects with health indicators
curl -s -H "X-API-KEY: $BM_API_KEY" \
     https://client.benmore.tech/api/v1/reports/active-projects-summary/

# Step 2: For each project, get comprehensive status
curl -s -H "X-API-KEY: $BM_API_KEY" \
     "https://client.benmore.tech/api/v1/reports/project-status/<project_id>/"

# Step 2b (alternative): Get ALL project assets in one call
curl -s -H "X-API-KEY: $BM_API_KEY" \
     "https://client.benmore.tech/api/v1/reports/project-assets/<project_id>/"

# Step 3: Use MCP connectors for external data
# - Slack: read recent messages from slack_channel_id
# - Fireflies: cross-reference with meetings.past_7_days[].fireflies_transcript_id
# - GitHub: get commits/PRs from github_repo_owner/github_repo_name

# Step 4: Claude synthesizes risk assessment per project
```

**Required API Key Scopes:** `projects:read` (for the full scheduled task flow, `projects:write` if updating project data).

---

## Endpoint Quick Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/reports/my-projects/` | List assigned projects with asset counts |
| GET | `/reports/active-projects-summary/` | Active projects overview with health |
| GET | `/reports/project-status/<id>/` | Comprehensive project status |
| GET | `/reports/project-assets/<id>/` | All project assets in one call |
| GET | `/projects/search/` | Search projects |
| GET | `/projects/users/` | Search users' projects (superuser) |
| POST | `/projects/create/` | Create a project |
| PATCH | `/projects/<id>/update/` | Update project fields |
| GET | `/projects/<id>/context/` | Project context brief |
| GET/POST/DELETE | `/reports/project-team/<id>/` | Manage team members |
| GET/PATCH | `/reports/project-slack/<id>/` | Slack channel summary |
| GET/POST | `/reports/project-slack/<id>/messages/` | Slack messages |
| GET | `/reports/project-slack/<id>/thread/<ts>/` | Thread replies |
| GET/POST | `/projects/<id>/comms/meetings/` | Meetings |
| GET/PATCH | `/projects/<id>/github/` | GitHub Project board |
| POST/PATCH/DELETE | `/projects/<id>/github/items/` | GitHub items |
| POST | `/github/create-project/` | Create GitHub Project |
| GET/POST/DELETE | `/reports/project-github/<id>/repos/` | Linked repos |
| GET/POST/PATCH/DELETE | `/projects/<id>/documents/` | Project documents |
| GET/POST/PATCH/DELETE | `/projects/<id>/dynamic-assets/` | Dynamic assets (HTML) |
| GET/POST/PATCH/DELETE | `/projects/<id>/signature-documents/` | Signature documents |
| POST | `/projects/<id>/signature-documents/<id>/sign/` | Sign document |
| GET/POST/PATCH/DELETE | `/projects/<id>/qa/` | QA logs |
| POST | `/projects/<id>/qa/sync-github/` | Sync QA to GitHub |
| GET/POST | `/projects/<id>/diagrams/` | Mermaid diagrams |
| GET/POST | `/flash-documents/` | Flash documents list/create |
| GET/PATCH/DELETE | `/flash-documents/<slug>/` | Flash document detail |
