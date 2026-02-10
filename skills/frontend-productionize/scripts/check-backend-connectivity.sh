#!/bin/bash
# Check if Django backend is reachable and OpenAPI schema is available

set -e

BACKEND_URL="${1:-http://localhost:8000}"
SCHEMA_PATH="${2:-/api/schema/}"
SCHEMA_URL="${BACKEND_URL}${SCHEMA_PATH}"

echo "🔍 Checking backend connectivity..."
echo "Backend URL: $BACKEND_URL"
echo "Schema URL: $SCHEMA_URL"
echo ""

# Check backend is reachable
if ! curl -sf --max-time 5 "$BACKEND_URL" > /dev/null 2>&1; then
  echo "❌ Backend unreachable at $BACKEND_URL"
  echo ""
  echo "Options:"
  echo "  1. Start Django backend: python manage.py runserver"
  echo "  2. Check backend URL is correct"
  echo "  3. Check backend is accessible from this machine"
  exit 1
fi

echo "✅ Backend is reachable"

# Check schema endpoint exists
if ! curl -sf --max-time 5 "$SCHEMA_URL" > /dev/null 2>&1; then
  echo "❌ Schema endpoint not found at $SCHEMA_URL"
  echo ""
  echo "Make sure drf-spectacular is installed and configured:"
  echo "  1. pip install drf-spectacular"
  echo "  2. Add 'drf_spectacular' to INSTALLED_APPS"
  echo "  3. Add schema URL to urls.py:"
  echo "     path('api/schema/', SpectacularAPIView.as_view(), name='schema')"
  exit 1
fi

echo "✅ Schema endpoint is accessible"

# Check schema returns valid OpenAPI spec
CONTENT_TYPE=$(curl -sf --max-time 5 -I "$SCHEMA_URL" | grep -i "content-type" | awk '{print $2}' | tr -d '\r')

if [[ "$CONTENT_TYPE" == *"yaml"* ]] || [[ "$CONTENT_TYPE" == *"json"* ]]; then
  echo "✅ Schema returns valid OpenAPI spec (Content-Type: $CONTENT_TYPE)"
else
  echo "⚠️  Unexpected Content-Type: $CONTENT_TYPE"
  echo "Expected: application/vnd.oai.openapi+json or application/yaml"
fi

echo ""
echo "🎉 Backend connectivity check passed!"
exit 0
