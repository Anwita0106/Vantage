# Incident History: Access-Related Security Events

**Document ID:** INCIDENT-HISTORY-001
**Tags:** incidents, history, lessons-learned

## Purpose

This document records prior synthetic security incidents related to excessive or dormant access grants. It is used by Vantage's agents to ground recommendations in real organizational consequences and to strengthen the justification provided to stakeholders.

## Incident INC-2025-014: Dormant Admin Credential Exploited in Phishing Attack

**Date:** February 2025
**Summary:** An employee in the Sales department had been granted temporary admin access to the Production Database (Customer Records) in late 2024 for a one-time data export task. The access was never revoked. In February 2025, the employee's email credentials were compromised via a phishing attack. Because the dormant admin database access remained active, the attacker was able to use the compromised account to query and exfiltrate a subset of customer records before the activity was detected.

**Root Cause:** Dormant access grant (CC6.3 violation) combined with credential compromise.

**Lesson:** Dormant access dramatically increases the blast radius of any individual account compromise. Routine removal of unused access is one of the highest-leverage security controls available.

## Incident INC-2025-031: Onboarding Template Copy Led to Unauthorized Billing Changes

**Date:** July 2025
**Summary:** A new engineering intern was onboarded using an access template copied from a senior engineer's profile, which included admin access to the cloud billing console. The access was not reviewed. Several months later, the intern's account was used (accidentally, during a misconfigured automation script) to modify billing alert thresholds, resulting in a delayed response to an unrelated cost anomaly that cost the company approximately $14,000 in unexpected cloud spend before being caught.

**Root Cause:** Unreviewed onboarding template copy (CC6.2 violation) granting access far beyond the intern's actual role requirements.

**Lesson:** Onboarding "shortcuts" that copy access profiles from unrelated senior roles are a recurring source of avoidable risk, especially for short-tenure employees who have not yet been fully vetted on security practices.

## Incident INC-2025-047: Lingering Migration Access Used in Internal Misconfiguration Incident

**Date:** October 2025
**Summary:** During a server migration project, a backend engineer was granted temporary admin SSH access to production servers. After the migration concluded, this access was not downgraded. Months later, the same engineer, while testing an unrelated script, accidentally ran a destructive command against a production server using the lingering admin access, causing a 40-minute service outage.

**Root Cause:** Lingering admin access after project completion (CC6.3 violation).

**Lesson:** Even well-intentioned, non-malicious use of lingering elevated access can cause significant operational incidents. Time-bound access should be automatically downgraded at project completion.

## Related Documents

- Least Privilege Policy (POL-ACCESS-001)
- SOC2 Control Mapping (SOC2-CONTROLS-001)
- Remediation Playbook (REMEDIATION-001)
