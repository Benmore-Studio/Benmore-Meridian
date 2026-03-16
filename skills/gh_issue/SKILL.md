---
name: gh_issue
description: GitHub Issue Generator Skill
context: fork
---

# GitHub Issue Generator Skill

## Purpose
Generate detailed, actionable GitHub issues for development tasks. Break down features into modular, atomic tasks with precise implementation guidance including code snippets, file locations, and critical thinking notes.

## When to Use
- Breaking down large features into implementable tasks
- Creating developer-ready work items with clear acceptance criteria
- Generating issues that can be assigned to team members
- **IMPORTANT:** Always ask who to assign issues to before creating them
- Documenting implementation approaches for complex features

## How This Skill Works

When invoked, this skill will:
1. **ASK ABOUT DEVELOPER ASSIGNMENT FIRST** (Critical!)
   - Always ask: "Who should I assign these issues to?"
   - Get developer's name (e.g., "Funbi", "John")
   - **VERIFY GITHUB USERNAME:** Ask if this is their first time or confirm their GitHub username
   - Store common developer mappings:
     - Funbi (Oluwafunbi Onaeko) → @ouujay
     - [Add more as you learn them]
2. Analyze the feature/task request
3. Break it down into atomic, modular subtasks
  **STORE LOCALLY FIRST IN A CREATED DIRECTORY CALLED github-issues WITHIN PROJECT DIRECTORY FOR MANUAL APPROVAL BEFORE POSTING ANYTHING TO GITHUB**
4. Generate detailed GitHub issues for each subtask
5. Include implementation steps, code examples, and critical notes
6. Create issues via `gh` CLI with `--assignee <github-username>` flag

## Issue Template Structure

Each generated issue will include:

### Title
- Clear, actionable format: `[Component] Brief description`
- Example: `[video_editor] Create VideoInteractionPoint model`

### Description Sections (KEEP CONCISE)

**Overview** (2-3 sentences max)
- What this task accomplishes
- Why it's needed

**Requirements** (Bullet points)
- Hard requirements only
- What must be implemented
- Key constraints or specifications

**Key Files/Locations** (Brief list)
- Where changes likely needed
- Reference existing patterns if critical

**Implementation Notes** (Optional, 1-2 hints max)
- One or two critical technical hints if needed
- Link to existing code patterns
- DO NOT write full implementations

**Acceptance Criteria** (Checklist)
- Clear, testable outcomes
- What "done" means

**Dependencies**
- Blocks/blocked by (if any)

## Input Format

When using this skill, provide:
```
Feature: [Name of feature]
Context: [Brief context from CLAUDE.md or project docs]
Task: [Specific task to break down]
Assignee: [Developer name, e.g., "Funbi"]
GitHub Username: [e.g., "@ouujay" - MUST verify this!]
Priority: [high/medium/low]
```

**CRITICAL:** If GitHub username is not provided or unclear, STOP and ask:
- "Is this developer new to the project?"
- "What is their GitHub username?"
- "Can you provide their GitHub profile URL to verify?"

**Known Developer Mappings:**
- Funbi (Oluwafunbi Onaeko) → @ouujay → https://github.com/ouujay

## Output Format

The skill will output:
1. A list of atomic tasks with titles
2. Full GitHub issue markdown for each task
3. `gh` CLI commands to create issues (if gh is available)
4. Dependency graph showing task relationships

## Example Usage

**Input:**
```
Feature: Video Editor Interactive Breakpoints
Context: See VIDEO_EDITOR_INTEGRATION_PLAN.md Phase 1
Task: Implement the core data models for video editor
Assignee: Funbi
Priority: high
```

**Output:**
```markdown
## Breakdown: Core Data Models (4 tasks)

### Task 1: Create video_editor Django app
### Task 2: Implement VideoInteractionPoint model
### Task 3: Implement VideoEndAction model
### Task 4: Implement StudentVideoResponse model

---

# ISSUE 1: [video_editor] Create Django app and initial structure

## Overview
Create the new `video_editor` Django app that will house all video interaction functionality...

[Full detailed issue content]

---

# ISSUE 2: [video_editor] Create VideoInteractionPoint model
...
```

## Skill Behavior

### Task Decomposition Strategy
1. **Read project context** from CLAUDE.md and relevant docs
2. **Identify dependencies** between subtasks
3. **Order tasks** by logical implementation sequence
4. **Size appropriately** - each task should be completable in < 1 day
5. **Include rollback plans** for risky changes
6. **Handle uncertainties:**
   - If clarification/design choice needed from client → Ask Leo directly OR add to project notes
   - If future consideration → Add to project notes (e.g., `077-notes.md`), NOT as GitHub issue
   - Never create GitHub issues for unknowns or "to be determined" items

### Code Snippet Quality
- Use actual code from the repository as reference
- Follow existing patterns (TailwindCSS, Django conventions, etc.)
- Include imports and context
- Add inline comments for non-obvious decisions
- Reference line numbers in existing files

### Developer Empathy
- Assume the developer knows Django but not this specific codebase
- Link to relevant existing files for pattern reference
- Explain "why" not just "what"
- Include troubleshooting notes for common issues
- Provide both happy path and edge cases

### GitHub Integration
- **ALWAYS verify developer GitHub username before creating issues**
- Use `gh issue create` with appropriate flags
- Add labels automatically (e.g., `enhancement`, `backend`, `frontend`)
  - NOTE: Check if labels exist in repo first (use `gh label list` if needed)
  - If custom labels don't exist, fall back to basic labels like `enhancement`
- Link to project boards if configured
- Set milestones based on priority
- **CRITICAL:** Use `--assignee <github-username>` flag (NOT `-a`)
  - Example: `--assignee ouujay` (for Funbi)
  - Verify username format (no @ symbol in flag)
  - If username is incorrect, issue creation will fail

## Critical DO's and DON'Ts

### DO's ✅
- **BE CONCISE** - Issues should be short and to the point (most important!)
- Break tasks into true atoms (single responsibility)
- List hard requirements clearly with bullets
- Include specific file paths from the actual repo
- Reference existing code patterns
- Leave implementation details to the developer
- Mention critical constraints (e.g., "use TailwindCSS", "use existing decorators")
- Link to documentation if relevant
- Include rollback instructions for database migrations
- Consider mobile/tablet implications for frontend tasks
- Add security considerations for user-facing features
- **When clarifications/design choices needed:** Either ask Leo directly OR add to project notes (never create GitHub issue for unknowns)
- **For future considerations:** Add to overarching project notes, NOT as GitHub issues

### DON'Ts ❌
- **Don't write full code implementations** (1-2 hints max if critical)
- **Don't create overly prescriptive steps** - trust the developer
- **Don't include exhaustive testing sections** - brief acceptance criteria only
- **Don't write long paragraphs** - use bullets
- **Don't create GitHub issues for future/unclear requirements** - add to project notes instead
- Don't create tasks that depend on external unknowns
- Don't write vague steps like "implement the feature"
- Don't ignore existing patterns (use TailwindCSS not Bootstrap!)
- Don't forget to reference the permission system in core/decorators.py
- Don't create unnecessary files (prefer editing existing)
- Don't forget about migrations for model changes

## Advanced Features

### Intelligent Sequencing
The skill will analyze dependencies and output:
```
Task Sequence:
1. Task A (no dependencies)
2. Task B (depends on A)
3. Task C (depends on A)
4. Task D (depends on B, C)

Parallel-safe: [A], [B, C can run in parallel after A], [D]
```

### Code Pattern Recognition
When generating code, the skill will:
- Scan repository for similar patterns
- Match existing code style
- Use the same imports and conventions
- Reference similar implementations

### Risk Assessment
Each issue will include:
- 🟢 Low risk: Isolated change, easily reversible
- 🟡 Medium risk: Affects multiple files, requires testing
- 🔴 High risk: Database migrations, user-facing changes, security implications

## Repository Context Awareness

Before generating issues, the skill will:
1. Read CLAUDE.md for project overview
2. Check relevant plan documents (VIDEO_EDITOR_INTEGRATION_PLAN.md)
3. Examine existing models/views/templates for patterns
4. Verify file paths exist
5. Check for existing similar implementations

## Quality Checklist

Before outputting issues, verify:
- [ ] Each task is independently completable
- [ ] Code examples are syntactically correct
- [ ] File paths reference actual locations
- [ ] Implementation follows existing patterns
- [ ] Security/permission considerations included
- [ ] Testing approach is clear
- [ ] Acceptance criteria are measurable
- [ ] Dependencies are explicit
- [ ] Rollback plan exists for risky changes

## GitHub CLI Commands

If `gh` is available, generate commands like:
```bash
gh issue create \
  --repo owner/repo-name \
  --title "[video_editor] Create VideoInteractionPoint model" \
  --body-file issue_content.md \
  --label "enhancement" \
  --assignee "ouujay"
```

**Important Notes:**
- Use `--body-file` for markdown files (NOT `--body "$(cat ...)"``)
- Use `--assignee` with GitHub username (no @ symbol)
- Verify labels exist in repo before using (fall back to `enhancement` if unsure)
- Always include `--repo owner/repo-name` for clarity

If `gh` is not available, provide markdown files that can be copy-pasted into GitHub's web interface.

---

## Skill Invocation

To use this skill, simply say:
```
Use the github-issue-generator skill to create issues for [feature/task description]
```

Or provide structured input:
```
Feature: Video Editor
Task: Phase 1 - Core Data Models
Assignee: Funbi (@ouujay)
```

**The skill will ALWAYS ask for developer assignment if not provided:**
1. "Who should these issues be assigned to?"
2. "What is their GitHub username?" (if new developer)
3. "Can you verify their GitHub profile URL?" (if uncertain)

Only after confirming assignment will issues be created!
