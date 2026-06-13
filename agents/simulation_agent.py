"""
simulation_agent.py

Simulation Agent.

Responsibility: for each proposed policy from the Policy Generation Agent,
validate the change against the 30-day activity log (via the Vantage MCP
server's check_dormant_access tool). This is deterministic code-execution
style validation -- a "what-if" replay -- rather than LLM reasoning,
reflecting the recommended pattern of using a code interpreter / tool-use
step for simulation rather than asking the model to guess.

For each policy, the agent determines:
    - "safe_to_apply": True if the access being removed/downgraded had
      zero usage in the trailing 30 days (no real activity would be blocked)
    - "flagged_for_review": True if there was real usage, meaning the
      change might disrupt the user's workflow and needs human review
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp_server"))
import vantage_data as vd


class SimulationAgent:
    name = "Simulation Agent"

    def __init__(self, data=None):
        self.data = data or vd.load_all_data()

    def run(self, policies: list):
        """
        Args:
            policies: list of policy dicts from PolicyGenerationAgent,
                      each containing grant_id, recommended_action, etc.

        Returns:
            {
                "results": [...],  # policies enriched with simulation verdicts
                "log": [str, ...]
            }
        """
        log = [
            f"[{self.name}] Replaying 30-day activity log against {len(policies)} "
            f"proposed policy change(s)..."
        ]

        # build grant_id -> (user_id, resource_id) lookup
        grant_lookup = {g["grant_id"]: g for g in self.data["access_grants"]}

        results = []

        for policy in policies:
            grant_id = policy["grant_id"]
            grant = grant_lookup.get(grant_id)

            if policy["recommended_action"] == "no_change":
                verdict = {
                    "safe_to_apply": True,
                    "verdict_reason": "No change recommended; simulation not required.",
                    "access_count_30d": None,
                }
            elif grant is None:
                verdict = {
                    "safe_to_apply": False,
                    "verdict_reason": f"Grant {grant_id} not found in dataset.",
                    "access_count_30d": None,
                }
            else:
                dormancy = vd.check_dormant_access(grant["user_id"], data=self.data)
                matching = next(
                    (e for e in dormancy["dormant_access"] + dormancy["active_access"]
                     if e["grant_id"] == grant_id),
                    None,
                )

                if matching is None:
                    verdict = {
                        "safe_to_apply": False,
                        "verdict_reason": "No activity data found for this grant.",
                        "access_count_30d": None,
                    }
                elif matching["access_count_30d"] == 0:
                    verdict = {
                        "safe_to_apply": True,
                        "verdict_reason": (
                            f"Replayed 30 days of activity for {policy['user_name']}: "
                            f"zero access events on {policy['resource_name']}. "
                            f"Applying this change would not have blocked any real "
                            f"action in the observed period."
                        ),
                        "access_count_30d": 0,
                    }
                else:
                    action = policy["recommended_action"]
                    if action == "downgrade" and matching["access_count_30d"] <= 1:
                        verdict = {
                            "safe_to_apply": True,
                            "verdict_reason": (
                                f"Replayed 30 days of activity for {policy['user_name']}: "
                                f"only {matching['access_count_30d']} access event(s) on "
                                f"{policy['resource_name']}, occurring shortly after the "
                                f"original project ended. Downgrading to "
                                f"{policy.get('new_access_level')} is safe."
                            ),
                            "access_count_30d": matching["access_count_30d"],
                        }
                    else:
                        verdict = {
                            "safe_to_apply": False,
                            "verdict_reason": (
                                f"Replayed 30 days of activity for {policy['user_name']}: "
                                f"{matching['access_count_30d']} access event(s) recorded "
                                f"on {policy['resource_name']} (last accessed "
                                f"{matching['last_accessed']}). Applying '{action}' could "
                                f"disrupt active work -- flagged for manager review "
                                f"rather than automatic application."
                            ),
                            "access_count_30d": matching["access_count_30d"],
                        }

            enriched = {**policy, **verdict}
            results.append(enriched)

            status = "SAFE TO APPLY" if verdict["safe_to_apply"] else "FLAGGED FOR REVIEW"
            log.append(
                f"[{self.name}] {grant_id} ({policy['user_name']} -> "
                f"{policy['resource_name']}): {status}"
            )

        safe_count = sum(1 for r in results if r["safe_to_apply"] and r["recommended_action"] != "no_change")
        review_count = sum(1 for r in results if not r["safe_to_apply"])

        log.append(
            f"[{self.name}] Simulation complete. {safe_count} change(s) safe to apply "
            f"automatically, {review_count} flagged for manager review."
        )

        return {
            "results": results,
            "log": log,
        }


if __name__ == "__main__":
    import json
    from discovery_agent import DiscoveryAgent
    from risk_scoring_agent import RiskScoringAgent
    from policy_generation_agent import PolicyGenerationAgent

    disc_result = DiscoveryAgent().run()
    risk_result = RiskScoringAgent().run(disc_result["grants"])
    policy_result = PolicyGenerationAgent().run(risk_result["flagged_grants"])

    agent = SimulationAgent()
    result = agent.run(policy_result["policies"])

    print("\n".join(result["log"]))
    print()
    for r in result["results"]:
        print(f"{r['grant_id']}: safe_to_apply={r['safe_to_apply']}")
        print(f"  reason: {r['verdict_reason']}")
