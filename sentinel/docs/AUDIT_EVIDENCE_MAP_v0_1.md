# GxP Deviation Risk Sentinel  
## Audit Evidence Map — v0.1

Purpose:
This document maps the GxP Deviation Risk Sentinel design controls to enforcement mechanisms and
verifiable evidence artifacts. It demonstrates inspection ready traceability
without storing GMP data or influencing product decisions.

This system is advisory, read-only, and metadata-only.

---

## System Classification

- System Type: Advisory Monitoring System
- Product Impact: None (non-product-impacting)
- Data Class: Metadata only
- Scope: Deviation risk signaling, not deviation management
- Validation Status: Portfolio / design demonstration (not production validated as of Jan 2026)

---

## Control → Mechanism → Evidence Mapping

---

### CONTROL 1: Prevent ingestion of GMP values or narratives

**Risk Addressed**  
Uncontrolled storage of GMP data, free text, or raw identifiers.

**Enforcement Mechanism**
- JSON Schema (`event_schema_v0_1.json`)
- Prohibited field tripwire (`prohibited_fields_v0_1.json`)
- Hard reject at ingestion

**Evidence Artifacts**
- `audit_log.jsonl`
  - `INGEST_REJECT`
  - `rejection_reason_code = PROHIBITED_DATA_DETECTED`
- Test vectors:
  - `event_reject_gmp_value.json`
  - `event_reject_free_text.json`
  - `event_reject_raw_ids.json`

---

### CONTROL 2: Ensure deterministic ingestion decisions

**Risk Addressed**  
Non-repeatable or subjective ingestion logic.

**Enforcement Mechanism**
- Static JSON Schema validation
- Deterministic rule paths
- No ML or probabilistic logic

**Evidence Artifacts**
- `audit_log.jsonl`
  - `INGEST_ACCEPT`
  - `INGEST_REJECT`
- Test vector:
  - `event_valid_minimal.json`

---

### CONTROL 3: Enforce read-only integration boundary

**Risk Addressed**  
Unauthorized writes back into DBR/MES systems.

**Enforcement Mechanism**
- One-way ingestion only
- No outbound connectors to source systems
- No mutation APIs

**Evidence Artifacts**
- Architecture diagram (`architecture_v0_1.md`)
- Absence of write paths in code
- Alert-only output to consumers

---

### CONTROL 4: Deterministic deviation risk signaling

**Risk Addressed**  
Inconsistent or undocumented deviation alerts.

**Enforcement Mechanism**
- YAML-based rule definitions (`rules_v0_1.yaml`)
- Fixed severity and risk codes
- Explicit routing configuration

**Evidence Artifacts**
- `audit_log.jsonl`
  - `RULE_MATCH`
  - `RULE_NO_MATCH`
- Alerts:
  - `alerts.jsonl`
- Test vectors:
  - `event_submit_rejected_missing.json`
  - `event_step_opened_overdue.json`

---

### CONTROL 5: Alert suppression to prevent alert fatigue

**Risk Addressed**  
Repeated alerts masking true deviation risk.

**Enforcement Mechanism**
- Time-based suppression window
- Deterministic suppression key

**Evidence Artifacts**
- `suppression_state_v0_1.json`
- `audit_log.jsonl`
  - `ALERT_SUPPRESSED`
- Console output:
  - `ALERT SUPPRESSED 🧱`

---

### CONTROL 6: Correlation-based timeout detection

**Risk Addressed**  
Missed deviations due to incomplete workflows.

**Enforcement Mechanism**
- CorrelationStore (metadata-only)
- Time-threshold evaluation
- Optional sweep-based evaluation

**Evidence Artifacts**
- `correlation_state_v0_1.json`
- `audit_log.jsonl`
  - `CORRELATION_HIT`
- Alerts:
  - `DR-002 STEP_TIMEOUT`

---

### CONTROL 7: Routing enforcement and segregation of responsibility

**Risk Addressed**  
Alerts delivered to unauthorized or unintended consumers.

**Enforcement Mechanism**
- Consumer allowlist (`consumers_allowlist_v0_1.json`)
- Routing normalization before alert emission

**Evidence Artifacts**
- `audit_log.jsonl`
  - `ROUTING_APPLIED`
  - `ROUTING_NOT_ALLOWED` (if triggered)

---

### CONTROL 8: Append-only audit trail

**Risk Addressed**  
Audit log tampering or loss of traceability.

**Enforcement Mechanism**
- Append-only JSONL logs
- No update or delete operations
- Minimal, immutable records

**Evidence Artifacts**
- `audit_log.jsonl`
- Log record types:
  - `INGEST_ACCEPT`
  - `INGEST_REJECT`
  - `RULE_MATCH`
  - `ALERT_BUILT`
  - `ALERT_PERSISTED`
  - `INTERNAL_ERROR`

---

## Summary

This system demonstrates:
- Governance-first design
- Strong data minimization
- Deterministic behavior
- Inspection-grade traceability
- Clear separation between monitoring and quality decisions

Quality ownership, deviation initiation, and batch disposition remain
outside the Sentinel by design.

---

## Version History

- v0.1 — Initial audit evidence mapping (portfolio implementation)
