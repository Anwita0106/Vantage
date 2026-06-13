# SOC2 Control Mapping for Access Governance

**Document ID:** SOC2-CONTROLS-001
**Tags:** soc2, compliance, controls, audit

## Overview

This document maps Vantage's access governance findings and remediations to relevant SOC2 Trust Services Criteria controls. It is used by the Policy Generation Agent to cite the specific compliance control that justifies a recommended access change.

## CC6.1 — Logical Access Controls

**Control Description:** The entity implements logical access security software, infrastructure, and architectures over protected information assets to protect them from security events to meet the entity's objectives.

**How it applies:** Any finding involving a user holding access beyond their role's requirements (e.g., an intern with cloud billing admin access) is a direct CC6.1 finding. Remediation: downgrade or remove the excess access grant.

## CC6.2 — Prior Authorization of Access

**Control Description:** Prior to issuing system credentials and granting system access, the entity registers and authorizes new internal and external users whose access is administered by the entity.

**How it applies:** Access grants provisioned via "copying a template" from another user's profile without independent authorization for the new user's specific role are CC6.2 findings. Remediation: require explicit re-authorization or removal.

## CC6.3 — Role-Based Access Removal and Modification

**Control Description:** The entity authorizes, modifies, or removes access to data, software, functions, and other protected information assets based on roles, responsibilities, or the system design and changes, giving consideration to the concept of least privilege.

**How it applies:** Dormant access (no usage in 30+ days) that was originally granted for a time-bound project but never revoked is a CC6.3 finding. Remediation: revoke access and document the change.

## CC7.2 — Monitoring of Access Activity

**Control Description:** The entity monitors system components and the operation of controls to detect anomalies that are indicative of malicious acts, natural disasters, and errors affecting the entity's ability to meet its objectives.

**How it applies:** The Simulation Agent's review of 30-day activity logs before applying policy changes directly supports CC7.2 by demonstrating ongoing monitoring of access usage patterns.

## Audit Reporting Requirements

When Vantage generates a compliance report, each remediation item must cite:
1. The specific control violated (e.g., CC6.1)
2. The evidence (access grant details + activity log summary)
3. The remediation action taken
4. The simulation result confirming no operational disruption

## Related Documents

- Least Privilege Policy (POL-ACCESS-001)
- Risk Scoring Rubric (RISK-RUBRIC-001)
- Remediation Playbook (REMEDIATION-001)
