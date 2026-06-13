"""
test_server.py

Test client that connects to the Vantage MCP server over stdio
and calls each tool, exactly as an agent would via MCP.

Run with:
    python test_server.py
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    import sys
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools_result = await session.list_tools()
            print("=== Available Tools ===")
            for tool in tools_result.tools:
                print(f"- {tool.name}: {tool.description[:80]}...")
            print()

            # Test 1: get_user_access for Raj (EMP-002)
            print("=== Tool call: get_user_access(EMP-002) ===")
            result = await session.call_tool("get_user_access", {"user_id": "EMP-002"})
            print(result.content[0].text)
            print()

            # Test 2: check_dormant_access for Raj
            print("=== Tool call: check_dormant_access(EMP-002) ===")
            result = await session.call_tool("check_dormant_access", {"user_id": "EMP-002"})
            print(result.content[0].text)
            print()

            # Test 3: access graph summary
            print("=== Tool call: get_access_graph_summary() ===")
            result = await session.call_tool("get_access_graph_summary", {})
            print(result.content[0].text)
            print()

            # Test 4: resource owners for AWS billing console
            print("=== Tool call: get_resource_owners(RES-002) ===")
            result = await session.call_tool("get_resource_owners", {"resource_id": "RES-002"})
            print(result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
