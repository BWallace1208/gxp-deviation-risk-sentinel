## **Dashboard & Notification Path (v0.1)**

### 

### **Core Design Principle (Non-Negotiable)**

* The dashboard and notifications consume alerts; they do not interpret them.  
* No business logic.  
* No decision-making.  
* No modification of alert content.

**NOTE:** Interpretation, assessment, and disposition remain the responsibility of QA and Operations.

## 1\. Alert Queue Dashboard (Read-Only)

### 

### **Purpose**

Provide a simple, operationally usable queue of Sentinel alerts suitable for a DOC-style workflow.

### 

### *Data Source*

* Derived only from `alerts.jsonl`  
* No additional enrichment  
* No derived risk scoring

### *Displayed Columns*

* Alert ID  
* Area  
* Severity  
* Risk Code  
* Product ID  
* Status (`NEW`, `ACKNOWLEDGED`, `CLOSED`)  
* Created At (UTC)  
* Age (computed at view time)

### *Filters*

* Area  
* Severity  
* Risk Code  
* Product ID  
* Age thresholds (e.g., \>30 minutes, \>60 minutes)

### *Explicitly Not Displayed*

* Raw event payloads  
* GMP values or calculations  
* Free-text narratives  
* Operator names  
* Step instructions or execution detail

### *Compliance Rationale*

* Dashboard is a **read-only view**, not a system of record  
* All data originates from immutable alert artifacts  
* No user interaction alters stored alert data.

This preserves audit integrity and prevents uncontrolled data mutation.

## 2\. SLA Timers (Computed, Not Stored)

### 

### **SLA Model**

SLA timing is calculated dynamically at runtime:  
`SLA Age = current_time (UTC) − created_at`

### *Enforcement Rules*

* No SLA timestamps written to alert records  
* No background “business clock” services  
* No persistence of SLA state

### *Compliance Rationale*

* Computed SLAs are transparent and reproducible  
* No hidden timing logic  
* Avoids unverifiable escalation behavior

**NOTE:** Auditors expect to be able to recompute timing independently.

## 

## 3\. Alert Acknowledgement (Minimal — Optional in v0.1)

### 

### **Scope**

Acknowledgement is the **only** permitted user action in Phase 5\.

### 

### *Allowed Action*

* Change alert status from `NEW` → `ACKNOWLEDGED`

### *Recorded Metadata*

* `alert_id`  
* `acknowledged_at` (UTC)  
* `acknowledged_by_role` (role only; no personal identifiers)

### *Storage Model*

* Written to a **separate append-only artifact**  
  * Example: `alert_actions.jsonl`  
* Original alert record remains immutable

### *Compliance Rationale*

* Preserves immutability of alert records  
* Creates a clear, auditable chain of custody  
* Mirrors behavior of validated enterprise alerting systems

## 4\. Notifications (Email / Teams-Style)

### 

### **Notification Philosophy**

Notifications are summaries, not records. They signal awareness; not action.

### 

### *Allowed Notification Content*

* Alert ID  
* Area  
* Severity  
* Risk Code  
* Product ID  
* Link to dashboard (if applicable)

### *Explicitly Forbidden*

* Batch narratives  
* Calculations  
* Operator names  
* Step-level instructions

### *Example Notification*

`🚨 Sentinel Alert`  
`Area: AREA-A`  
`Severity: CRITICAL`  
`Risk: DR-002`  
`Product: PROD-123`  
`Status: NEW`

No additional context is included by design.

## 5\. Escalation Logic (Time-Based Only)

### 

### *Escalation Rule*

* Applies **only** to `CRITICAL` alerts  
* Based solely on time unacknowledged

### *Example*

* If a CRITICAL alert remains `NEW` for \>30 minutes → escalate

### *Escalation Behavior*

* Secondary notification  
* Expanded recipient list (e.g., QA leadership)

### *Compliance Rationale*

* Escalation is procedural, not interpretive  
* No content-based decision logic  
* Consistent with real DOC escalation models

## Phase 5 Scope Boundaries

*This phase adds:*

* Visibility  
* Awareness  
* Escalation

*This phase does NOT add:*

* Deviation decisions  
* Batch impact  
* Workflow enforcement  
* Root cause analysis

