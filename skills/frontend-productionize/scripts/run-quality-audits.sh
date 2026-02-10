#!/bin/bash
# Run parallel quality audits (ESLint, TypeScript, Security)

set -e

OUTPUT_DIR="${1:-.productionization}"
mkdir -p "$OUTPUT_DIR"

echo "🔍 Running quality audits in parallel..."
echo "Output directory: $OUTPUT_DIR"
echo ""

# Function to run ESLint audit
run_eslint_audit() {
  echo "[ESLint] Starting audit..."
  if [ -f .eslintrc.json ] || [ -f .eslintrc.js ] || [ -f eslint.config.js ]; then
    npx eslint . --max-warnings 0 > "$OUTPUT_DIR/eslint-report.txt" 2>&1 || true
    ERRORS=$(grep -c "error" "$OUTPUT_DIR/eslint-report.txt" || echo "0")
    WARNINGS=$(grep -c "warning" "$OUTPUT_DIR/eslint-report.txt" || echo "0")
    echo "[ESLint] Complete: $ERRORS errors, $WARNINGS warnings"
  else
    echo "[ESLint] No ESLint config found - skipping"
    echo "No ESLint config found" > "$OUTPUT_DIR/eslint-report.txt"
  fi
}

# Function to run TypeScript audit
run_typescript_audit() {
  echo "[TypeScript] Starting audit..."
  if [ -f tsconfig.json ]; then
    npx tsc --noEmit > "$OUTPUT_DIR/typescript-report.txt" 2>&1 || true
    ERRORS=$(grep -c "error TS" "$OUTPUT_DIR/typescript-report.txt" || echo "0")
    echo "[TypeScript] Complete: $ERRORS type errors"
  else
    echo "[TypeScript] No tsconfig.json found - skipping"
    echo "No tsconfig.json found" > "$OUTPUT_DIR/typescript-report.txt"
  fi
}

# Function to run security audit
run_security_audit() {
  echo "[Security] Starting audit..."

  # Check for exposed secrets in source code
  {
    echo "=== Exposed Secrets Check ==="
    # Check if rg is available, fallback to grep
    if command -v rg &> /dev/null; then
      rg -i "PRIVATE_KEY|SECRET_KEY|API_KEY|PASSWORD" \
        --type-add 'tsx:*.tsx' --type-add 'jsx:*.jsx' \
        --type ts --type tsx --type js --type jsx \
        src/ 2>/dev/null | grep -v ".env" | grep -v "process.env" || echo "No secrets found"
    else
      grep -r -i "PRIVATE_KEY\|SECRET_KEY\|API_KEY\|PASSWORD" src/ 2>/dev/null | \
        grep -v ".env" | grep -v "process.env" || echo "No secrets found"
    fi

    echo ""
    echo "=== Dependency Vulnerabilities ==="
    if command -v jq &> /dev/null; then
      npm audit --json 2>/dev/null | jq -r '
        if .vulnerabilities then
          "Critical: " + (.vulnerabilities.critical // 0 | tostring) + "\n" +
          "High: " + (.vulnerabilities.high // 0 | tostring) + "\n" +
          "Moderate: " + (.vulnerabilities.moderate // 0 | tostring) + "\n" +
          "Low: " + (.vulnerabilities.low // 0 | tostring)
        else
          "No vulnerabilities found"
        end
      ' || echo "npm audit not available"
    else
      npm audit 2>/dev/null || echo "npm audit not available (jq not installed)"
    fi
  } > "$OUTPUT_DIR/security-report.txt"

  echo "[Security] Complete"
}

# Run all audits in parallel
run_eslint_audit &
PID_ESLINT=$!

run_typescript_audit &
PID_TYPESCRIPT=$!

run_security_audit &
PID_SECURITY=$!

# Wait for all to complete
wait $PID_ESLINT
wait $PID_TYPESCRIPT
wait $PID_SECURITY

echo ""
echo "✅ All quality audits complete!"
echo "Reports saved to: $OUTPUT_DIR/"
echo "  - eslint-report.txt"
echo "  - typescript-report.txt"
echo "  - security-report.txt"
exit 0
