## **Threat Model (Light)**

## **Purpose**

This document identifies plausible threats to the GxP Deviation Risk Sentinel and defines mitigations aligned with its read-only, metadata-only, advisory design. The goal is to reduce risk while maintaining strict separation from GMP systems and data.

**Scope**  
Threats considered:

* Confidentiality of operational metadata and identities.  
* Integrity of alerts and audit logs.  
* Availability of monitoring and alerting.  
* Misuse or misinterpretation of advisory alerts.

Threats excluded:

* Threat modeling of the DBR/MES/IMEX platforms themselves (owned by those systems).  
* Cloud/on-prem network topology specifics (handled during deployment phase).


**Key Assets**

* Event metadata (Area, Product ID, Step/Section codes, timestamps).  
* Risk codes and rule logic.  
* Alert records and alert lifecycle status.  
* Sentinel audit trail (append-only record of actions).  
* Tokenization keys (for operator/batch tokens).


  
**Trust Boundaries**

* Source Systems (systems of record) → Sentinel ingestion boundary.  
* Sentinel → Alert Consumers (QA, Area Management, DOC) distribution boundary.  
* Admin boundary for rule changes (higher privilege).


**Threats & Mitigations**

**1\. Confidentiality: Metadata Leakage**  
***Threat*****:** Unauthorized users access alerts revealing sensitive operational context.    
***Mitigations:***

* Strict allowed/prohibited data policy; reject payloads containing prohibited elements.  
* Tokenize identities (operator/batch) where identity is not required.  
* Role-based access for alert visibility and filtering.  
* Separate “sanitized alert” from “privileged detail” patterns (if detail exists elsewhere).

 **2\. Integrity: Event Tampering or Spoofing**  
***Threat:*** Fake or altered events generate false alerts or hide true risk.    
***Mitigations:***

* Schema validation and event type allow-listing.  
* Source system identification and event signing/verification (deployment phase).  
* Rate limiting and replay protection (deployment phase).  
* Audit logging of ingestion attempts and rejections.

**3\. Integrity: Rule Manipulation**  
***Threat:*** Unauthorized change to rules alters alert behavior.    
***Mitigations:***

* Rules are versioned and stored in source control.  
* Rule changes require documented change notes (rule\_change\_log).  
* Restricted admin role for rule updates (deployment phase).  
* Audit log entries for rule version used per alert.

**4\. Integrity: Audit Log Tampering**  
***Threat:*** Audit records are modified or deleted to conceal actions.    
***Mitigations:***

* Append-only log design (write-once behavior).  
* Integrity checksums or hash chaining (optional enhancement).  
* Restricted write permissions (deployment phase).  
* Regular export/backup of audit logs (deployment phase).

**5\. Availability: Alerting Outage**  
***Threat:*** Sentinel downtime prevents detection and notification.    
***Mitigations:***

* Graceful degradation (queue events for later processing in deployment phase).  
* Health monitoring and alerting on system health (deployment phase).  
* Clear statement: Sentinel is advisory; source systems remain authoritative.

**6\.  Misuse:** Alerts Treated as Quality Decisions  
***Threat:*** Stakeholders treat alerts as confirmed deviations.    
***Mitigations:***

* Clear “advisory only” labeling in alerts and documentation.  
* Risk codes described as “potential deviation risk”.  
* Training note: actions require QA review and established quality processes.

**Residual Risk Statement**

Even with mitigations, the Sentinel may generate false positives or miss certain risks due to limited metadata context. The system remains advisory and does not replace established quality oversight, deviation systems, or batch disposition processes.  
