# **GxP Deviation Risk Sentinel**

**Version:** v0.1  
**Status:** Design-complete MVP (Phases 1–5)  
**Classification:** Advisory, read-only, metadata-only monitoring system

**Quickstart:** [Quickstart](https://github.com/BWallace1208/gxp-deviation-risk-sentinel/blob/main/docs/QUICKSTART.md)

## **Overview**

The *GxP Deviation Risk Sentinel* is a vendor-neutral, read-only monitoring system designed to detect potential deviation risk signals from Digital Batch Records (DBR), MES, or document control systems without ingesting or storing GMP data.

The Sentinel operates upstream of quality decisions.It does not manage deviations, influence batch execution, or write back to source systems.

Its sole purpose is to:

* Detect risk conditions deterministically  
* Alert appropriate stakeholders  
* Preserve an immutable audit trail

## **Core Design Principles**

* Metadata-only ingestion (no GMP values, narratives, or calculations)  
* Read-only integration boundary  
* Deterministic logic only (no ML, no scoring)  
* Advisory alerts, not control actions  
* Append-only audit evidence  
* Clear separation between monitoring and quality decisions

Interpretation and disposition remain with QA and Operations.

## **Phase Summary**

### 

### *Phase 1: System Definition & Boundaries*

**Goal:** Define what the Sentinel is, what it is not, and where it stops.

**Delivered**

* System purpose and scope definition  
* Explicit non-product-impacting classification  
* Read-only architecture (no write paths back to DBR/MES)  
* Metadata-only data contract  
* Architecture diagram proving one-way flow

**Outcome**  
A defensible system boundary aligned with inspection readiness and GxP expectations.

### *Phase 2: Data Contracts & Governance*

**Goal:** Lock down schemas and control surfaces before any logic.

**Delivered**

* Event schema (`event_schema_v0_1.json`)  
* Alert schema (`alert_schema_v0_1.json`)  
* Prohibited data tripwire configuration  
* Risk code catalog  
* Deterministic field requirements

**Outcome**  
Strong data minimization, schema-first enforcement, and audit-ready contracts.

### *Phase 3: Audit, Suppression & Correlation*

**Goal:** Add inspection-grade behavior and evidence.

**Delivered**

* Append-only audit logging (JSONL)  
* Explicit audit record types (ingest, rules, alerts, errors)  
* Time-based suppression to reduce alert fatigue  
* Metadata-only correlation state  
* Deterministic timeout correlation logic  
* Correlation pruning and state hygiene  
* Test vectors demonstrating expected outcomes

**Outcome**  
A system that is traceable, reproducible, and defensible under inspection.

### *Phase 4: Sentinel Core (Design complete proof of concept)*

**Goal:** Ingest → evaluate → alert → audit.

**Delivered**

* Ingestion gate with schema validation and tripwire rejection  
* Rules engine with versioned YAML rules  
* Deterministic rule matching (risk code \+ severity)  
* Advisory alert creation (`NEW` state)  
* Immutable alert persistence  
* Repeatable local execution with test vectors

**Outcome**  
A working Sentinel Core that demonstrates real operational behavior without expanding GxP risk.

### *Phase 5: Dashboard & Notification Design (Design Concept Only)*

**Goal:** Make alerts usable in a DOC-style workflow without adding risk.

**Delivered (Design Only)**

* Read-only alert queue concept  
* Filterable by area, severity, risk code, product, age  
* Computed SLA timers (not stored)  
* Minimal acknowledgement model (optional)  
* Summary-only notifications (email / Teams style)  
* Time-based escalation for CRITICAL alerts  
* Explicit prohibition of interpretation, enrichment, or execution logic

**Outcome**  
A clear operational path forward that preserves system boundaries and audit integrity.

## **What This System Is**

* A monitoring and signaling system  
* A design-first, governance-first implementation  
* A portfolio-grade demonstration of regulated system thinking  
* A foundation for site-specific implementation

## **What This System Is Not**

* Not a deviation management system  
* Not a batch review system  
* Not a control or execution platform  
* Not a validated production deployment  
* Not a source of GMP truth  
* 

## **Evidence & Traceability**

* All enforcement is deterministic and inspectable  
* All outputs are append-only  
* All decisions are explainable from artifacts  
* No hidden state or opaque logic

*Key artifacts:*

* `schemas/`  
* `rules/`  
* `engine/`  
* `docs/AUDIT_EVIDENCE_MAP_v0_1.md`  
* `docs/PHASE_5_DASHBOARD_NOTIFICATION_DESIGN_v0_1.md`

