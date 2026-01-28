# Test Vectors — Expected Outcomes (v0.1)

Goal: Demonstrate deterministic, metadata-only behavior with audit logging.
This document defines the expected system behavior for each test vector.

---

## How to run

From the repository root:

```powershell
python -m sentinel.app .\sentinel\tests\test_vectors\<FILE>.json
```

---

## Evidence locations (append-only)

- Alerts:
  ```
  .\sentinel\storage\alerts.jsonl
  ```

- Audit log:
  ```
  .\sentinel\storage\audit_log.jsonl
  ```

Helpful inspection commands:

```powershell
Get-Content .\sentinel\storage\alerts.jsonl | Select-Object -Last 1
Get-Content .\sentinel\storage\audit_log.jsonl | Select-Object -Last 10
```

---

## Test Vectors

### 1) event_valid_minimal.json

Purpose:
- Validate minimal, schema-compliant ingestion
- Confirm no alert is generated

Expected:
- Console: `ACCEPTED ✅`
- Console: `NO ALERT 💤`
- Audit:
  - `INGEST_ACCEPT`
  - Rule evaluation recorded with no match

---

### 2) event_submit_rejected_missing.json

Purpose:
- Detect submission rejected due to missing required entry

Expected:
- Console: `ACCEPTED ✅`
- Console: `ALERT EMITTED 🚨`
- Alert:
  - `risk_code`: DR-001
  - `severity`: HIGH
- Audit:
  - `RULE_MATCH`
  - `ALERT_BUILT`
  - `ALERT_PERSISTED`

---

### 3) event_step_opened_overdue.json

Purpose:
- Trigger step timeout logic (R-002)

Expected:
- Console: `ACCEPTED ✅`
- Console outcome depends on suppression state:
  - `ALERT EMITTED 🚨` (first occurrence)
  - or `ALERT SUPPRESSED 🧱` (within suppression window)
- Alert (when emitted):
  - `risk_code`: DR-002
  - `severity`: CRITICAL

---

### 4) event_step_completed_on_time.json

Purpose:
- Validate correlation logic where completion occurs within threshold

Expected:
- Console: `ACCEPTED ✅`
- Console: `NO ALERT 💤`
- Correlation state updated
- No alert generated

---

### 5) event_step_completed_wrong_batch.json

Purpose:
- Validate correlation pairing rules (batch_token mismatch)

Expected:
- Console: `ACCEPTED ✅`
- Console: `NO ALERT 💤`
- Demonstrates that incorrect correlation does not satisfy timeout rule

---

## Prohibited-data / Tripwire Rejection Vectors

These tests demonstrate strict metadata-only enforcement.
All must reject at ingestion.

---

### 6) event_tripwire_should_reject.json

Expected:
- Console: `REJECTED ❌`
- Rejection reason indicates prohibited-field tripwire

---

### 7) event_reject_gmp_value.json

Expected:
- Console: `REJECTED ❌`
- Rejection reason indicates GMP value capture is prohibited

---

### 8) event_reject_free_text.json

Expected:
- Console: `REJECTED ❌`
- Rejection reason indicates narrative / free-text is prohibited

---

### 9) event_reject_raw_ids.json

Expected:
- Console: `REJECTED ❌`
- Rejection reason indicates raw identifier class is prohibited

---

## Reset state between test runs (optional)

To run tests without suppression or correlation carryover, delete:

```
.\sentinel\storage\alerts.jsonl
.\sentinel\storage\audit_log.jsonl
.\sentinel\storage\suppression_state_v0_1.json
.\sentinel\storage\correlation_state_v0_1.json
```

---

## Notes

- All behavior is deterministic.
- No payload bodies or GMP values are persisted.
- All persistence is append-only.
- Alerts are advisory only; quality decisions remain external to the Sentinel.


