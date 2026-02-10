#!/bin/bash
# Generate TypeScript types from Django OpenAPI schema

set -e

SCHEMA_URL="${API_SCHEMA_URL:-http://localhost:8000/api/schema/}"
OUTPUT_FILE="src/api/schema.d.ts"

echo "🔍 Generating TypeScript types from OpenAPI schema..."
echo "Schema URL: $SCHEMA_URL"
echo "Output: $OUTPUT_FILE"
echo ""

# Check if backend is reachable
if ! curl -sf --max-time 5 "$SCHEMA_URL" > /dev/null 2>&1; then
  echo "⚠️  Backend unreachable at $SCHEMA_URL"

  if [ -f "$OUTPUT_FILE" ]; then
    echo "✅ Using cached $OUTPUT_FILE"
    exit 0
  else
    echo "❌ No cached schema found. Cannot proceed."
    echo ""
    echo "Options:"
    echo "  1. Start backend: python manage.py runserver"
    echo "  2. Run this script again when backend is available"
    exit 1
  fi
fi

# Generate types
echo "⚙️  Generating types..."
npx openapi-typescript "$SCHEMA_URL" -o "$OUTPUT_FILE"

# Check for changes
if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
  if git diff --quiet "$OUTPUT_FILE" 2>/dev/null; then
    echo "✅ Schema is up to date"
  else
    echo "⚠️  Schema has changed! Review the diff:"
    git diff "$OUTPUT_FILE" | head -n 50
  fi
fi

echo ""
echo "✅ API types generated successfully"
exit 0
