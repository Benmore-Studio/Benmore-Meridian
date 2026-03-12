# Dependabot Configuration Guide

## File Location
`.github/dependabot.yml`

## Complete Template for Django + React Native + GitHub Actions

```yaml
version: 2
updates:
  # Python backend (pip)
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    groups:
      python-minor-patch:
        update-types:
          - "minor"
          - "patch"
    reviewers:
      - "org/backend-team"   # replace with actual GitHub team or username
    labels:
      - "dependencies"
      - "backend"

  # JavaScript mobile (npm)
  - package-ecosystem: "npm"
    directory: "/mobile"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    groups:
      npm-minor-patch:
        update-types:
          - "minor"
          - "patch"
    reviewers:
      - "org/mobile-team"    # replace with actual GitHub team or username
    labels:
      - "dependencies"
      - "mobile"
    ignore:
      # Pin Expo SDK — only upgrade intentionally
      - dependency-name: "expo"
        update-types: ["version-update:semver-major", "version-update:semver-minor"]

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    labels:
      - "dependencies"
      - "ci"
```

## Finding Reviewers

```bash
git log --format='%aN' | sort | uniq -c | sort -rn | head -5
# Use the top contributors as reviewers
# Use GitHub username (not git name): check git log --format='%ae' for emails
```

## Activate After Commit

Dependabot auto-activates once `.github/dependabot.yml` is pushed to the default branch.
Verify at: `https://github.com/<org>/<repo>/network/updates`
