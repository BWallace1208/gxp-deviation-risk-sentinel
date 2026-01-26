## Assumptions & Constraints

## **Purpose**

This document captures key assumptions and constraints for the GxP Deviation Risk Sentinel. It defines what must be true for the system to operate as intended and what limitations intentionally shape the design.

**Assumptions**

* Source systems (DBR, MES, IMEX/DOC) can emit workflow or audit-trail metadata events suitable for monitoring.  
* The Sentinel can consume events in a read-only manner without modifying source system workflows or records.  
* Events include sufficient metadata to identify process context (e.g., Area, Product ID, Step/Section code, timestamps).  
* Where identity is included, it can be tokenized prior to broader distribution.  
* Risk codes and rules are maintained as a controlled vocabulary and versioned configuration.  
* Alerts are advisory; human review is required for any quality action.  
* Source systems remain systems of record for batch data, audit trails, and deviation initiation.  
* Time synchronization is reliable enough to support alert age calculations (i.e., server timestamps).

**Constraints**

* No GMP process values may be ingested, stored, persisted, or logged by the Sentinel.  
* No free-text batch narratives, attachments, signatures, or raw batch/operator identifiers may be stored by the Sentinel.  
* The Sentinel must **not** create, modify, or write back into DBR/MES/IMEX/eQMS systems.  
* The Sentinel must remain deployment-neutral at the conceptual stage.   
* Alerting **must** support least-privilege distribution (sanitized alerts to Ops/DOC; more privileged views restricted to QA roles where applicable).  
*  Rules must be deterministic and explainable.  
* System behavior must be auditable (append-only records of Sentinel actions, including rejected events).

**Non-Goals**

* Automated deviation initiation.  
* Automated batch hold placement.  
* Batch disposition decisions.  
* Replacement of validated GMP execution systems.  
* Storage of GMP values for analytics or reporting.

