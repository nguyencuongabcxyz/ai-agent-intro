# Educational AI Agent — Progressive Demo

A from-scratch AI agent built to demonstrate how AI agents work. No frameworks, no magic — just a Python while loop, the OpenAI API, and some tools.

The project is split into **5 progressive stages**. Each stage introduces one new concept, building on the previous. Start with Stage 1 and work your way up.

## The 5 Stages

| Stage | File | Concept | What's New |
|-------|------|---------|------------|
| 1 | `stage1_llm.py` | **LLM Only** | Raw LLM API call. A simple chatbot — no tools, no loop, no memory. |
| 2 | `stage2_agent_loop.py` | **Agent Loop** | The `while` loop + 2 inline tools. This is what turns an LLM into an agent. |
| 3 | `stage3_agent_tools.py` + `tools.py` | **Full Tools** | 7 tools in a separate module. Schemas, registry, dispatcher pattern. |
| 4 | `stage4_agent_mcp.py` + `mcp_client.py` | **MCP** | Dynamic tool discovery from an external MCP server (Atlassian). |
| 5 | `stage5_agent_session.py` | **Session Memory** | Multi-turn conversations — the agent remembers everything. |

### Stage 1: LLM Only (`stage1_llm.py`)
The simplest possible AI app. Send text to the LLM, get text back. It can't search the web, read files, or take any actions. Each turn is completely independent — no memory.

**Key takeaway**: The LLM is just a text-in, text-out API. Everything else must be built on top.

### Stage 2: Agent Loop (`stage2_agent_loop.py`)
Adds the **agent loop** — a `while` loop that calls the LLM, checks for tool calls, executes them, and loops back. Uses 2 simple tools (web_search, read_file) inline to keep the focus on the loop.

**Key takeaway**: The agent loop IS the agent. The LLM decides when to stop by not calling tools. This is what Cursor, Claude Code, and every AI coding tool does under the hood.

### Stage 3: Full Tools (`stage3_agent_tools.py` + `tools.py`)
Extracts tools into a proper module with 7 tools: web_search, fetch_webpage, list_files, read_file, write_file, run_bash, run_background. Introduces the dispatcher pattern.

**Key takeaway**: Tools are the agent's "hands". The LLM never runs code — the harness/dispatcher bridges intent to execution. Same loop, more capabilities.

### Stage 4: MCP (`stage4_agent_mcp.py` + `mcp_client.py`)
Replaces hardcoded tools with dynamically discovered tools from an external MCP server. Same agent loop, different tool backend.

**Key takeaway**: MCP is like USB for AI — plug in any tool server. The agent loop doesn't change; only WHERE tool calls are routed changes.

### Stage 5: Session Memory (`stage5_agent_session.py`)
Adds multi-turn memory by keeping the `messages` list across turns instead of resetting it. The agent remembers the entire conversation.

**Key takeaway**: LLMs have no built-in memory. "Memory" is just keeping and re-sending the messages list. This is how ChatGPT and Claude work.

## What is an AI Agent?

A **chatbot** takes one input and gives one output. One shot. Done.

An **AI agent** takes one input and **loops** — calling tools, reading results, reasoning, calling more tools — until the task is complete. The difference is literally a `while` loop.

```
User: "Find the weather in Hanoi and write it to a file"

Chatbot (Stage 1): "I can't do that, I don't have access to the internet."

Agent (Stage 2+):
  → Thinks: "I need to search the web first"
  → Calls: web_search("weather in Hanoi today")
  → Gets result: "28°C, partly cloudy..."
  → Thinks: "Now I need to write this to a file"
  → Calls: write_file("weather.txt", "Hanoi: 28°C, partly cloudy...")
  → Gets result: "Successfully wrote to weather.txt"
  → Returns: "Done! Saved the weather to weather.txt"
```

## How It Maps to Real Tools

| This Agent | Cursor / Claude Code / Copilot |
|---|---|
| `SYSTEM_PROMPT` | System prompt (much longer, with many rules) |
| `while` loop in `run_agent()` | The agent loop (same concept, more sophisticated) |
| `TOOL_SCHEMAS` | Tool definitions (dozens of tools: edit file, search code, run tests...) |
| `execute_tool()` | Tool harness (with permissions, sandboxing, safety checks) |
| `messages` list | Context window (with compression, summarization for long conversations) |
| No tool calls = done | Same, plus additional stop conditions |

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create your .env file
cp .env.example .env

# 3. Add your OpenAI API key to .env
#    Edit .env and replace sk-your-key-here with your real key

# 4. Run any stage!
python stage1_llm.py              # Start here
python stage2_agent_loop.py       # Add the loop
python stage3_agent_tools.py      # Full tools
python stage4_agent_mcp.py        # MCP (needs Atlassian config)
python stage5_agent_session.py    # Multi-turn memory
```

## What to Watch in the Terminal

When the agent runs, you'll see colored output showing every step:

- **[SYSTEM PROMPT]** (blue) — The instructions sent to the LLM
- **[USER TASK]** — What you asked the agent to do
- **[ITERATION N]** — Which loop iteration + message count (Stages 2+)
- **[LLM RESPONSE]** (green) — What the LLM says
- **[TOOL CALL]** (yellow) — The LLM requesting to use a tool (Stages 2+)
- **[TOOL RESULT]** (cyan) — What came back from running that tool (Stages 2+)
- **[SESSION]** — Message count in memory (Stage 5)
- **[AGENT FINISHED]** (magenta) — The task is done

## Architecture Diagram

```
          ┌─────────────────────┐
          │    User's Task       │
          └──────────┬──────────┘
                     │
                     ▼
   ┌─────────────────────────────────┐
   │        System Prompt            │  ◄── Defines agent behavior
   │      + User Message             │
   │      = Initial Messages         │
   └──────────────┬──────────────────┘
                  │
        ┌─────────▼─────────┐
        │                   │
        │    LLM API Call   │  ◄── Send ALL messages + tool schemas
        │                   │
        └─────────┬─────────┘
                  │
          ┌───────┴───────┐
          │               │
     Tool calls?     Text only?
          │               │
          ▼               ▼
   ┌─────────────┐  ┌──────────┐
   │ Execute     │  │  DONE!   │  ◄── Stop condition
   │ Tool(s)     │  │  Return  │
   └──────┬──────┘  └──────────┘
          │
          ▼
   Add results to
   message history
          │
          └──────── Loop back to LLM API Call
```

Anatomy of an AI Agent

From Genius to Agent

How a Trapped Genius Learned to Act
