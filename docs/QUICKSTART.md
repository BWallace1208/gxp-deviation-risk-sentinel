## **Quickstart (Local)**

### 

### **Prerequisites**

* Python 3.11+  
* Git  
* PowerShell / Terminal

### ***1\. Clone the repository***

`git clone https://github.com/BWallace1208/gxp-deviation-risk-sentinel.git`  
`cd gxp-deviation-risk-sentinel`

### ***2\. (Optional) Create a virtual environment***

`python -m venv .venv`  
`.venv\Scripts\activate   # Windows`  
`# source .venv/bin/activate  # macOS/Linux`

### ***3\. Install dependencies***

`pip install -r requirements.txt`

### ***4\. Run Sentinel against a test event***

Run all lines from the **repo root**:  
`python -m sentinel.app sentinel/tests/test_vectors/event_step_opened_overdue.json`  
Expected output:  
`ACCEPTED ✅`  
`ALERT EMITTED 🚨`

### ***5\. View emitted alerts***

Alerts are written append-only to:  
`sentinel/storage/alerts.jsonl`  
Example:  
`Get-Content sentinel/storage/alerts.jsonl`  
Each line is a single immutable alert record (JSONL).

### ***6\. Run correlation sweep (optional)***

To evaluate overdue step timeouts via correlation state:  
`python -m sentinel.app --sweep-timeouts`  
This scans correlation state and emits alerts **only if** timeout conditions are met and suppression rules allow.

## 

## **Outputs**

* Alerts: `sentinel/storage/alerts.jsonl`  
* Audit log: `sentinel/storage/audit_log.jsonl`  
* Correlation state: `sentinel/storage/correlation_state_v0_1.json`  
* Suppression state: `sentinel/storage/suppression_state_v0_1.jso`

All outputs are:

* Append-only  
* Metadata-only  
* Inspection-safe (no GMP values, no narratives)

## **Design Notes (v0.1)**

* Deterministic rule evaluation  
* Rules defined as data (YAML)  
* Alerts are records, not interpretations  
* Dashboards and notifications consume alerts,  they do not alter them

**Why this exists**  
Sentinel detects procedural risk in GxP digital workflows without storing GMP data or making compliance decisions. It evaluates deterministic rules, emits inspection-safe alerts, and leaves interpretation with QA and Operations;where it belongs.  
