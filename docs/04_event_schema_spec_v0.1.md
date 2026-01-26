## **Event Schema Specification (v0.1)**

## **Purpose**

This document defines the metadata-only event contract for the GxP Deviation Risk Sentinel. The schema constrains what the Sentinel can ingest and is designed to prevent capture or persistence of GMP process values.

**Design Rules**

* Metadata-only: no process values, limits, yields, or free-text narratives.  
* Read-only: events represent observations; no write-back behavior exists.  
* Strict allow-listing: unknown fields are rejected (\`additionalProperties: false\`).  
* Tokenization: raw batch and operator identifiers are not permitted.

**Required Fields**  
Events must include the following minimum fields:

* event\_id, source\_system, event\_type, event\_timestamp  
* site, area, product\_id  
* dbr\_template\_id, dbr\_template\_version  
* step\_code, section\_code  
* operator\_token, operator\_role

*Optional Fields*

* suite, line, page\_number  
* batch\_token   
* calc\_status   
* hold\_code (if emitted by source systems)  
* correlation\_id (for session/batch correlation)

**Rejection Criteria**  
Any inbound payload is rejected if:

* It contains fields not defined in the schema.  
* It includes prohibited content such as process values, specs/limits, yields, attachments, or free-text narratives.  
* It includes raw batch numbers or raw operator identifiers.

## **Event Type Notes**

The schema supports normalized event types intended to cover common DBR/MES/DOC workflow signals (i.e., submit attempts rejected due to missing required entries, timeouts, out-of-sequence attempts, calculation pass/fail flags, and hold/exception triggers).

