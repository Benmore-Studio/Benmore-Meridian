# README.md Template and Section Guide

## Required Sections (in order)

### 1. Header
```markdown
# Project Name

> One-sentence tagline describing what it does and who it's for.

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Version](https://img.shields.io/badge/version-1.4.0-green.svg)
![CI](https://github.com/org/repo/actions/workflows/ci.yml/badge.svg)
```

### 2. Features
3-6 bullet points. Be concrete, not generic.
```markdown
## Features

- **Offline-first mobile** — cattle records sync in the background; works in poor connectivity
- **Multi-tenant operations** — each ranching operation sees only its own data
- **API docs** — Swagger UI at `/api/docs/`, ReDoc at `/api/redoc/`
```

### 3. Tech Stack
```markdown
## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.2 + DRF 3.15 |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Mobile | React Native 0.76 + Expo 52 |
| Auth | JWT (SimpleJWT) |
| Async | Celery 5 + Redis |
| Payments | Stripe |
```

### 4. Quick Start

Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_protocols
python manage.py runserver
```

Mobile:
```bash
cd mobile
npm install
npm start   # then press 'i' for iOS or 'a' for Android
```

### 5. API Documentation
```markdown
## API Documentation

Interactive API docs are available when the backend is running:

- **Swagger UI** — http://localhost:8000/api/docs/
- **ReDoc** — http://localhost:8000/api/redoc/
- **OpenAPI schema** — http://localhost:8000/api/schema/
```

### 6. Architecture (optional but valued)
Link to CLAUDE.md or include a trimmed diagram.

### 7. Contributing
```markdown
## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Commit with conventional commits (`feat:`, `fix:`, `chore:`)
4. Open a pull request
```

### 8. License
```markdown
## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
```

## Writing Tips

- Use present tense ("manages", not "will manage")
- Every code block must be copy-pasteable
- Badge URLs: replace `org/repo` with actual GitHub slug from `git remote -v`
- Don't duplicate CLAUDE.md — link to it for deep technical detail
