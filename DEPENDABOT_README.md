# Dependabot Setup for Vanta Compliance

## What This Script Does

The `enable_dependabot.sh` script enables **FREE** GitHub security features for all repositories in your organization to pass Vanta's vulnerability scanning compliance test.

## Cost Breakdown

### ✅ FREE Features (What We Enable)

| Feature | Description | Cost |
|---------|-------------|------|
| **Dependabot Alerts** | Scans dependencies for known vulnerabilities | **FREE** |
| **Dependabot Security Updates** | Auto-creates PRs to fix vulnerable dependencies | **FREE** |
| **Dependabot Version Updates** | Auto-creates PRs to keep dependencies up-to-date | **FREE** |

### ❌ PAID Features (NOT Enabled)

| Feature | Description | Cost |
|---------|-------------|------|
| **GitHub Advanced Security (GHAS)** | Code scanning, advanced secret scanning, security overview | **$49/user/month** |
| **CodeQL Code Scanning** | Detects security vulnerabilities in your code | Part of GHAS |
| **Advanced Secret Scanning** | Detects secrets with validity checking | Part of GHAS |
| **Push Protection** | Blocks commits with secrets | Part of GHAS |

**Note:** Public repositories get all GitHub Advanced Security features for FREE. Only private repos require payment.

## Usage

### First Time Setup

1. **Install GitHub CLI** (if not already installed):
   ```bash
   brew install gh
   # or visit: https://cli.github.com/
   ```

2. **Authenticate with GitHub**:
   ```bash
   gh auth login
   ```

3. **Run the script**:
   ```bash
   ./enable_dependabot.sh
   ```

### Re-running for New Repositories

When you create new repositories, simply run the script again:

```bash
./enable_dependabot.sh
```

Update the `REPOS` array in the script to include any new repository names.

## Vanta Compliance Test

### Test Details

- **Test Name**: "Vulnerability scanning is enabled (GitHub)"
- **Pass Criteria**: At least ONE monitored repository has Dependabot enabled
- **Fail Criteria**: NO monitored repositories have Dependabot enabled

### Why the Test Was Failing

1. **API vs UI Mismatch**: Dependabot alerts existed but weren't properly registered via the API
2. **Missing Permissions**: Vanta couldn't read Dependabot status from GitHub
3. **Repo-Level Settings**: Features weren't explicitly enabled at the repository level

### Steps to Pass the Test

1. ✅ **Run the script** (Done!)
2. ⚠️  **Grant Vanta permissions**:
   - Go to: https://github.com/organizations/Patriot-Compliance-Systems/settings/installations
   - Find "Vanta" app
   - Click "Configure"
   - Ensure these permissions are enabled:
     - ✅ Dependabot alerts: Read-only
     - ✅ Vulnerability alerts: Read-only
     - ✅ Repository administration: Read-only
3. ⏳ **Wait 10-15 minutes** for GitHub's API cache to update
4. 🔄 **Re-run the test** in Vanta dashboard

## Verification

Check Dependabot status for all repos:

```bash
gh api /orgs/Patriot-Compliance-Systems/repos --paginate | \
  jq -r '.[] | "\(.name): \(.security_and_analysis.dependabot_security_updates.status)"'
```

Expected output:
```
Patriot_compliance: enabled
PCS_workforce: enabled
PCS_prod: enabled
pcs_backend: enabled
Audit_logs: enabled
```

## Troubleshooting

### Script fails with "permission denied"
- Ensure you have **admin access** to the organization
- Run `gh auth refresh -s admin:org,repo` to grant necessary scopes

### Vanta test still fails after running script
- Verify Vanta has read permissions (see step 2 above)
- Wait 15 minutes for GitHub's API cache
- Check if Vanta is monitoring all repositories

### "Already enabled" warnings
- This is normal! It means the feature was already enabled
- The script will still verify all settings

## Related Documentation

- [GitHub Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [Vanta GitHub Integration](https://www.vanta.com/integrations/github)
- [GitHub Advanced Security Pricing](https://docs.github.com/en/billing/managing-billing-for-github-advanced-security/about-billing-for-github-advanced-security)

## Current Repository Status

As of last run:

- ✅ Patriot_compliance: **Enabled**
- ✅ PCS_workforce: **Enabled**
- ✅ PCS_prod: **Enabled**
- ✅ pcs_backend: **Enabled**
- ✅ Audit_logs: **Enabled**

**Total Monthly Cost**: $0.00 (All free features)
