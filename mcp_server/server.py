"""
server.py

Vantage MCP Server.

Exposes the access graph and activity data as MCP tools so that
Foundry agents can query user access, check dormancy, and look up
resource ownership via the Model Context Protocol instead of
direct function calls.

Run with:
    python server.py

This starts an MCP server over stdio, which can be referenced from
an MCP-compatible agent client (e.g., Foundry Agent Service, or the
Anthropic/OpenAI-compatible MCP client config).
"""

import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

import vantage_data as vd

server = Server("vantage-access-graph")

# Load data once at startup
_DATA = vd.load_all_data()
_GRAPH = vd.build_access_graph(_DATA)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_user_access",
            description=(
                "Get all access grants held by a specific user, including "
                "resource name, sensitivity, access level, and the reason "
                "on file for the grant. Use this to understand what a "
                "user currently has access to."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The user ID, e.g. 'EMP-002'",
                    }
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="check_dormant_access",
            description=(
                "Check a user's access grants against the 30-day activity log "
                "to identify which grants are dormant (zero usage) versus "
                "actively used. Use this before recommending or validating "
                "an access removal/downgrade."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The user ID, e.g. 'EMP-002'",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to check (default 30)",
                        "default": 30,
                    },
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="get_all_grants_with_context",
            description=(
                "Return every access grant in the organization, enriched with "
                "user role/department/tenure, resource sensitivity, and "
                "30-day activity data. This is the primary dataset for "
                "risk scoring across the whole organization."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_resource_owners",
            description=(
                "Get all users who currently have access to a specific resource, "
                "along with their access level and role."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_id": {
                        "type": "string",
                        "description": "The resource ID, e.g. 'RES-002'",
                    }
                },
                "required": ["resource_id"],
            },
        ),
        Tool(
            name="get_access_graph_summary",
            description=(
                "Get a high-level summary of the organization's access graph: "
                "total users, total resources, total access grants, and a "
                "breakdown of access levels by resource sensitivity. Use this "
                "for an overall organizational risk overview."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_user_access":
        result = vd.get_user_access(arguments["user_id"], data=_DATA)

    elif name == "check_dormant_access":
        result = vd.check_dormant_access(
            arguments["user_id"],
            days=arguments.get("days", 30),
            data=_DATA,
        )

    elif name == "get_all_grants_with_context":
        result = vd.get_all_grants_with_context(data=_DATA)

    elif name == "get_resource_owners":
        result = vd.get_resource_owners(arguments["resource_id"], data=_DATA)

    elif name == "get_access_graph_summary":
        result = _build_graph_summary()

    else:
        result = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


def _build_graph_summary():
    user_nodes = [n for n, d in _GRAPH.nodes(data=True) if d.get("node_type") == "user"]
    resource_nodes = [n for n, d in _GRAPH.nodes(data=True) if d.get("node_type") == "resource"]

    sensitivity_breakdown = {}
    for u, r, edge_data in _GRAPH.edges(data=True):
        res_sensitivity = _GRAPH.nodes[r].get("sensitivity", "unknown")
        access_level = edge_data.get("access_level", "unknown")
        key = f"{res_sensitivity}_{access_level}"
        sensitivity_breakdown[key] = sensitivity_breakdown.get(key, 0) + 1

    return {
        "total_users": len(user_nodes),
        "total_resources": len(resource_nodes),
        "total_access_grants": _GRAPH.number_of_edges(),
        "access_breakdown_by_sensitivity_and_level": sensitivity_breakdown,
    }


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
