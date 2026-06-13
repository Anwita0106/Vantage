# Internal Access Policy: Least Privilege Standard

**Document ID:** POL-ACCESS-001
**Tags:** access-control, least-privilege, policy, governance

## Summary

This policy establishes the standard for granting, reviewing, and revoking access to company systems and data. It applies to all employees, interns, and contractors.

## Core Principles

1. **Least Privilege by Default**: Users must be granted the minimum level of access required to perform their current role. Access beyond this baseline requires written justification and time-bound expiry.

2. **Mandatory 90-Day Review**: All access grants must be reviewed at least every 90 days. Access that has not been used in the prior 30 days during a review must be flagged for removal unless an active business justification is documented.

3. **Admin Access Restrictions**: Admin-level access to critical systems (databases, cloud billing, production infrastructure) is restricted to roles where it is part of standard job function (e.g., DevOps Engineer, SRE, Finance Manager). Admin access granted for one-off projects must be automatically downgraded to viewer or removed within 30 days of project completion.

4. **Intern and Contractor Access**: Interns and contractors must receive read-only or editor-level access only, scoped to systems directly relevant to their assigned project. Interns must never receive admin access to critical infrastructure, cloud billing consoles, or financial systems, regardless of how access was provisioned during onboarding.

5. **Onboarding Template Risk**: Access provisioned by copying a "template" from another employee's profile (a common onboarding shortcut) must be reviewed within 14 days to remove any access not relevant to the new employee's actual role.

6. **Dormant Access**: Any access grant with zero recorded usage in the trailing 30-day window is considered dormant and should be revoked, regardless of the original justification, unless the resource owner explicitly confirms ongoing need.

## Severity Classification

- **Critical Risk**: Admin access to critical-sensitivity resources (production databases, cloud billing, production infrastructure, payroll) held by users whose role does not require it, or which is dormant.
- **High Risk**: Any access to high or critical-sensitivity resources granted via onboarding template copying without review.
- **Medium Risk**: Editor or viewer access to medium-sensitivity resources that is dormant for 30+ days.
- **Low Risk**: Standard role-appropriate access with regular usage.

## Related Documents

- SOC2 Control Mapping (SOC2-CONTROLS-001)
- Risk Scoring Rubric (RISK-RUBRIC-001)
- Remediation Playbook (REMEDIATION-001)
