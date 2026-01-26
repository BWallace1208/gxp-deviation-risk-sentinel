## **Prohibited Fields & Tripwires (v0.1)**

## **Purpose**

This document defines explicit prohibited fields and content tripwires used by the GxP Deviation Risk Sentinel to prevent ingestion, persistence, or logging of GMP process values or sensitive batch record content.

The event schema uses strict allow-listing. This tripwire list adds an additional defensive layer for detection of common “leak paths” where GMP values may be embedded under misleading field names.

**Enforcement Principles**

* Reject payloads containing prohibited keys (exact matches).  
* Reject payloads containing prohibited key patterns (case-insensitive).  
* Reject payloads containing suspicious content patterns in strings (case-insensitive).  
* Do not persist rejected payload contents; log only rejection reason \+ event\_id (if present).

*Prohibited Keys (Exact Match)*

1\. If any of the following keys are present at any level of the payload, reject the event:

* weight  
* volume  
* temperature  
* pressure  
* ph  
* viscosity  
* density  
* concentration  
* potency  
* yield  
* specification  
* spec\_limit  
* upper\_limit  
* lower\_limit  
* target\_value  
* actual\_value  
* measured\_value  
* setpoint  
* material\_lot  
* lot\_number  
* batch\_number  
* operator\_id  
* employee\_id  
* signature  
* e\_signature  
* comment  
* narrative  
* attachment  
* image  
* file  
    
  


  
*Prohibited Key Patterns (Regex, case-insensitive)*  
1\. Reject if any key matches these patterns:

* ^temp(erature)?$  
* ^press(ure)?$  
* ^wt$|^weight\_?  
* ^vol$|^volume\_?  
* ^(upper|lower)\_(spec|limit)$  
* ^(spec|limit|target|actual|measured|setpoint)  
* ^(lot|batch|serial)(\_?(no|num|number))?$  
* ^(operator|employee|user)(\_?id)?$  
* ^(comment|notes?|narrative|free\_text)$  
* ^(attach|attachment|file|image|photo)

*Prohibited Content Patterns (String Tripwires)*

1. Reject if any string value contains patterns consistent with GMP values or batch narrative content. Examples:  
     
* \- Units and measurements: "mg", "g", "kg", "mL", "L", "°C", "psi", “F”  
* \- Spec-style notation: "NLT", "NMT", "\<=", "\>=", "±"  
* \- Lot/batch indicators: "LOT", "BATCH", "BN:"  
* \- Signature-like artifacts: "Signed by", "E-sign", "Signature"

**Note**: These tripwires are conservative by design. The system is advisory and should prefer false rejection over accidental GMP data capture.

*Logging Rules for Rejections*

1. *When rejecting an event, log only:*  
* rejection\_reason\_code  
* rejection\_reason\_text (short)  
* event\_id (if present)  
* source\_system  
* event\_timestamp (if present)  
* received\_at (server timestamp)


Do not log the rejected payload body

**Change Control**  
Tripwire lists are versioned. Updates require:

* rationale summary.  
* test vector updates demonstrating rejection/acceptance behavior.

