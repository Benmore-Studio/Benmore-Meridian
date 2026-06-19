# bm v1.10.0 Release Hardening

This note summarizes the public-release split for `bm` and is intended to be copied into
PR descriptions or review comments.

## Release Flow

```mermaid
flowchart LR
    dev[Local changes] --> ci[CI gates]
    ci --> lint[Ruff format + lint]
    ci --> types[mypy + basedpyright]
    ci --> tests[pytest + schema smoke]
    ci --> rust[Cargo tests]
    ci --> build[sdist + native maturin wheels]
    build --> tag[v1.10.0 tag]
    tag --> pypi[Trusted PyPI publish]
    tag --> gh[GitHub Release]
    gh --> skills[skills.sh index refresh]
```

## PR Split

```mermaid
flowchart TD
    A[Public release hardening] --> B[CLI usability]
    A --> C[Global skill context]
    A --> D[Release pipeline]
    A --> E[Compliance docs]

    B --> B1[bm uninstall]
    B --> B2[bm suggest --install --cache --dry-run]
    B --> B3[JSON stdout contracts]

    C --> C1[Category-aware matcher]
    C --> C2[bm context --global]
    C --> C3[HIPAA/SOC2/security discovery signals]

    D --> D1[Ruff/mypy/basedpyright/pytest]
    D --> D2[Cargo tests]
    D --> D3[maturin native wheels]
    D --> D4[PyPI + GitHub release jobs]

    E --> E1[Code of Conduct]
    E --> E2[Security policy]
    E --> E3[Authors + Notice]
    E --> E4[skills.sh.json]
```

## Native Wheel Pipeline

```mermaid
sequenceDiagram
    participant Tag as git tag v1.10.0
    participant CI as GitHub Actions
    participant Rust as Cargo/PyO3
    participant PyPI as PyPI
    participant GH as GitHub Release

    Tag->>CI: trigger release workflow
    CI->>CI: run quality gates on Python 3.11/3.12 and Linux/macOS/Windows
    CI->>Rust: cargo test native/Cargo.toml
    CI->>Rust: maturin build --release --out dist
    Rust-->>CI: platform native wheels
    CI->>CI: uv build --sdist
    CI->>PyPI: uv publish dist/*
    CI->>GH: gh release create with all artifacts
```

## Reviewer Checklist

- CLI commands remain backward compatible.
- `--json` commands emit machine-readable JSON only on stdout.
- New warning/error text goes to stderr or Rich output only.
- `bm uninstall` only removes bm-managed installs and preserves external skills.
- `bm context --global` exposes the full skill catalog without installing everything.
- Security/compliance skills are discoverable from HIPAA, SOC 2, PHI, audit, MFA, auth, and tenant-isolation project signals.
- Release tags build an sdist and native wheels before publishing.
