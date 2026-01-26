## **Rules Engine Specification (v0.1)**

## **Purpose**

This document defines how the GxP Deviation Risk Sentinel evaluates metadata events to generate advisory deviation-risk alerts. Rules are deterministic, version-controlled, and explainable. The rules engine does not store GMP values and does not make quality decisions.

**Inputs**  
Validated events that pass:

* Event schema validation (allow-list)  
* Prohibited-field tripwires (deny-list)

Events are expected to contain only metadata fields such as site, area, product\_id, template identifiers, step/section codes, timestamps, and tokenized identities.

*Outputs*

1\. Advisory alerts containing:

* Risk\_code (DR-\#\#\#)  
* Severity (LOW/MEDIUM/HIGH/CRITICAL)  
* Context metadata (site/area/product/template/step/section/page if present)  
* Rule\_id and rule\_version  
* References to contributing event\_id values (metadata only)

*Rule Design Principles*

* Deterministic and explainable (no opaque scoring required for v0.1).  
*  Metadata-only (no process values, limits, or free-text narratives).  
* Strict mapping from event patterns to standardized risk codes.  
* Conservative posture: prefer false alerts/rejections over GMP data capture.  
* Rules may be enabled/disabled without code changes.

*Normalized Event Types Supported (v0.1)*

* STEP\_OPENED  
* STEP\_COMPLETED  
* SUBMIT\_ATTEMPTED  
* SUBMIT\_REJECTED\_REQUIRED\_MISSING  
* VERIFICATION\_REQUIRED\_MISSING  
* SESSION\_TIMEOUT  
* OUT\_OF\_SEQUENCE\_ATTEMPT  
* CALC\_STATUS\_CHANGED  
* HOLD\_TRIGGERED  
* EXCEPTION\_TRIGGERED  
* SIGN\_CAPTURED




**Rule Matching Model**  
Each rule contains:

* *rule\_id, version, enabled*  
* *description and rationale*  
* *trigger conditions (event\_type and optional field constraints)*  
* *optional timing thresholds (e.g., step\_open too long)*  
* *outputs: risk\_code, severity, recommended\_action*  
* *routing: intended consumers (QA, Area Management, DOC)*

*Rules may be evaluated as:*

* *Single-event rules (triggered by one event)*  
* *Correlation rules (require multiple events tied by batch\_token or correlation\_id)*  
* *Time-window rules (require elapsed time calculations using timestamps)*

*Correlation Keys:*  
Preferred:

* batch\_token

Fallback:

* correlation\_id


**Note:** If neither is present, the rule engine may still generate single-event alerts but must not attempt multi-event correlation.

**Audit Requirements**  
For each evaluated event, record:

* event\_id  
* rule\_id and rule\_version evaluated  
* evaluation outcome (matched/not\_matched)  
* if matched: alert\_id emitted (or suppression reason)  
* rejected events (schema/tripwire) are not persisted; only minimal rejection metadata is logged.