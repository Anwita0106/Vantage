"""
discovery_agent.py

Discovery Agent.

Responsibility: map out the organization's access landscape by querying
the Vantage MCP server for the full enriched grant list and the access
graph summary. Produces a structured overview that downstream agents
(Risk Scoring, Policy Generation, Simulation) consume.

This agent primarily performs data retrieval via MCP tools rather than
LLM reasoning -- it represents the "Discovery" stage of the pipeline:
build the access graph (Fabric IQ semantic model pattern) and summarize it.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp_server"))
import vantage_data as vd


class DiscoveryAgent:
    name = "Discovery Agent"

    def run(self, data=None):
        """
        Returns:
            {
                "summary": {...graph summary...},
                "grants": [...enriched grant list...],
                "log": [str, ...]  # human-readable reasoning trace
            }
        """
        if data is None:
            data = vd.load_all_data()

        graph = vd.build_access_graph(data)
        grants = vd.get_all_grants_with_context(data)

        user_count = sum(1 for _, d in graph.nodes(data=True) if d.get("node_type") == "user")
        resource_count = sum(1 for _, d in graph.nodes(data=True) if d.get("node_type") == "resource")

        log = [
            f"[{self.name}] Connected to access graph via MCP server.",
            f"[{self.name}] Discovered {user_count} users, {resource_count} resources, "
            f"{graph.number_of_edges()} access grants.",
            f"[{self.name}] Built semantic access graph (Fabric IQ pattern): "
            f"User --HAS_ACCESS--> Resource, with role/department/sensitivity attributes.",
            f"[{self.name}] Handing enriched grant list to Risk Scoring Agent.",
        ]

        return {
            "summary": {
                "user_count": user_count,
                "resource_count": resource_count,
                "grant_count": graph.number_of_edges(),
            },
            "grants": grants,
            "log": log,
        }


if __name__ == "__main__":
    import json
    agent = DiscoveryAgent()
    result = agent.run()
    print("\n".join(result["log"]))
    print()
    print(f"Total grants discovered: {len(result['grants'])}")
    print(json.dumps(result["grants"][4], indent=2))  # show GR-005 (Raj's billing access)
