## **Data Flow Diagram (Metadata-Only)**

## **Purpose**

This document describes how meta-data events flow from source systems into the GxP Deviation Risk Sentinel and how advisory alerts flow to consumers. The diagram intentionally avoids APIs, cloud services, databases, ports, or protocols.

**Data Flow (Mermaid)**  
```mermaid  
flowchart LR

  subgraph Source\_Systems\["Source Systems (Systems of Record)"\]  
    DBR\["DBR (workflow metadata events)"\]  
    MES\["MES (workflow metadata events)"\]  
    IMEX\["IMEX / DOC (event feeds)"\]  
  end

  subgraph Sentinel\["GxP Deviation Risk Sentinel (Advisory / Read-Only)"\]  
    V\["Validate & Filter (reject prohibited data)"\]  
    N\["Normalize (standard event shape)"\]  
    R\["Evaluate Rules (risk codes \+ severity)"\]  
    A\["Create Advisory Alert"\]  
    L\["Append-Only Audit Log (Sentinel actions)"\]  
  end

  subgraph Consumers\["Alert Consumers"\]  
    QA\["QA"\]  
    AM\["Area Management"\]  
    DOC\["DOC"\]  
  end

  DBR \--\> V  
  MES \--\> V  
  IMEX \--\> V

  V \--\> N  
  N \--\> R  
  R \--\> A  
  V \--\> L  
  R \--\> L  
  A \--\> L

  A \--\> QA  
  A \--\> AM  
  A \--\> DOC

**Data Flow (ASCII)**

\+--------------------------------------------------+  
 | SOURCE SYSTEMS (Systems of Record) |  
 | |  
 | DBR | MES | IMEX / DOC |  
 | (events) (events) (feeds) |  
 \+-----|------------|--------------|----------------+  
 | | |  
 v v v  
 \+--------------------------------------------------+  
 | GxP DEVIATION RISK SENTINEL (Read-Only) |  
 | |  
 | \[Validate & Filter\] \--\> \[Normalize\] \--\> \[Rules\]|  
 | | | |  
 | v v |  
 | \[Append-Only Audit Log\] \[Advisory Alert\] |  
 \+-------------------------------------|------------+  
 |  
 v  
 \+--------------------------------------------------+  
 | ALERT CONSUMERS |  
 | QA | Area Management | DOC |  
 \+--------------------------------------------------+

## **Notes**

* Only one-way flow into the Sentinel (read-only).  
* Only metadata is permitted; prohibited GMP data is rejected.  
* Alerts are advisory and require human review for quality actions.

