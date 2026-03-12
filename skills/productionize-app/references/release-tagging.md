# Git Release Tagging Guide

## Tag Convention
Use annotated tags with `v` prefix: `v1.4.0`, `v1.4.1`, `v2.0.0`

## Create and Push a Release Tag

```bash
# Read version from changelog or package.json
VERSION=$(cat mobile/package.json | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])")
echo "Tagging v$VERSION"

# Create annotated tag
git tag -a "v$VERSION" -m "Release v$VERSION

$(sed -n "/## \[$VERSION\]/,/## \[/p" CHANGELOG.md | head -30)"

# Push tag
git push origin "v$VERSION"
```

## Create GitHub Release

```bash
# Extract release notes from CHANGELOG
VERSION=$(cat mobile/package.json | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])")

# Use gh CLI
gh release create "v$VERSION" \
  --title "v$VERSION" \
  --notes "$(sed -n "/## \[$VERSION\]/,/## \[/p" CHANGELOG.md | sed '1d;$d')" \
  --latest
```

## Verify

```bash
git tag --sort=-version:refname | head -3
gh release list | head -3
```

## Tag Naming Rules

| Pattern | Use for |
|---------|---------|
| `v1.4.0` | Production release |
| `v1.4.0-beta.1` | Pre-release / beta |
| `v1.4.0-rc.1` | Release candidate |

## GitHub Release Checklist

- [ ] CHANGELOG.md has an entry for this version (not just [Unreleased])
- [ ] version in `package.json` matches tag
- [ ] All CI checks pass on main
- [ ] Tag is annotated (not lightweight)
- [ ] Release marked as `--latest` on GitHub
