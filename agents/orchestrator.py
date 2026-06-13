"""
orchestrator.py

Vantage Pipeline Orchestrator.

Runs the full multi-agent pipeline in sequence:
    Discovery -> Risk Scoring -> Policy Generation -> Simulation

Combines each agent's reasoning log into a single ordered trace, and
produces the final structured result consumed by the API/UI:
    - graph data (before/after, for visualization)
    - flagged grants with risk scores
    - policy recommendations with citations
    - simulation verdicts
    - full agent log
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp_server"))
import vantage_data as vd

from discovery_agent import DiscoveryAgent
from risk_scoring_agent import RiskScoringAgent
from policy_generation_agent import PolicyGenerationAgent
from simulation_agent import SimulationAgent


class VantageOrchestrator:
    def __init__(self):
        self.data = vd.load_all_data()
        self.discovery = DiscoveryAgent()
        self.risk_scoring = RiskScoringAgent()
        self.policy_generation = PolicyGenerationAgent()
        self.simulation = SimulationAgent(data=self.data)

    def run(self):
        full_log = []

        # 1. Discovery
        disc_result = self.discovery.run(data=self.data)
        full_log.extend(disc_result["log"])

        # 2. Risk Scoring
        risk_result = self.risk_scoring.run(disc_result["grants"])
        full_log.extend(risk_result["log"])

        # 3. Policy Generation
        policy_result = self.policy_generation.run(risk_result["flagged_grants"])
        full_log.extend(policy_result["log"])

        # 4. Simulation
        sim_result = self.simulation.run(policy_result["policies"])
        full_log.extend(sim_result["log"])

        policy_lookup = {r["grant_id"]: r for r in sim_result["results"]}

        # Build graph data for visualization (before state)
        graph_before = self._build_graph_payload(
            highlight_grant_ids=set(),
            policy_lookup=policy_lookup,
        )

        # Determine which grants are removed/downgraded in the "after" state
        applied_changes = {
            r["grant_id"]: r for r in sim_result["results"]
            if r["safe_to_apply"] and r["recommended_action"] != "no_change"
        }

        graph_after = self._build_graph_payload(
            highlight_grant_ids=set(applied_changes.keys()),
            applied_changes=applied_changes,
            policy_lookup=policy_lookup,
        )

        return {
            "summary": disc_result["summary"],
            "scored_grants": risk_result["scored_grants"],
            "flagged_grants": risk_result["flagged_grants"],
            "policies": sim_result["results"],
            "graph_before": graph_before,
            "graph_after": graph_after,
            "agent_log": full_log,
            "stats": {
                "total_grants": disc_result["summary"]["grant_count"],
                "flagged_count": len(risk_result["flagged_grants"]),
                "safe_to_apply_count": len(applied_changes),
                "flagged_for_review_count": sum(
                    1 for r in sim_result["results"] if not r["safe_to_apply"]
                ),
            },
        }

    def _build_graph_payload(self, highlight_grant_ids, applied_changes=None, policy_lookup=None):
        """
        Build a graph JSON payload (nodes + edges) for the frontend.

        - "before" graph: all edges as-is, with risk-based coloring for
          flagged grants
        - "after" graph: edges in applied_changes are either removed
          (action=remove) or relabeled (action=downgrade)
        """
        applied_changes = applied_changes or {}

        # severity color map
        severity_colors = {
            "Critical": "#dc2626",
            "High": "#f97316",
            "Medium": "#eab308",
            "Low": "#22c55e",
        }

        # build severity lookup from scored grants (re-run discovery+risk for this)
        # NOTE: caller should pass the same risk_result; for simplicity here we
        # recompute via a fresh discovery+risk pass on cached data (cheap, mock/local)
        disc = self.discovery.run(data=self.data)
        risk = self.risk_scoring.run(disc["grants"])
        severity_by_grant = {
            g["grant_id"]: g.get("severity", "Low") for g in risk["scored_grants"]
        }

        nodes = []
        for user in self.data["users"]:
            nodes.append({
                "id": user["user_id"],
                "label": user["name"],
                "type": "user",
                "role": user["role"],
                "department": user["department"],
            })
        for res in self.data["resources"]:
            nodes.append({
                "id": res["resource_id"],
                "label": res["name"],
                "type": "resource",
                "sensitivity": res["sensitivity"],
            })

        edges = []
        for grant in self.data["access_grants"]:
            grant_id = grant["grant_id"]

            policy = policy_lookup.get(grant_id, {}) if policy_lookup else {}
            recommended_action = policy.get("recommended_action") or "no_change"
            risk_score = policy.get("risk_score")

            if grant_id in highlight_grant_ids:
                change = applied_changes[grant_id]
                if change["recommended_action"] == "remove":
                    # edge removed in "after" graph
                    continue
                elif change["recommended_action"] == "downgrade":
                    edges.append({
                        "source": grant["user_id"],
                        "target": grant["resource_id"],
                        "grant_id": grant_id,
                        "access_level": change.get("new_access_level"),
                        "severity": "Low",
                        "color": severity_colors["Low"],
                        "changed": True,
                        "risk_score": risk_score,
                        "recommended_action": recommended_action,
                        "user_name": grant.get("user_name") or grant.get("user_id"),
                        "resource_name": grant.get("resource_name") or grant.get("resource_id"),
                    })
                    continue

            severity = severity_by_grant.get(grant_id, "Low")
            edges.append({
                "source": grant["user_id"],
                "target": grant["resource_id"],
                "grant_id": grant_id,
                "access_level": grant["access_level"],
                "severity": severity,
                "color": severity_colors.get(severity, "#94a3b8"),
                "changed": False,
                "risk_score": risk_score,
                "recommended_action": recommended_action,
                "user_name": grant.get("user_name") or grant.get("user_id"),
                "resource_name": grant.get("resource_name") or grant.get("resource_id"),
            })

        return {"nodes": nodes, "edges": edges}


if __name__ == "__main__":
    orchestrator = VantageOrchestrator()
    result = orchestrator.run()

    print("=== AGENT LOG ===")
    for line in result["agent_log"]:
        print(line)

    print()
    print("=== STATS ===")
    print(json.dumps(result["stats"], indent=2))

    print()
    print("=== GRAPH BEFORE (edge count) ===", len(result["graph_before"]["edges"]))
    print("=== GRAPH AFTER (edge count) ===", len(result["graph_after"]["edges"]))
