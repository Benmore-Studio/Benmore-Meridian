---
name: create-project-tickets
description: Create parent and child GitHub issues linked to a GitHub Project using gh CLI
tags: [tickets, github, project-management, issues, agents]
scope: general
project: ""
---

Using /tickets, link issues to the GitHub Project — these are the systems of record.

Create parent (epic) and children (task) issues. Check if they are open or closed using gh CLI and extensions.

Use an agent team of 5-6 haiku agents to create these tickets efficiently in parallel.

For each ticket:
- Set appropriate labels (bug, feature, enhancement, etc.)
- Assign to the correct milestone if applicable
- Link parent/child relationships using task lists
- Add to the GitHub Project board
- Check for duplicates before creating

$ARGUMENTS
