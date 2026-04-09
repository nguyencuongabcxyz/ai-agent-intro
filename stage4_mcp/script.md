# Stage 4: MCP — Dynamic Tool Discovery

## What to Tell the Audience

### Opening (1 min)

- "What if I told you the agent loop we wrote hasn't changed since Stage 2? And it's still not changing."
- "The only thing that changes is WHERE the tools come from. In Stage 3, they were hardcoded. Now, the agent **discovers** them at runtime from an external server."
- "This is MCP — Model Context Protocol. Think of it as **USB-C for AI agents**."

### Core Concept (3 min)

- MCP is a **standard protocol** created by Anthropic (open-sourced late 2024).
- Instead of writing tool code inside your agent, you connect to an **MCP server** that provides tools.
- The handshake:
  1. Agent starts the MCP server as a subprocess
  2. Agent asks: "What tools do you have?" (`list_tools`)
  3. Server responds with tool schemas (same format as our hardcoded ones!)
  4. When the LLM wants to call a tool, agent sends `call_tool` to the server
  5. Server executes it and returns the result
- The protocol is **JSON-RPC over stdin/stdout**. That's it.

### Walk Through the Code (3 min)

- **`mcp_client.py`** — the MCP client class:
  - `connect()` (line 75): starts server, does handshake, discovers tools
  - `_mcp_to_openai()` (line 136): converts MCP tool format → OpenAI tool format
  - `call_tool()` (line 162): sends a tool call to the server and gets the result
- **`agent.py`** — the agent:
  - `build_system_prompt()` (line 109): dynamically lists discovered tool names
  - Line 167: `tools=mcp.openai_tools` — uses discovered tools instead of hardcoded ones
  - Line 201: `await mcp.call_tool(name, args)` — routes to MCP server instead of local function
  - **The loop is identical to Stage 2/3!**

---

## What to Explain Further

### Why MCP Matters

- **Before MCP**: Every agent builds its own Jira integration, its own Slack integration, etc. Duplicated work.
- **After MCP**: Someone builds ONE MCP server for Jira. Every agent (Claude Code, Cursor, your custom agent) can use it.
- It's the same pattern as REST APIs, but specifically designed for AI tool calling.

### The MCP Ecosystem

- **1000+ community MCP servers** available: GitHub, Postgres, Notion, Figma, Slack, Google Drive, etc.
- Claude Code supports MCP natively — you configure servers in your settings.
- Cursor also supports MCP.
- You can build your own MCP server for internal tools in ~50 lines of Python.

### MCP vs REST API

| Aspect    | REST API                      | MCP Server                            |
| --------- | ----------------------------- | ------------------------------------- |
| Discovery | Read docs, hardcode endpoints | Automatic via `list_tools`            |
| Schema    | You interpret OpenAPI specs   | Server provides tool schemas directly |
| Auth      | You manage tokens, sessions   | Server handles internally             |
| Format    | Agent-specific                | Universal standard                    |

### This Demo: Atlassian MCP

- We connect to `mcp-atlassian` — a community MCP server for Jira + Confluence.
- It exposes tools like `jira_search`, `jira_get_issue`, `confluence_search`, etc.
- Our agent doesn't know anything about the Jira API. It just calls tools.

---

## Demo Examples

### Demo 1: Discover Tools

```bash
python agent.py
```

- Just start the agent and watch it connect to the MCP server.
- Point out the "Discovered X tools" message — these were NOT in our code.
- "The agent didn't know about Jira 5 seconds ago. Now it has 20+ Jira tools."

### Demo 2: Search Jira (requires Atlassian setup)

```
> Search for open bugs assigned to me in Jira
```

- Watch: the agent calls `jira_search` with a JQL query it constructed itself.
- "We never taught it JQL. The LLM figured it out from the tool description."

### Demo 3: Cross-Tool Task (requires Atlassian setup)

```
> Find the latest sprint in project XYZ and summarize what's in progress
```

- Watch: multiple MCP tool calls chained together.
- "Same loop as Stage 2. The agent just has different tools available."

### Fallback Demo (if no Atlassian setup)

- Show the code and explain the flow conceptually.
- Show the `mcp_client.py` connect/discover/call pattern.
- "Even without running it, notice: the agent loop file is nearly identical to Stage 3. Only the import changed."

---

## Transition to Stage 5

> "We have a smart agent with powerful tools. But try this: tell it your name, then ask it what your name is in the next turn. It forgets. Every turn is a blank slate. Stage 5 fixes that."

NOTE: summarize the CI/CD deployement of my app documented at https://sioux.atlassian.net/wiki/spaces/SC/pages/3809476625/CI+CD
