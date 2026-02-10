#!/bin/bash
# Scan for dependency vulnerabilities across multiple package managers
# Usage: ./scan_vulnerabilities.sh [output_format]
# output_format: json (default) or text

set -euo pipefail

OUTPUT_FORMAT="${1:-json}"
RESULTS_FILE="security_scan_results.json"

# Initialize results
echo "{" > "$RESULTS_FILE"
echo '  "scan_timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",' >> "$RESULTS_FILE"
echo '  "scans": {' >> "$RESULTS_FILE"

# Function to detect package manager
detect_package_manager() {
    if [ -f "package.json" ]; then
        if [ -f "pnpm-lock.yaml" ]; then
            echo "pnpm"
        elif [ -f "yarn.lock" ]; then
            echo "yarn"
        elif [ -f "package-lock.json" ]; then
            echo "npm"
        else
            echo "npm"
        fi
    elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
        if [ -f "poetry.lock" ]; then
            echo "poetry"
        else
            echo "pip"
        fi
    elif [ -f "Gemfile" ]; then
        echo "bundler"
    elif [ -f "go.mod" ]; then
        echo "go"
    elif [ -f "Cargo.toml" ]; then
        echo "cargo"
    else
        echo "unknown"
    fi
}

PKG_MANAGER=$(detect_package_manager)
echo "Detected package manager: $PKG_MANAGER" >&2

# Scan based on package manager
case "$PKG_MANAGER" in
    pnpm)
        echo '    "pnpm": {' >> "$RESULTS_FILE"
        if command -v pnpm &> /dev/null; then
            pnpm audit --json 2>/dev/null | jq -c '.' >> "$RESULTS_FILE" || echo '      "error": "pnpm audit failed"' >> "$RESULTS_FILE"
        else
            echo '      "error": "pnpm not installed"' >> "$RESULTS_FILE"
        fi
        echo '    },' >> "$RESULTS_FILE"
        ;;
    npm)
        echo '    "npm": {' >> "$RESULTS_FILE"
        if command -v npm &> /dev/null; then
            npm audit --json 2>/dev/null | jq -c '.' >> "$RESULTS_FILE" || echo '      "error": "npm audit failed"' >> "$RESULTS_FILE"
        else
            echo '      "error": "npm not installed"' >> "$RESULTS_FILE"
        fi
        echo '    },' >> "$RESULTS_FILE"
        ;;
    yarn)
        echo '    "yarn": {' >> "$RESULTS_FILE"
        if command -v yarn &> /dev/null; then
            yarn audit --json 2>/dev/null | jq -c '.' >> "$RESULTS_FILE" || echo '      "error": "yarn audit failed"' >> "$RESULTS_FILE"
        else
            echo '      "error": "yarn not installed"' >> "$RESULTS_FILE"
        fi
        echo '    },' >> "$RESULTS_FILE"
        ;;
    pip)
        echo '    "pip": {' >> "$RESULTS_FILE"
        if command -v pip &> /dev/null && command -v pip-audit &> /dev/null; then
            pip-audit --format json 2>/dev/null | jq -c '.' >> "$RESULTS_FILE" || echo '      "error": "pip-audit failed"' >> "$RESULTS_FILE"
        else
            echo '      "error": "pip-audit not installed (run: pip install pip-audit)"' >> "$RESULTS_FILE"
        fi
        echo '    },' >> "$RESULTS_FILE"
        ;;
    poetry)
        echo '    "poetry": {' >> "$RESULTS_FILE"
        if command -v poetry &> /dev/null; then
            poetry show --outdated --format json 2>/dev/null | jq -c '.' >> "$RESULTS_FILE" || echo '      "error": "poetry check failed"' >> "$RESULTS_FILE"
        else
            echo '      "error": "poetry not installed"' >> "$RESULTS_FILE"
        fi
        echo '    }' >> "$RESULTS_FILE"
        ;;
    *)
        echo '    "error": "Unknown or unsupported package manager"' >> "$RESULTS_FILE"
        ;;
esac

# Check for GitHub Dependabot alerts if gh CLI is available
if command -v gh &> /dev/null; then
    echo ',' >> "$RESULTS_FILE"
    echo '    "dependabot": {' >> "$RESULTS_FILE"
    gh api repos/:owner/:repo/dependabot/alerts?state=open 2>/dev/null | jq -c '.' >> "$RESULTS_FILE" || echo '      "error": "Failed to fetch Dependabot alerts"' >> "$RESULTS_FILE"
    echo '    }' >> "$RESULTS_FILE"
fi

echo '  }' >> "$RESULTS_FILE"
echo '}' >> "$RESULTS_FILE"

echo "Scan complete. Results saved to: $RESULTS_FILE" >&2
cat "$RESULTS_FILE"
