"""
mcp_client.py — MCP Client: Connecting to External Tool Servers
================================================================

This file shows how MCP (Model Context Protocol) works. MCP is a
STANDARD PROTOCOL that lets AI agents discover and use tools from
EXTERNAL SERVERS — instead of hardcoding tools in your own code.

THE BIG IDEA:
  In tools.py, we hardcoded every tool: web_search, read_file, etc.
  That works, but it doesn't scale. What if you want your agent to
  talk to Jira? Confluence? Slack? GitHub? You'd have to write and
  maintain all those integrations yourself.

  MCP solves this: someone else builds a "tool server" (e.g. Atlassian
  builds one for Jira/Confluence), and your agent connects to it over
  a standard protocol. The server tells the agent what tools exist,
  and the agent can call them — WITHOUT knowing anything about the
  Jira API, authentication, etc.

  Think of it like USB: you don't need a custom driver for every
  device. You just plug it in and it works.

HOW IT WORKS:
  1. Your agent starts an MCP server as a subprocess (via stdio)
  2. It asks the server: "What tools do you have?" (list_tools)
  3. The server responds with tool schemas (name, description, parameters)
  4. When the LLM wants to call a tool, your agent sends a "call_tool"
     message to the server
  5. The server executes the tool and returns the result
  6. Your agent sends the result back to the LLM

  The protocol is JSON-RPC over stdin/stdout. That's it.

THIS DEMO USES: mcp-atlassian (pip install mcp-atlassian)
  - Connects to Jira and Confluence
  - Exposes tools like jira_search, jira_get_issue, confluence_search, etc.
  - See: https://github.com/sooperset/mcp-atlassian
"""

import asyncio
import json
import os
from contextlib import AsyncExitStack
from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client


# ============================================================
# SECTION 1: THE MCP CLIENT CLASS
# ============================================================
# This class wraps the MCP protocol into a simple interface:
#   connect()    → start the server, discover tools
#   call_tool()  → execute a tool on the server
#   close()      → shut down the server
#
# KEY INSIGHT: The agent doesn't need to know HOW the tools
# work internally. It just knows their names and schemas —
# exactly like how it works with our hardcoded tools, but
# the implementations live in a SEPARATE process.
# ============================================================

class MCPClient:
    """
    A client that connects to an MCP server, discovers its tools,
    and can call them on behalf of the AI agent.
    """

    def __init__(self):
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self.tools = []           # Raw MCP tool definitions
        self.openai_tools = []    # Tools converted to OpenAI format

    async def connect(self, command: str, args: list[str] = None, env: dict = None, cwd: str = None):
        """
        Start an MCP server and establish a connection.

        This does three things:
          1. Launches the server as a subprocess (via stdio)
          2. Performs the MCP handshake (initialize)
          3. Discovers all available tools (list_tools)

        Args:
            command: The command to run the MCP server (e.g. "mcp-atlassian")
            args: Command arguments (e.g. ["--transport", "stdio"])
            env: Environment variables for the server (API keys, URLs, etc.)
            cwd: Working directory for the server process
        """
        # ── Build the server parameters ─────────────────────────
        # StdioServerParameters tells the MCP client HOW to start
        # the server. The server runs as a subprocess, and the
        # client talks to it over stdin/stdout using JSON-RPC.
        server_env = {**os.environ, **(env or {})}
        server_params = StdioServerParameters(
            command=command,
            args=args or ["--transport", "stdio"],
            env=server_env,
            cwd=cwd,
        )

        # ── Start the server and connect ────────────────────────
        # stdio_client launches the subprocess and gives us
        # read/write streams. ClientSession wraps those streams
        # in a nice API for sending MCP messages.
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read_stream, write_stream = stdio_transport

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        # ── MCP Handshake: Initialize ───────────────────────────
        # This is like a TCP handshake — the client and server
        # agree on protocol version and capabilities.
        await self.session.initialize()

        # ── Discover tools ──────────────────────────────────────
        # Ask the server: "What tools do you have?"
        # The server responds with a list of tool schemas.
        # This is the MAGIC of MCP — tools are discovered at
        # runtime, not hardcoded at compile time.
        tools_response = await self.session.list_tools()
        self.tools = tools_response.tools

        # ── Convert to OpenAI format ────────────────────────────
        # MCP uses its own schema format. OpenAI's API expects a
        # different format. We need to translate between them.
        # This is a one-time conversion when we connect.
        self.openai_tools = [self._mcp_to_openai(tool) for tool in self.tools]

        return self.tools

    def _mcp_to_openai(self, mcp_tool) -> dict:
        """
        Convert an MCP tool schema to OpenAI's tool format.

        MCP format:
          { name: "jira_search", description: "...", inputSchema: { type: "object", properties: {...} } }

        OpenAI format:
          { type: "function", function: { name: "jira_search", description: "...", parameters: {...} } }

        This translation is needed because MCP and OpenAI use
        different JSON schema conventions. The actual tool
        capabilities are the same — just different packaging.
        """
        return {
            "type": "function",
            "function": {
                "name": mcp_tool.name,
                "description": mcp_tool.description or "",
                "parameters": mcp_tool.inputSchema if mcp_tool.inputSchema else {
                    "type": "object",
                    "properties": {},
                },
            },
        }

    async def call_tool(self, name: str, arguments: dict) -> str:
        """
        Call a tool on the MCP server and return the result.

        This sends a JSON-RPC "tools/call" message to the server,
        waits for the response, and returns the result as a string.

        The server does all the heavy lifting — authenticating with
        Jira, making API calls, formatting results, etc. Our agent
        just sends the tool name and arguments and gets back text.
        """
        if not self.session:
            return "Error: MCP client is not connected. Call connect() first."

        try:
            result = await self.session.call_tool(name, arguments)

            # MCP returns a list of content blocks (text, images, etc.)
            # We concatenate the text blocks into a single string.
            output_parts = []
            for block in result.content:
                if hasattr(block, "text"):
                    output_parts.append(block.text)
                else:
                    output_parts.append(str(block))

            return "\n".join(output_parts) if output_parts else "(empty result)"

        except Exception as e:
            return f"Error calling MCP tool '{name}': {e}"

    async def close(self):
        """Shut down the MCP server and clean up."""
        await self.exit_stack.aclose()
        self.session = None

    def get_tool_names(self) -> list[str]:
        """Get just the names of all available tools."""
        return [tool.name for tool in self.tools]


# ============================================================
# SECTION 2: HELPER — BUILD THE ATLASSIAN MCP CLIENT
# ============================================================
# This is a convenience function that creates an MCPClient
# pre-configured for the Atlassian MCP server. It reads
# connection details from environment variables.
# ============================================================

async def create_atlassian_client() -> MCPClient:
    """
    Create and connect an MCP client to the Atlassian MCP server.

    Required environment variables (set in .env):
      ATLASSIAN_URL      — e.g. https://yoursite.atlassian.net
      ATLASSIAN_USERNAME — e.g. you@example.com
      ATLASSIAN_API_TOKEN — from https://id.atlassian.com/manage-profile/security/api-tokens

    On Atlassian Cloud, Jira and Confluence share the same site and
    credentials — so we use ONE set of config for both.
    Confluence lives at {ATLASSIAN_URL}/wiki automatically.
    """
    client = MCPClient()

    # Build env vars for the MCP server from our .env
    # Jira and Confluence on Atlassian Cloud use the SAME credentials.
    # The MCP server expects separate env vars, but we derive them
    # from a single set so the user doesn't have to duplicate config.
    atlassian_url = os.getenv("ATLASSIAN_URL", "")
    username = os.getenv("ATLASSIAN_USERNAME", "")
    api_token = os.getenv("ATLASSIAN_API_TOKEN", "")

    env = {
        "JIRA_URL": atlassian_url,
        "JIRA_USERNAME": username,
        "JIRA_API_TOKEN": api_token,
        "CONFLUENCE_URL": atlassian_url.rstrip("/") + "/wiki",
        "CONFLUENCE_USERNAME": username,
        "CONFLUENCE_API_TOKEN": api_token,
    }

    # Set cwd to our project directory so the MCP server finds
    # THIS .env file — not a stray one in a parent directory.
    project_dir = os.path.dirname(os.path.abspath(__file__))

    await client.connect(
        command="mcp-atlassian",
        args=["--transport", "stdio"],
        env=env,
        cwd=project_dir,
    )

    return client
