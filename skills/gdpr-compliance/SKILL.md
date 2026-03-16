---
name: gdpr-compliance
description: Use when implementing privacy compliance features - GDPR consent management, data subject access requests (DSARs), data retention policies, right to erasure, data portability, or CCPA/FCRA consent tracking
context: fork
---

# GDPR & Privacy Compliance

Implement privacy compliance workflows for GDPR, CCPA, and FCRA in FastAPI + SQLAlchemy services.

## When to Use
- Adding consent collection/tracking
- Implementing DSAR (Data Subject Access Request) workflows
- Setting up automated data retention and purge policies
- Handling right-to-erasure (account deletion with CASCADE)
- Building compliance dashboards or audit exports
- Adding FCRA background-check disclosure consent

## Five Compliance Models

### 1. ConsentRecord - GDPR Art. 7
Immutable audit trail. Never update in place - revocation creates a new row.

```python
class ConsentRecord(Base):
    __tablename__ = "consent_records"
    __table_args__ = (Index("idx_consent_user", "user_id", "consent_type"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    consent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g. "gdpr_marketing_emails", "fcra_background_check_disclosure"
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**Rules:** Append-only, version-aware (policy update requires re-consent), forensic IP+UA.

### 2. DataSubjectRequest - GDPR Arts. 15-22
Track DSARs with 30-day SLA.

```python
class DataSubjectRequest(Base):
    __tablename__ = "data_subject_requests"
    __table_args__ = (
        CheckConstraint("request_type IN ('access','rectification','erasure','portability','restriction','objection')"),
        CheckConstraint("status IN ('pending','in_progress','completed','denied')"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    requestor_email: Mapped[str] = mapped_column(String(320), nullable=False)
    request_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_by: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**State machine:** `pending -> in_progress -> completed | denied`
**SLA query:** `WHERE status IN ('pending','in_progress') AND due_by < NOW()`

### 3. DataRetentionPolicy - GDPR Art. 5(1)(e)

```python
class DataRetentionPolicy(Base):
    __tablename__ = "data_retention_policies"

    tenant_id: Mapped[UUID | None] = mapped_column(nullable=True)  # NULL = platform-wide
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    retention_days: Mapped[int] = mapped_column(nullable=False)
    auto_purge: Mapped[bool] = mapped_column(Boolean, default=False)
    legal_basis: Mapped[str | None] = mapped_column(Text, nullable=True)
```

**Resolution:** Tenant-specific > platform-wide > hardcoded default.

### 4. IpAccessRule - SOC 2, GDPR Art. 32

```python
class IpAccessRule(Base):
    __tablename__ = "ip_access_rules"
    __table_args__ = (
        CheckConstraint("rule_type IN ('allow', 'block')"),
        Index("idx_ip_rules_tenant", "tenant_id"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(nullable=True)  # NULL = global
    cidr_range: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(10), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**Evaluation:** Block first -> allow rules -> default deny if allow rules exist.

### 5. MfaRecoveryCode - NIST SP 800-63B

```python
class MfaRecoveryCode(Base):
    __tablename__ = "mfa_recovery_codes"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    code_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**Rules:** Batch of 10, bcrypt hashed, single-use, CASCADE on user delete.

## Compliance Checklist for New Features

1. [ ] Collects personal data? -> Add consent record
2. [ ] Stores personal data? -> Define retention policy
3. [ ] Users can request data? -> DSAR export covers it
4. [ ] Users can delete account? -> CASCADE or explicit cleanup
5. [ ] Logs user activity? -> Audit trail with retention
6. [ ] Background checks? -> FCRA disclosure consent
7. [ ] Restricts access? -> IP rules or RBAC

## Right to Erasure Flow

```
User requests deletion
  -> Create DSAR (type=erasure)
  -> Verify identity
  -> Check legal holds (FCRA retention, litigation)
     -> Hold exists: deny with documented reason
     -> No hold: proceed
  -> CASCADE delete user record
     -> Removes: consent_records, mfa_recovery_codes, sessions
     -> Anonymizes: audit_logs (NULL user_id, keep event)
     -> Notifies: downstream services via Kafka
  -> Mark DSAR completed
  -> Emit audit: DATA_DELETED
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Updating consent in place | Append-only - new row for each change |
| No DSAR deadline | Always set `due_by = created_at + 30 days` |
| Hard-deleting audit logs | Anonymize (NULL user_id), keep event |
| Missing legal basis | Document GDPR Art. 6(1) ground per policy |
| Same version after policy update | Increment version - old consents invalid |
| No expiry on bounded consent | Set `expires_at` for FCRA annual renewals |
