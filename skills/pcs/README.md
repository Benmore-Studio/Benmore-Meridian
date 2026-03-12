# PCS Skills — Project-Specific Skills

Production skills for building and maintaining PCS (Platform Core Services) microservices.
These are **project-scoped** skills — they follow PCS conventions and are designed for that project.

## Lifecycle: Project → General

Skills can be promoted from project-specific to general:

```bash
bm skill generalize pcs-migration   # moves to skills/ and re-symlinks
```

## Available Skills

| Skill | Purpose |
|-------|---------|
| pcs-add-endpoint | Add CRUD endpoints to any PCS service |
| pcs-add-kafka-event | Add Kafka producer + consumer |
| pcs-integration-test | Write integration/unit tests |
| pcs-kong-route | Add/modify Kong Gateway routes |
| pcs-migration | Create Alembic database migrations |
| pcs-new-service | Scaffold a complete new microservice |
| pcs-pr-review | Review PRs for PCS architecture compliance |

## Installation

```bash
bm install        # installs all skills including PCS ones
bm skill list --project pcs   # see just PCS skills
```
