# Ingestion Decision Flow (v0.1)

## Purpose
This document defines the end-to-end decision flow for ingesting metadata events into the GxP Deviation Risk Sentinel. The flow is designed to be deterministic, audit-ready, and defensively prevents capture or persistence of GMP process values.

## Core Principles
- Strict allow-list event schema validation
- Prohibited-field tripwires (deny-list) as a second defensive layer
- Deterministic rules evaluation (metadata-only)
- Minimal logging on rejections (no payload persistence)
- Append-only audit log of Sentinel actions

## Decision Flow (Mermaid)

```mermaid
flowchart TD

    A[Event Received] --> B{Event Schema Valid?<br/>(allow-list)}
    B -- No --> R1[REJECT: SCHEMA_INVALID<br/>Log minimal rejection metadata]
    B -- Yes --> C{Tripwires Clear?<br/>(deny-list)}
    C -- No --> R2[REJECT: PROHIBITED_DATA_DETECTED<br/>Log minimal rejection metadata]
    C -- Yes --> D[Normalize Event<br/>(standard event shape)]
    D --> E[Evaluate Rules<br/>(deterministic)]
    E --> F{Rule Match?}
    F -- No --> N1[NO ALERT<br/>Log evaluation outcome]
    F -- Yes --> G[Create Advisory Alert<br/>(metadata-only)]
    G --> H[Route Alert<br/>(DOC / Area Mgmt;<br/>QA for High/Critical)]
    H --> I[Append-only Audit Log<br/>(alert created + routing)]
```

[Event Received]
      |
      v
{Schema Valid? (allow-list)}
   |Yes                    |No
   v                       v
{Tripwires Clear?}     [REJECT: SCHEMA_INVALID]
   |Yes      |No            |
   v         v              v
[Normalize] [REJECT: PROHIBITED_DATA_DETECTED]
   |              (log minimal metadata only)
   v
[Evaluate Rules (deterministic)]
   |
   v
{Rule Match?}
   |Yes                    |No
   v                       v
[Create Advisory Alert]   [NO ALERT]
   |                       (log evaluation outcome)
   v
[Route Alert]
   |
   v
[Append-only Audit Log]


**Rejection Logging (Minimal)**

When rejecting an event, log only:
-rejection_reason_code
-rejection_reason_text (short)
-event_id (if present)
-source_system (if present)
-event_timestamp (if present)
-received_at (server timestamp)

**Do not store or log the rejected payload body.**

**Evaluation Logging (Matched/Not Matched)**
For accepted events, log:
-event_id
-normalized_event_type
-evaluated_rule_ids (or rule set version)
-match outcomes (matched/not matched)
-suppression outcome (if duplicate suppression applies)
-alert_id (if an alert is created)

**Alert Creation Rules**
-Alerts created by the Sentinel must:
-conform to alert_schema_v0_1.json
-contain metadata only (no GMP values or narratives)
-include rule_id and rule_version
-include risk_code and severity
-include contributing event_refs (event IDs only)

**Routing Logic (Advisory)**
Default routing:
LOW/MEDIUM: DOC + Area Management
HIGH/CRITICAL: DOC + Area Management + QA

**Note:** routing is advisory; quality decisions remain outside the Sentinel.