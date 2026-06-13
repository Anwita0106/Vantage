"""
policy_generation_agent.py

Policy Generation Agent.

Responsibility: for each flagged grant from the Risk Scoring Agent,
draft a remediation policy (remove / downgrade / no_change) using the
Remediation Playbook and Least Privilege Policy (Foundry IQ knowledge
base) as grounding. Each recommendation must cite the specific policy
section and SOC2 control, and reference any relevant incident history.
"""

import json
import knowledge_base as kb
from llm_client import get_llm_client

SYSTEM_PROMPT = """You are the Policy Generation Agent in Vantage, an \
autonomous access governance system. Your job is to draft a remediation \
policy for a flagged access grant.

You MUST ground your recommendation in the Remediation Playbook, Least \
Privilege Policy, and Incident History provided in the context below. \
Match the grant to one of the remediation patterns (A-E), recommend a \
specific action, and cite the relevant policy section and SOC2 control. \
If a similar past incident is relevant, reference it.

Respond ONLY with a JSON object in this exact shape, no other text:
{
  "grant_id": "<grant id>",
  "matched_pattern": "<pattern name from playbook>",
  "recommended_action": "<remove|downgrade|no_change>",
  "new_access_level": "<new level or null>",
  "citation": "<policy section + SOC2 control>",
  "supporting_incident": "<incident id + short title, or null>",
  "simulation_check_required": "<what the Simulation Agent should verify>"
}
"""


class PolicyGenerationAgent:
    name = "Policy Generation Agent"

    def __init__(self, llm_client=None):
        self.llm = llm_client or get_llm_client()

    def _build_prompt(self, grant: dict, context: str) -> str:
        return f"""REMEDIATION PLAYBOOK + POLICY + INCIDENTS (grounding context from Foundry IQ):
{context}

FLAGGED ACCESS GRANT (with risk score):
{json.dumps(grant, indent=2)}

This is a policy generation task for grant {grant['grant_id']}. \
Draft the remediation policy per the playbook above."""

    def run(self, flagged_grants: list):
        """
        Args:
            flagged_grants: list of scored grant dicts from RiskScoringAgent

        Returns:
            {
                "policies": [...],  # one policy dict per flagged grant
                "log": [str, ...]
            }
        """
        log = [f"[{self.name}] Retrieving Remediation Playbook, Least Privilege Policy, "
               f"and Incident History from Foundry IQ knowledge base..."]

        context_results = kb.search(
            "remediation pattern intern admin access critical resource dormant onboarding template lingering project incident"
        )
        context = "\n\n".join(
            f"[{r['doc_id']}] {r['section']}\n{r['content']}" for r in context_results
        )

        log.append(
            f"[{self.name}] Retrieved {len(context_results)} grounding section(s): "
            + ", ".join(f"{r['doc_id']}/{r['section']}" for r in context_results)
        )

        policies = []

        for grant in flagged_grants:
            prompt = self._build_prompt(grant, context)
            response = self.llm.chat(SYSTEM_PROMPT, prompt)

            try:
                policy = json.loads(response)
            except json.JSONDecodeError:
                policy = {
                    "grant_id": grant["grant_id"],
                    "matched_pattern": "Unknown",
                    "recommended_action": "no_change",
                    "new_access_level": None,
                    "citation": "N/A",
                    "supporting_incident": None,
                    "simulation_check_required": "Could not parse model response.",
                }

            policy["user_name"] = grant["user_name"]
            policy["resource_name"] = grant["resource_name"]
            policy["current_access_level"] = grant["access_level"]
            policy["risk_score"] = grant.get("risk_score")
            policy["severity"] = grant.get("severity")
            policy["preferred_change_window"] = grant.get("preferred_change_window")

            policies.append(policy)

            action_desc = {
                "remove": "REMOVE access entirely",
                "downgrade": f"DOWNGRADE to {policy.get('new_access_level')}",
                "no_change": "NO CHANGE recommended",
            }.get(policy["recommended_action"], policy["recommended_action"])

            log.append(
                f"[{self.name}] {grant['grant_id']} ({grant['user_name']} -> "
                f"{grant['resource_name']}): {action_desc}. "
                f"Pattern: {policy.get('matched_pattern')}. "
                f"Citation: {policy.get('citation')}"
            )

        log.append(
            f"[{self.name}] Drafted {len(policies)} policy recommendation(s). "
            f"Handing to Simulation Agent for validation."
        )

        return {
            "policies": policies,
            "log": log,
        }


if __name__ == "__main__":
    from discovery_agent import DiscoveryAgent
    from risk_scoring_agent import RiskScoringAgent

    disc_result = DiscoveryAgent().run()
    risk_result = RiskScoringAgent().run(disc_result["grants"])

    agent = PolicyGenerationAgent()
    result = agent.run(risk_result["flagged_grants"])

    print("\n".join(result["log"]))
    print()
    print(json.dumps(result["policies"][0], indent=2))
