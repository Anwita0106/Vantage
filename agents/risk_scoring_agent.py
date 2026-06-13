"""
risk_scoring_agent.py

Risk Scoring Agent.

Responsibility: for each access grant from the Discovery Agent, score
the risk (1-10) using the Risk Scoring Rubric (Foundry IQ knowledge
base) as grounding context. Returns a severity label and explanation
for each grant.

Only grants scoring >= RISK_THRESHOLD are flagged for the Policy
Generation Agent.
"""

import json
import knowledge_base as kb
from llm_client import get_llm_client

RISK_THRESHOLD = 5  # Medium and above gets flagged for policy generation

SYSTEM_PROMPT = """You are the Risk Scoring Agent in Vantage, an autonomous \
access governance system. Your job is to evaluate a single access grant and \
assign a risk score from 1 (negligible) to 10 (critical).

You MUST ground your scoring in the Risk Scoring Rubric provided in the \
context below. Consider role-resource alignment, dormancy/usage, \
provisioning method, resource sensitivity, and tenure.

Respond ONLY with a JSON object in this exact shape, no other text:
{
  "grant_id": "<grant id>",
  "risk_score": <int 1-10>,
  "severity": "<Critical|High|Medium|Low>",
  "explanation": "<1-2 sentence explanation citing specific rubric factors>"
}
"""


class RiskScoringAgent:
    name = "Risk Scoring Agent"

    def __init__(self, llm_client=None):
        self.llm = llm_client or get_llm_client()

    def _build_prompt(self, grant: dict, rubric_context: str) -> str:
        return f"""RISK SCORING RUBRIC (grounding context from Foundry IQ):
{rubric_context}

ACCESS GRANT TO EVALUATE:
{json.dumps(grant, indent=2)}

Score this grant's risk per the rubric above."""

    def run(self, grants: list):
        """
        Args:
            grants: list of enriched grant dicts from DiscoveryAgent

        Returns:
            {
                "scored_grants": [...],   # all grants with risk_score/severity/explanation
                "flagged_grants": [...],  # subset with risk_score >= RISK_THRESHOLD
                "log": [str, ...]
            }
        """
        log = [f"[{self.name}] Retrieving Risk Scoring Rubric from Foundry IQ knowledge base..."]

        rubric_results = kb.search("risk scoring rubric role resource sensitivity dormant tenure")
        rubric_context = "\n\n".join(
            f"[{r['doc_id']}] {r['section']}\n{r['content']}" for r in rubric_results
        )

        log.append(
            f"[{self.name}] Retrieved {len(rubric_results)} grounding section(s): "
            + ", ".join(f"{r['doc_id']}/{r['section']}" for r in rubric_results)
        )

        scored_grants = []
        flagged_grants = []

        log.append(f"[{self.name}] Scoring {len(grants)} access grants...")

        for grant in grants:
            prompt = self._build_prompt(grant, rubric_context)
            response = self.llm.chat(SYSTEM_PROMPT, prompt)

            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                result = {
                    "grant_id": grant["grant_id"],
                    "risk_score": 1,
                    "severity": "Low",
                    "explanation": "Could not parse model response; defaulted to Low.",
                }

            scored = {**grant, **result}
            scored_grants.append(scored)

            if result.get("risk_score", 0) >= RISK_THRESHOLD:
                flagged_grants.append(scored)
                log.append(
                    f"[{self.name}] {grant['grant_id']} ({grant['user_name']} -> "
                    f"{grant['resource_name']}): risk={result.get('risk_score')} "
                    f"[{result.get('severity')}] -- FLAGGED for policy review"
                )

        log.append(
            f"[{self.name}] Completed scoring. {len(flagged_grants)} of {len(grants)} "
            f"grants flagged (risk >= {RISK_THRESHOLD}). Handing flagged grants to "
            f"Policy Generation Agent."
        )

        return {
            "scored_grants": scored_grants,
            "flagged_grants": flagged_grants,
            "log": log,
        }


if __name__ == "__main__":
    from discovery_agent import DiscoveryAgent

    discovery = DiscoveryAgent()
    disc_result = discovery.run()

    agent = RiskScoringAgent()
    result = agent.run(disc_result["grants"])

    print("\n".join(result["log"]))
    print()
    print(f"Flagged grants: {[g['grant_id'] for g in result['flagged_grants']]}")
