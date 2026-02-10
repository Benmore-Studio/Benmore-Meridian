# Security Audit Report

**Project**: [PROJECT_NAME]
**Audit Date**: [DATE]
**Total Vulnerabilities**: [TOTAL_COUNT]
**Critical/High**: [HIGH_COUNT] | **Moderate**: [MODERATE_COUNT] | **Low**: [LOW_COUNT]

---

## Executive Summary

[Brief overview of security posture and key findings]

**Risk Level**: [CRITICAL | HIGH | MODERATE | LOW]

---

## Vulnerabilities Found

### HIGH SEVERITY ([COUNT])

#### [#N] [VULNERABILITY_NAME]

**CVE**: [CVE_ID or N/A]
**Package**: [PACKAGE_NAME] [VERSION_CURRENT] → [VERSION_FIXED]
**CVSS Score**: [SCORE]

**Vulnerability Description**:
[Clear explanation of what the vulnerability is]

**Attack Vector**:
```
[Code example or attack scenario]
```

**Business Impact**:
- [Impact point 1]
- [Impact point 2]
- [Impact point 3]

**Remediation**:
[How to fix - upgrade command, override config, or alternative approach]

---

### MODERATE SEVERITY ([COUNT])

[Same structure as High Severity]

---

### LOW SEVERITY ([COUNT])

[Same structure as High Severity]

---

## Remediation Summary

| Vulnerability | Severity | Fix Method | Status |
|---------------|----------|------------|--------|
| [Name] | [HIGH/MOD/LOW] | [Upgrade/Override/Alternative] | [❌ Open / ✅ Fixed] |

---

## Compliance Impact

**Before Fixes**:
- [ ] OWASP Top 10 compliance
- [ ] PCI-DSS compliance
- [ ] SOC 2 audit readiness

**After Fixes**:
- [X] OWASP Top 10 compliant
- [X] PCI-DSS compliant
- [X] SOC 2 audit-ready

---

## Next Steps

1. **Immediate Actions** (within 24 hours):
   - Fix all HIGH severity issues
   - Test fixes in staging environment

2. **Short-term** (within 1 week):
   - Fix all MODERATE severity issues
   - Update security documentation

3. **Long-term** (ongoing):
   - Fix LOW severity issues
   - Enable automated security scanning
   - Schedule quarterly audits

---

## Recommendations

### Automated Scanning
- Enable Dependabot auto-merge for patch versions
- Integrate security scanning in CI/CD pipeline
- Set up alerts for new CVEs

### Security Hardening
- Implement WAF rules for common attacks
- Add rate limiting to prevent DoS
- Enable security headers (CSP, HSTS, etc.)

### Monitoring
- Set up logging for security events
- Configure alerts for unusual patterns
- Regular penetration testing

---

**Prepared by**: Claude Sonnet 4.5
**Next Review**: [DATE + 90 days]
