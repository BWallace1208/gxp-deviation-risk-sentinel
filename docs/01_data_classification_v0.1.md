## DOC 01 \- Data Classification & Handling Rules

## **Data Handling Principle**

The GxP Deviation Risk Sentinel enforces strict separation between GMP data and monitoring metadata. The system is intentionally designed to operate without capturing, storing, or persisting GMP process values. Any inbound payload containing prohibited data elements is rejected at ingestion.

**Allowed Data (Metadata Only)**

The following categories of data are **permitted** for ingestion and processing:

| *Category*  | *Examples*  |
| ----- | ----- |
| Location Context | Site, Area, Suite, Line  |
| Process Context | Product ID, DBR Template ID, Step/Page/Section Code |
| Timing | Event timestamp, alert creation time |
| Identity (Masked) | Operator token, operator role |
| Risk Information | Risk code, severity, alert status |
| System Context | Source system identifier |

**Prohibited Data**  
The following data types are explicitly **prohibited** from ingestion, storage, or logging:

* GMP process values (e.g., weights, volumes, temperatures).  
* Specifications or acceptance limits.  
*  Material quantities or yields.  
*  Potency, purity, or assay data.  
*  Free-text batch narratives or comments.  
*  Attachments, images, or scanned records.  
*  Raw operator identifiers or batch numbers.  
*  Electronic signatures or signature images.

**Enforcement Mechanisms**

* JSON schema validation at ingestion.  
* Explicit rejection of payloads containing prohibited fields.  
* Audit logging of rejected payload attempts.  
* No persistence of rejected data.

