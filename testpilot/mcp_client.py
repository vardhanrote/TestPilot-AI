
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVER_PATH = PROJECT_ROOT / "mcp_tools" / "server.py"


async def call_mcp_tool(
    tool_name: str,
    arguments: dict | None = None,
) -> dict:
    """
    Launch the local MCP server and call one allowlisted tool.
    """
    allowed_tools = {
        "inspect_synthetic_source",
        "run_empty_list_diagnostic",
        "run_division_by_zero_diagnostic",
        "run_empty_list_regression_tests",
        "run_division_regression_tests",
    }

    if tool_name not in allowed_tools:
        raise ValueError(f"Tool is not allowed: {tool_name}")

    if not SERVER_PATH.exists():
        raise FileNotFoundError(
            f"MCP server file not found: {SERVER_PATH}"
        )

    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(server_parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments=arguments or {},
            )

            if result.isError:
                raise RuntimeError(
                    f"MCP tool failed: {tool_name}"
                )

            structured = getattr(result, "structuredContent", None)

            if structured is not None:
                return structured

            # Fallback for servers that return JSON as text.
            import json

            for item in result.content:
                if getattr(item, "type", None) == "text":
                    try:
                        return json.loads(item.text)
                    except json.JSONDecodeError:
                        continue

            raise RuntimeError(
                "MCP tool returned no structured result."
            )
