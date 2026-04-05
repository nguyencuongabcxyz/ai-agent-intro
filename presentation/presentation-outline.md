# Anatomy of an AI Agent — Presentation Outline

A step-by-step walkthrough that builds a simple AI agent from scratch, introducing each core concept along the way. By the end, the audience understands exactly what happens inside tools like Claude Code, Cursor, and Devin.

---

## Opening — The Question (2 min)

- You use Cursor, Claude Code, Copilot daily. **What's actually inside?**
- Show a short clip/screenshot of Claude Code doing a multi-step task (reading files, editing, running tests)
- "By the end of this session, you'll know exactly what just happened. Because we're going to build it."

---

## Agenda
a
| # | Stage | Code File | Concept |
|---|-------|-----------|---------|
| 1 | The Brain | `stage1_llm.py` | LLM Integration |
| 2 | The Loop | `stage2_agent_loop.py` | Agent Loop |
| 3 | The Tools | `stage3_agent_tools.py` | Tool Architecture |
| 4 | Extending Capabilities | `stage4_agent_mcp.py` | MCP (Model Context Protocol) |
| 5 | Memory | `stage5_agent_session.py` | Session / Conversation Memory |
| 6 | The Full Picture | — | Recap + Architecture |
| 7 | Should You Build an Agent? | — | Agent Skills (open ending) |

---

## Stage 1 — The Brain (`stage1_llm.py`)

### Concept
The LLM is the brain of the agent. But a brain alone can't do anything.

### Diagram — Brain in a Jar

```
┌─────────────┐
│   You        │──── "What files are in /src?" ────▶ ┌──────────┐
│              │                                      │   LLM    │
│              │◀── "I don't know, I can't look." ──  │  (Brain) │
└─────────────┘                                       └──────────┘
```

### Live Demo
- Run `stage1_llm.py`
- Ask "what files are in this directory?" — it can't do it, it just guesses

### Real-World Facts
- Claude Opus costs ~$15/M input, ~$75/M output tokens. Every message has a price tag.
- GPT-4o, Gemini, Claude — different brains, same interface: text in, text out
- Claude Code's brain is Claude. Cursor lets you pick (GPT-4o, Claude, etc). The brain is **swappable**.
- The system prompt for Claude Code is ~12,000 tokens. Before you type anything, the brain has already read a small novel of instructions.

### Takeaway
> An LLM by itself is a chatbot. To make it an agent, it needs a body.

---

## Stage 2 — The Loop (`stage2_agent_loop.py`)

### Concept
The agent loop is the heartbeat. It turns a chatbot into an agent. It's literally a `while` loop.

### Diagram — The Agent Loop

```
          ┌──────────────────────────────────────┐
          │                                      │
          ▼                                      │
   ┌─────────────┐    Tool call?    ┌──────────┐ │
   │  Call LLM    │───── YES ──────▶│ Execute  │─┘
   │              │                 │  Tool    │
   │              │                 └──────────┘
   │              │
   │              │─── NO (just text) ──▶ DONE. Show response.
   └─────────────┘
```

### Live Demo
- Run `stage2_agent_loop.py`
- Ask something that requires a tool — watch the loop iterate with colored terminal output

### Walk Through Code
- The `while` loop — ~10 lines. That's the secret.
- Stop condition: LLM returns text without tool calls → done.

### Real-World Facts
- Claude Code's agent loop is the same concept: call Claude → check tool calls → execute → feed back → repeat
- **Cursor** batches multiple tool calls in parallel (Claude Code does this too)
- **Devin** adds a planning step before each iteration — the LLM writes a plan, then picks a tool
- **ChatGPT** "thinking" (chain-of-thought) happens inside the brain before deciding on tools. The loop itself is the same.
- A single user prompt in Claude Code can trigger **50+ loop iterations**. One prompt → dozens of reads, edits, grep, bash commands.

### Takeaway
> Agent = LLM + Loop. Everything else is plugging things into this loop.

---

## Stage 3 — The Tools (`stage3_agent_tools.py` + `tools.py`)

### Concept
Tools are the agent's hands. The LLM doesn't execute anything — it **asks** us to, and we do it.

### Diagram — How a Tool Call Works

```
  LLM says:                       Our code does:
  ┌──────────────────┐           ┌──────────────────────┐
  │ {                │           │                      │
  │   "tool": "read_file",  ──▶ │  open("main.py").read()  │
  │   "args": {      │          │                      │
  │     "path":"main.py" │      │  return contents     │
  │   }               │         └──────────┬───────────┘
  │ }                 │                    │
  └──────────────────┘                     │
                                           ▼
                               Feed result back to LLM
```

### The 3-Part Pattern
1. **Schema** — JSON description of what tools exist and their parameters
2. **Registry** — Lookup table mapping tool names to functions
3. **Dispatcher** — Receives tool call from LLM, finds the function, executes it

### Walk Through `tools.py`
- Each tool is just a Python function with a JSON schema
- The agent loop is UNCHANGED from Stage 2

### Real-World: Claude Code's Actual Tools

| Tool | What it does |
|------|-------------|
| `Read` | Read files (like `cat` but smarter) |
| `Edit` | Surgical string replacement in files |
| `Write` | Create/overwrite files |
| `Bash` | Run any shell command |
| `Grep` | Search file contents |
| `Glob` | Find files by pattern |
| `Agent` | Spawn a sub-agent (agent inside an agent!) |
| `WebSearch` | Search the web |
| `WebFetch` | Fetch a URL |

### Interesting Facts
- Claude Code has a **permission system** on tools. `Read` runs freely. `Bash` asks you first. `Write` asks you first. The agent loop doesn't change — the tool harness adds a confirmation step.
- Cursor's tools include `apply_diff` — it generates a diff, and the tool applies it to your file.
- The LLM never sees your file system directly. It only sees what the tools **return**. If `read_file` lies, the LLM believes it.

### Takeaway
> More tools = more capable agent. But the loop is still the same.

---

## Stage 4 — Extending Capabilities: MCP (`stage4_agent_mcp.py`)

### Concept
What if tools didn't have to be hardcoded? What if the agent could **discover** new tools at runtime?

### Diagram — Before vs After MCP

```
  BEFORE (Stage 3):                    AFTER (Stage 4):
  ┌──────────┐                         ┌──────────┐
  │  Agent    │                         │  Agent   │
  │          │                          │          │
  │ read_file │  ← hardcoded           │ ?????    │ ← discovered at runtime
  │ write_file│                         │          │
  │ web_search│                         └────┬─────┘
  └──────────┘                               │
                                             │ "What tools do you have?"
                                             ▼
                                    ┌─────────────────┐
                                    │   MCP Server     │
                                    │  (e.g. Atlassian)│
                                    │                  │
                                    │ • search_issues  │
                                    │ • create_ticket  │
                                    │ • get_board      │
                                    └─────────────────┘
```

### Key Point
The agent loop is **IDENTICAL** to Stage 2/3. Only the tool source changed.

### Analogy
MCP is like **USB-C for AI**. Plug in a server, get new tools. Unplug it, tools disappear. The laptop (agent) doesn't change.

### Real-World MCP Ecosystem
- Claude Code supports MCP natively — plug in Jira, Slack, GitHub, databases
- Cursor supports MCP too
- 1000+ community MCP servers (GitHub, Postgres, Notion, Figma, etc.)

### Interesting Facts
- MCP was created by Anthropic and open-sourced in late 2024. It's becoming the industry standard.
- An MCP server is just a process that speaks a JSON protocol. You could write one in ~50 lines of Python.
- Claude Desktop uses MCP to connect to local files, Google Drive, Slack — same protocol.

### Takeaway
> MCP means you don't build tools *into* the agent. You build tools *for* agents. Any agent can use them.

---

## Stage 5 — Memory (`stage5_agent_session.py`)

### Concept
Without memory, every turn is a first date. Memory is just... keeping the message list.

### Diagram — With vs Without Memory

```
  WITHOUT MEMORY (Stage 3):        WITH MEMORY (Stage 5):

  Turn 1: [system, user1] → LLM    Turn 1: [system, user1] → LLM
  Turn 2: [system, user2] → LLM    Turn 2: [system, user1, asst1, user2] → LLM
  Turn 3: [system, user3] → LLM    Turn 3: [system, user1, asst1, user2, asst2, user3] → LLM

  Each turn forgets everything.     Conversation grows. LLM sees everything.
```

### Live Demo
- Stage 3: "My name is Cuong" → "What's my name?" → Forgets
- Stage 5: Same questions → Remembers

### Real-World Memory Systems (It Goes Deeper)

| Level | What | Who does it |
|-------|------|------------|
| **Conversation** | Keep message history | Everyone (our Stage 5) |
| **Project context** | Load relevant files/docs automatically | Cursor (codebase indexing), Claude Code (CLAUDE.md) |
| **Persistent memory** | Remember across sessions | Claude Code (memory files), ChatGPT (memory feature) |
| **RAG** | Search a knowledge base for relevant context | Enterprise tools, custom agents |

### Interesting Facts
- Claude Code's context window is **1M tokens** (~750k words). That's the entire Harry Potter series. But it still compresses old messages when conversations get long.
- Cursor indexes your entire codebase into embeddings so the agent can "remember" files it hasn't read yet.
- ChatGPT's memory feature is literally a text file of facts about you, injected into the system prompt.
- The hard problem isn't storing memory — it's deciding **what to forget**. Context windows have limits, every token costs money.

### Takeaway
> Memory completes the picture. Brain + Loop + Tools + Discovery + Memory = a full agent.

---

## The Full Picture — Recap

### Architecture Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                        AI AGENT                                │
│                                                                │
│  ┌─────────┐     ┌──────────────┐     ┌────────────────────┐  │
│  │ Memory  │◄───▶│  Agent Loop  │◄───▶│   Tools            │  │
│  │(messages)│     │  (while...)  │     │ local + MCP        │  │
│  └─────────┘     └──────┬───────┘     └────────────────────┘  │
│                         │                                      │
│                         ▼                                      │
│                   ┌──────────┐                                 │
│                   │   LLM    │                                 │
│                   │ (Brain)  │                                 │
│                   └──────────┘                                 │
└────────────────────────────────────────────────────────────────┘
```

### Mapping to Real Products

| Concept | Claude Code | Cursor | ChatGPT | Devin |
|---------|------------|--------|---------|-------|
| Brain (LLM) | Claude | Configurable | GPT-4o | Multiple |
| Agent Loop | Yes | Yes | Yes | Yes + planner |
| Tools | Read, Edit, Bash, Grep... | apply_diff, terminal... | code interpreter, browsing | browser, terminal, editor |
| MCP | Supported | Supported | Not yet | Not yet |
| Memory | CLAUDE.md + memory files | Codebase indexing | Conversation + memory | Full session state |

### Punchline
> We built this in ~200 lines of Python. Claude Code, Cursor, Devin — they're this, plus engineering.

---

## Should You Build an Agent? (5 min)

### Answer: Probably Not.

**Why?**
- The agent loop is a solved problem
- Claude Code, Cursor, OpenAI Agents SDK, LangGraph — they all do it well
- Building your own = rebuilding the loop, permissions, error handling, memory, streaming, retry logic...
- The loop is **commodity infrastructure** now

### The Trend: Build Agent Skills, Not Agents

```
  OLD THINKING:                    NEW THINKING:
  "I'll build an agent             "I'll build SKILLS that
   from scratch for                 plug into existing agents"
   my use case"
                                    ┌──────────────┐
  ┌──────────────┐                  │ Claude Code   │
  │ My Custom    │                  │ Cursor        │──▶ My MCP Server
  │ Agent        │                  │ Any Agent     │    (my tools, my data)
  │ (months of   │                  └──────────────┘
  │  work)       │
  └──────────────┘                  ┌──────────────┐
                                    │ My Skills     │
                                    │ • MCP servers │
                                    │ • CLAUDE.md   │
                                    │ • Hooks       │
                                    │ • Prompts     │
                                    └──────────────┘
```

### What "Building Skills" Looks Like
- **MCP servers** — give agents access to your systems (Jira, internal APIs, databases)
- **CLAUDE.md / .cursorrules** — teach agents your team's conventions
- **Hooks** — automate workflows around agent actions
- **Custom prompts / slash commands** — package expertise into reusable instructions

### Closing Line
> "You now understand the engine. The question isn't how to build the car — it's where to drive it. And that's our next topic: **Agent Skills**."

---

## Flow Summary

| Section | Code | Concept | Duration |
|---------|------|---------|----------|
| Opening | — | The question | 2 min |
| Agenda | — | Overview | 1 min |
| Stage 1 | `stage1_llm.py` | The Brain (LLM) | 8 min |
| Stage 2 | `stage2_agent_loop.py` | The Loop | 10 min |
| Stage 3 | `stage3_agent_tools.py` | The Tools | 10 min |
| Stage 4 | `stage4_agent_mcp.py` | Extending via MCP | 8 min |
| Stage 5 | `stage5_agent_session.py` | Memory | 7 min |
| Recap | — | Full picture diagram | 3 min |
| Closing | — | Don't build agents, build skills | 5 min |
| **Total** | | | **~54 min** |
