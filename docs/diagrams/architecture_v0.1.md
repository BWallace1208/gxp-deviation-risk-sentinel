## System Architecture Overview

## **Purpose**

This document describes the high-level architecture of the GxP Deviation Risk Sentinel. It explains how the system ingests metadata events, evaluates deviation risk conditions, and generates advisory alerts while maintaining strict separation from GMP systems and data.

The architecture is intentionally designed to be read-only, metadata-only, and non-invasive to validated execution systems.

**Architectural Principles**  
The system is designed according to the following principles:

* Read-only integration with source systems.   
* No storage or persistence of GMP process values.    
* Clear separation between systems of record and advisory monitoring.    
* Explicit system boundaries to prevent scope creep.    
* Auditability of the sentinel’s own actions. 

**High-Level Architecture Description**  
1\.  Source Systems

*    Digital Batch Record (DBR).  
*    Manufacturing Execution Systems (MES).  
*    MEX / Digital Operations Center event feeds.

   These systems remain the authoritative systems of record and emit workflow or audit-trail metadata events.

2\.  Event Ingestion Layer

*    Receives read-only metadata events via API or message-based interfaces.  
*    Validates incoming payloads against a strict event schema.  
*    Rejects any payload containing prohibited GMP data elements.  
*    Records ingestion activity for audit purposes.

3\. Rules Evaluation Engine

*    Evaluates validated events against predefined deviation risk rules.  
*    Applies deterministic, version-controlled logic.  
*    Assigns standardized risk codes and severity levels.  
*    Does not perform batch disposition or quality decisions.

4\. Alert Management

*   Generates advisory alert records containing metadata only.  
*   Tracks alert lifecycle status (New, Acknowledged, Closed).  
*   Calculates alert age and escalation state.

5\. Audit Logging

*    Maintains an append-only record of system actions.  
*    Records event receipt, rule evaluation outcomes, and alert state changes.  
*    Supports traceability without storing GMP data.

6\.  Notification & Visibility

*    Provides alert visibility through a dashboard or Digital Operations Center view.  
*    Issues notifications based on severity and escalation logic.  
*    Does not expose restricted or sensitive data outside authorized roles.

**System Boundary Statement**

The GxP Deviation Risk Sentinel operates as an external advisory service. It consumes metadata events from source systems and produces risk alerts but does not modify, replace, or interfere with validated GMP systems. All quality decisions remain the responsibility of human reviewers operating within established quality systems.

**Deployment Neutrality**

This architecture is interoperable and may be implemented on-premises or in a cloud environment. Cloud services referenced in later phases are examples only and do not alter system boundaries or regulatory positioning.

**Flowchart**

'''mermaid
flowchart LR
    subgraph Source_Systems["Source Systems"]
        DBR["Digital Batch Records (DBR)"]
        MES["Manufacturing Execution Systems (MES)"]
        IMEX["IMEX / Digital Operations Center"]
    end

    subgraph Sentinel["GxP Deviation Risk Sentinel"]
        Ingest["Event Ingestion"]
        Rules["Rules Evaluation"]
        Alerts["Alert Management"]
        Audit["Audit Logging"]
    end

    subgraph Consumers["Alert Consumers"]
        QA["Quality Assurance (QA)"]
        DOC["Digital Operations Center (DOC)"]
        AM["Area Managemet (AMGNT)"]
    end

    %% One-way ingestion (read-only)
    DBR --> Ingest
    MES --> Ingest
    IMEX --> Ingest

    %% Internal sentinel flow
    Ingest --> Rules
    Rules --> Alerts
    Rules --> Audit
    Alerts --> Audit

    %% One-way alerts out
    Alerts --> QA
    Alerts --> AREA MANAGEMENT
    Alerts --> DOC