#!/bin/bash

################################################################################
# Dependabot Enablement Script - benmore-studio Organization
################################################################################
#
# This script enables FREE GitHub Dependabot features for all repositories
# in the benmore-studio organization.
#
# What this enables (100% FREE):
# ✅ Dependabot vulnerability alerts - Detects vulnerable dependencies
# ✅ Dependabot security updates - Auto-creates PRs to fix vulnerabilities
#
# Requirements:
# - GitHub CLI (gh) installed and authenticated
# - Admin access to the organization repositories
#
# Usage:
#   ./enable_dependabot_benmore_studio.sh
#
################################################################################

set -e  # Exit on any error

# Configuration
ORG="benmore-studio"
REPOS=("propurti_prototype" "propurti_backend" "cattle_ranch_software" "BEN130" "nil_platform" "House_service_pass")

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=================================="
echo "Dependabot Enablement Script"
echo "Organization: $ORG"
echo "=================================="
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}ERROR: GitHub CLI (gh) is not installed${NC}"
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}ERROR: Not authenticated with GitHub CLI${NC}"
    echo "Run: gh auth login"
    exit 1
fi

echo -e "${GREEN}✓${NC} GitHub CLI is installed and authenticated"
echo ""

# Enable Dependabot for each repository
for repo in "${REPOS[@]}"; do
    echo "Processing: $repo"
    echo "-------------------"

    # Enable vulnerability alerts (Dependabot alerts)
    echo -n "  • Enabling vulnerability alerts... "
    if gh api --method PUT "/repos/$ORG/$repo/vulnerability-alerts" \
        -H "Accept: application/vnd.github+json" &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠ Already enabled or permission denied${NC}"
    fi

    # Enable automated security fixes (Dependabot security updates)
    echo -n "  • Enabling security updates... "
    if gh api --method PUT "/repos/$ORG/$repo/automated-security-fixes" \
        -H "Accept: application/vnd.github+json" &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠ Already enabled or permission denied${NC}"
    fi

    echo ""
done

# Wait for changes to propagate
echo "Waiting for GitHub to process changes..."
sleep 5
echo ""

# Verify configuration
echo "=================================="
echo "Verification Results"
echo "=================================="
echo ""

for repo in "${REPOS[@]}"; do
    echo -n "$repo: "
    status=$(gh api "/repos/$ORG/$repo" --jq '.security_and_analysis.dependabot_security_updates.status' 2>/dev/null || echo "unknown")

    if [ "$status" = "enabled" ]; then
        echo -e "${GREEN}✓ ENABLED${NC}"
    elif [ "$status" = "disabled" ]; then
        echo -e "${RED}✗ DISABLED${NC}"
    else
        echo -e "${YELLOW}? UNKNOWN${NC}"
    fi
done

echo ""
echo "=================================="
echo "Next Steps for Vanta Compliance"
echo "=================================="
echo ""
echo "1. Grant Vanta permission to read Dependabot alerts:"
echo "   → Go to: https://github.com/organizations/$ORG/settings/installations"
echo "   → Find 'Vanta' and click 'Configure'"
echo "   → Ensure 'Dependabot alerts' permission is enabled"
echo ""
echo "2. Wait 10-15 minutes for changes to propagate"
echo ""
echo "3. Re-run the Vanta test"
echo ""
echo -e "${GREEN}Done!${NC}"
