# Risk Scoring Rubric for Access Grants

**Document ID:** RISK-RUBRIC-001
**Tags:** risk-scoring, methodology, rubric

## Purpose

This rubric defines how the Risk Scoring Agent should evaluate each access grant and assign a risk score from 1 (negligible) to 10 (critical, immediate action required).

## Scoring Factors

### Factor 1: Role-Resource Alignment (weight: high)

- Does the access level match what is typically required for the user's role?
- An intern or junior role holding admin access to a critical-sensitivity resource (production database, cloud billing, payroll, production infrastructure) should score 8-10 regardless of other factors.
- A role-appropriate grant (e.g., DevOps Engineer with admin access to production servers) should score 1-3 on this factor alone.

### Factor 2: Usage / Dormancy (weight: high)

- Zero access events in the trailing 30 days = dormant. Dormant access on a critical or high-sensitivity resource adds 3-4 points to the score.
- Regular, frequent usage consistent with the role's function should not add risk on this factor, even for high-sensitivity resources, provided Factor 1 is satisfied.

### Factor 3: Provisioning Method (weight: medium)

- Access granted by "copying a template" from another employee without independent review adds 2 points, particularly for new hires (tenure under 6 months).
- Access granted for a specific, time-bound project that has since ended (and was not revoked) adds 2 points.

### Factor 4: Resource Sensitivity (weight: medium)

- Critical sensitivity (production databases, cloud billing, payroll, production infrastructure): multiply base score by 1.5
- High sensitivity (HR records): multiply base score by 1.25
- Medium/Low sensitivity: no multiplier

### Factor 5: Tenure (weight: low)

- Employees with tenure under 6 months holding elevated access not directly tied to onboarding-stage tasks should receive a +1 modifier, reflecting reduced vetting/familiarity with security practices.

## Score Interpretation

- **8-10 (Critical):** Immediate remediation recommended. Typically: role-mismatched admin access to critical resources, often combined with dormancy or template-copy provisioning.
- **5-7 (High):** Remediation recommended within current review cycle.
- **3-4 (Medium):** Flag for next scheduled review; not urgent.
- **1-2 (Low):** No action needed; access is appropriate and actively used.

## Output Format

For each grant, the Risk Scoring Agent should output:
- Numeric score (1-10)
- Severity label (Critical / High / Medium / Low)
- A one-to-two sentence explanation referencing the specific factors that drove the score

## Related Documents

- Least Privilege Policy (POL-ACCESS-001)
- SOC2 Control Mapping (SOC2-CONTROLS-001)
- Remediation Playbook (REMEDIATION-001)
