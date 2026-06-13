# Remediation Playbook

**Document ID:** REMEDIATION-001
**Tags:** remediation, playbook, policy-generation

## Purpose

This playbook provides the standard remediation actions the Policy Generation Agent should recommend for common risk patterns identified by the Risk Scoring Agent. Each recommendation must reference the relevant policy section and SOC2 control.

## Remediation Patterns

### Pattern A: Intern/Junior Role with Admin Access to Critical Resource

**Trigger:** User with tenure under 6 months and a junior/intern role title holds admin-level access to a critical-sensitivity resource (cloud billing, production database, production infrastructure, payroll).

**Recommended Action:** Remove the access grant entirely. If the user has zero usage in the trailing 30 days, this is a fully safe removal (validate via Simulation Agent). If there is any usage, downgrade to viewer and flag for manager review rather than full removal.

**Cite:** POL-ACCESS-001 Section 4 (Intern and Contractor Access); SOC2-CONTROLS-001 CC6.1

### Pattern B: Dormant Access from Completed Project

**Trigger:** Access grant's "reason on file" references a completed or time-bound project, and the activity log shows zero or near-zero usage in the trailing 30 days.

**Recommended Action:** Revoke the access grant. Document the original justification and the dormancy evidence in the audit trail.

**Cite:** POL-ACCESS-001 Section 6 (Dormant Access); SOC2-CONTROLS-001 CC6.3

### Pattern C: Onboarding Template Copy, Unreviewed

**Trigger:** Access grant's "reason on file" indicates it was copied from another employee's template during onboarding and has not been reviewed, particularly where the resource sensitivity does not match the new employee's role.

**Recommended Action:** Remove the access grant unless the resource is directly relevant to the employee's actual day-to-day role (cross-check against Factor 1 of the risk rubric). If relevant, re-issue as a properly justified, reviewed grant.

**Cite:** POL-ACCESS-001 Section 5 (Onboarding Template Risk); SOC2-CONTROLS-001 CC6.2

### Pattern D: Lingering Admin Access After One-Off Project

**Trigger:** A non-admin-role employee holds admin access granted for a specific migration/project, the project has ended, but the access was never downgraded.

**Recommended Action:** Downgrade to viewer-level access, or remove entirely if zero usage in trailing 30 days.

**Cite:** POL-ACCESS-001 Section 3 (Admin Access Restrictions); SOC2-CONTROLS-001 CC6.3

### Pattern E: Role-Appropriate, Actively Used Access

**Trigger:** Access level matches the role's standard requirements and usage in the trailing 30 days is consistent with normal job function.

**Recommended Action:** No change. Mark as "reviewed, no action required" for audit trail purposes.

## Output Requirements

For every flagged grant, the Policy Generation Agent must output:
1. The matched remediation pattern (A-E)
2. The specific recommended new access level (or "remove")
3. A citation to the policy section and SOC2 control
4. A note for the Simulation Agent indicating what activity-log evidence should be checked before this change is marked safe

## Related Documents

- Least Privilege Policy (POL-ACCESS-001)
- SOC2 Control Mapping (SOC2-CONTROLS-001)
- Risk Scoring Rubric (RISK-RUBRIC-001)
