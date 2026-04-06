# Stage 5: Session Management — Multi-Turn Memory

## What to Tell the Audience

### Opening (1 min)
- "Without memory, every turn is a first date. The agent forgets everything between messages."
- "The fix is almost embarrassingly simple: **don't reset the messages list**."
- "In Stage 3, each turn created a fresh `[system, user]`. In Stage 5, we keep appending to the same list."

### Core Concept (2 min)
- Memory = keeping the conversation history across turns.
- Without memory: `Turn 1: [system, user1]` → `Turn 2: [system, user2]` (forgets turn 1)
- With memory: `Turn 1: [system, user1]` → `Turn 2: [system, user1, asst1, user2]` (remembers)
- The LLM sees the entire conversation every time. That's how it "remembers."
- This is the **simplest form** of memory, but it's what most products start with.

### Walk Through the Code (2 min)
- **The key difference** — compare `main()` in Stage 3 vs Stage 5:
  - Stage 3 (line 132): `messages` is created inside `run_agent()` — fresh each turn
  - Stage 5 (line 234): `messages` is created ONCE in `main()` and passed to every `run_agent()` call
- **`run_agent()` signature** (line 132): takes `messages` as a parameter and returns it
- **`print_session_info()`** (line 103-105): shows message count — watch it grow each turn
- The agent loop itself? **Unchanged**. Same as Stage 2, 3, and 4.

---

## What to Explain Further

### Real-World Memory Systems — It Goes Much Deeper

| Level | What | Who Does It |
|-------|------|-------------|
| **Conversation** | Keep message history | Everyone (our Stage 5) |
| **Project context** | Auto-load relevant files/docs | Cursor (codebase indexing), Claude Code (CLAUDE.md) |
| **Persistent memory** | Remember across sessions | Claude Code (memory files), ChatGPT (memory feature) |
| **RAG** | Search knowledge base for relevant context | Enterprise tools, custom agents |

### The Hard Problem: What to Forget
- Context windows have limits. Even Claude's 1M tokens (~750k words) runs out.
- Every token costs money. Sending 100k tokens of history every turn adds up.
- Claude Code uses **compression** — when conversations get long, it summarizes older messages.
- ChatGPT's "memory" is literally a text file of key facts, injected into the system prompt.
- Cursor indexes your codebase into embeddings — a form of long-term memory.

### CLAUDE.md: A Different Kind of Memory
- Claude Code reads `CLAUDE.md` files from your project root automatically.
- This is **project-level memory** — coding conventions, architecture decisions, team preferences.
- It persists across sessions because it's a file, not conversation history.
- This is one of the most powerful and underused features.

---

## Demo Examples

### Demo 1: Memory Works (the "name test")
```bash
python agent.py
```
```
> My name is Cuong and I work on the AI team
> What's my name and what team am I on?
```
- It remembers! Compare with Stage 3 where it would say "I don't know your name."
- Point out the `[SESSION] X messages in memory` counter growing.

### Demo 2: Multi-Turn Task Building
```
> Search the web for the top 3 programming languages in 2026
> Now create a file comparing them in a markdown table
> Add a section about which one is best for AI development
```
- Each turn builds on the previous. The agent remembers what it searched and what it wrote.
- "In Stage 3, the second message wouldn't know about the search results. Here, it does."

### Demo 3: Context Accumulation
```
> Read the README.md file
> What are the main sections?
> Now add a "Contributing" section to it based on what you read
```
- The agent reads → remembers → acts on that memory.
- "This is exactly how you use Claude Code: 'read this file, now fix this bug in it.'"

### Demo 4: Show the Growing Context
- After 4-5 turns, point out: `[SESSION] 25 messages in memory`
- "Every tool call, every result, every response — it's all in there."
- "This is why Claude Code sessions get expensive over long conversations."

---

## Closing — The Full Picture

### Recap What We Built
```
Stage 1: Brain only          → LLM API call
Stage 2: Brain + Loop        → Agent loop (while + tool calls)
Stage 3: Brain + Loop + Tools → Full tool suite (7 tools)
Stage 4: Dynamic tools        → MCP (discover tools at runtime)
Stage 5: Memory               → Session management (persistent messages)
```

### The Punchline
> "We built this in ~200 lines of Python. Claude Code, Cursor, Devin — they're this, plus engineering. The core architecture is what you just saw."

### What Makes Production Agents Different
- **Streaming** — tokens appear as they're generated, not all at once
- **Permissions** — ask the user before running dangerous tools
- **Error recovery** — retry failed tool calls, handle rate limits
- **Parallel tool calls** — run multiple tools at once
- **Context management** — compress old messages, prioritize relevant context
- **Sub-agents** — spawn child agents for subtasks

### The Trend: Build Skills, Not Agents
- The agent loop is commodity infrastructure now. Don't rebuild it.
- Instead, build **skills**: MCP servers, CLAUDE.md files, hooks, custom prompts.
- Give existing agents (Claude Code, Cursor) access to YOUR systems and YOUR knowledge.
