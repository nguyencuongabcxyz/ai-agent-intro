# Claude Code Facts & Tips — By Stage

Cross-referenced from the actual Claude Code codebase (`claude-code/src/`) to provide real-world context for each stage of the presentation.

---

## Stage 1: The Brain — LLM Only

### Facts from the Claude Code Codebase

1. **The system prompt is massive.** The script mentions ~12,000 tokens. In the actual codebase (`src/constants/prompts.ts`), the system prompt is assembled from 10+ sections: identity, core instructions, task guidance, tool usage, tone/style, output efficiency, environment info, memory, MCP instructions, and more. It's split into **static sections** (cached across requests for cost savings) and **dynamic sections** (recomputed every turn).

2. **Claude Code uses prompt caching.** There's a `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` marker that tells the API: "everything above this line is the same across turns — cache it." This saves money because the static portion (~80% of the prompt) doesn't get re-tokenized on every API call.

3. **The "genius" analogy extends to output limits too.** Claude Code has `CAPPED_DEFAULT_MAX_TOKENS = 8,192` for normal responses but can escalate to `ESCALATED_MAX_TOKENS = 64,000` when needed. The genius can write a note or a novel — but you're paying per page.

### Tips for the Audience

- **Tip:** When using Claude Code, you can shape the "genius" by creating a `CLAUDE.md` file in your project root. This gets injected into the system prompt automatically — it's like taping custom instructions on the wall of the room. Put your coding conventions, architecture decisions, and team preferences there.
- **Tip:** The knowledge cutoff is real, but Claude Code mitigates it with `WebSearch` and `WebFetch` tools. If you ask about something recent and it hallucinates, try prefixing with "search the web for..." to force it out of pure-brain mode.
- **Tip:** Every word costs money. If you paste a huge file and ask "what does this do?", you're paying for all those input tokens. Instead, let Claude Code read the file with its `Read` tool — it can selectively read specific line ranges (`offset` and `limit` parameters).

---

## Stage 2: The Agent Loop — LLM + Tools + Loop

### Facts from the Claude Code Codebase

1. **The loop is a `while (true)` in `src/query.ts` (line ~307).** It's an async generator (`queryLoop()`) that yields streaming events. The basic pattern is identical to Stage 2: call API → check for tool_use → execute tools → feed results back → repeat. The "embarrassingly simple" claim holds up — the core logic is the same.

2. **Claude Code's stop condition** is when the model returns a response with no `tool_use` blocks — exactly like the script describes. There's also a `maxTurns` parameter that can hard-stop the loop after N iterations (lines 1705-1712).

3. **Parallel tool calls are real and aggressive.** Claude Code runs up to **10 tools concurrently** (`getMaxToolUseConcurrency()` in `toolOrchestration.ts`). But it's smart about it — read-only tools (Read, Grep, Glob) batch concurrently, while write tools (Edit, Write, Bash) execute serially to avoid conflicts.

4. **The `MAX_ITERATIONS = 15` in the demo is conservative.** Claude Code's sub-agents can run up to **200 turns** (`maxTurns: 200` in fork agent definitions). The main loop has no hard iteration cap — it relies on `maxTurns` being set by the caller, or the model deciding it's done.

### Tips for the Audience

- **Tip:** In Claude Code, you can watch the ReAct loop in real-time. Each tool call shows you what the agent is doing — reading files, running commands, searching. If it's going in circles, press `Escape` to interrupt and redirect it.
- **Tip:** The message list grows fast. After 5-10 tool calls, you might have 20+ messages in context. Claude Code handles this with **autocompact** — when context gets too large, it automatically summarizes older messages. You can also trigger this manually with `/compact`.
- **Tip:** If the agent keeps calling tools and won't stop, it might be stuck in a loop. The `maxTurns` safety valve exists in Claude Code, but for your own agents, always set a `MAX_ITERATIONS` like the script shows.

---

## Stage 3: The Tools — Full Tool Suite

### Facts from the Claude Code Codebase

1. **Claude Code has way more than 9 tools.** The base tools list in `src/tools.ts` includes: `AgentTool`, `BashTool`, `FileEditTool`, `FileReadTool`, `FileWriteTool`, `GlobTool`, `GrepTool`, `WebFetchTool`, `WebSearchTool`, `NotebookEditTool`, `SkillTool`, plus task management tools (`TaskCreate/Get/List/Update`), worktree tools, and feature-gated tools like `SleepTool` and `MonitorTool`. Some tools are conditionally enabled based on feature flags.

2. **Tool result limits are strict.** Each tool result is capped at **50,000 characters** (`DEFAULT_MAX_RESULT_SIZE_CHARS`), and aggregate results per message are capped at **200,000 characters**. This prevents a single `cat` of a massive file from blowing up the context window. When you use the `Read` tool, it defaults to 2,000 lines max.

3. **The permission layer is exactly as described — an `if` statement wrapping the dispatcher.** In `src/utils/permissions/permissions.ts`, there's a multi-source rule evaluation system. Rules come from file settings, CLI args, commands, and session state. The decision reasons include: `classifier` (dangerous command detection), `hook` (custom permission hooks), `rule` (allow/deny rules), `sandboxOverride`, and `mode` (plan/auto/manual). It's sophisticated but the core concept is: check rules → allow, deny, or ask.

4. **The `Edit` tool is surgical.** Unlike `write_file` that replaces the whole file, Claude Code's `Edit` tool does exact string replacement — you give it `old_string` and `new_string`. It fails if the match isn't unique. This is a deliberate design choice to minimize damage from wrong edits.

### Tips for the Audience

- **Tip:** Tool descriptions matter enormously. In Claude Code, the `Bash` tool description says "Avoid using this tool to run `find`, `grep`, `cat`... use the appropriate dedicated tool." This steers the model toward better tools. When building your own agents, invest time in precise tool descriptions — vague ones cause the LLM to pick wrong tools.
- **Tip:** Claude Code's permission system has 3 modes you can configure: **auto** (approve safe tools automatically), **manual** (approve everything), and **plan** (read-only, no writes). You can also set `alwaysAllow` rules for specific tools in your settings to skip approval prompts.
- **Tip:** If you're building agents, the `Edit` tool pattern (surgical replacement vs. full rewrite) is worth copying. Full file rewrites are risky — one hallucinated line can corrupt a working file. String replacement is safer because it fails loudly if the match is wrong.

---

## Stage 4: MCP — Dynamic Tool Discovery

### Facts from the Claude Code Codebase

1. **MCP integration lives in `src/services/mcp/`.** The client supports 4 transport types: `StdioClientTransport` (subprocess, like the demo), `SSEClientTransport` (Server-Sent Events), `StreamableHTTPClientTransport`, and `WebSocketTransport`. Most local MCP servers use stdio.

2. **Tool naming convention:** When MCP tools are discovered, they're namespaced as `mcp__<server>__<tool>` using `buildMcpToolName()` in `mcpStringUtils.ts`. So a Jira MCP server named "atlassian" with a `search_issues` tool becomes `mcp__atlassian__search_issues`. This prevents name collisions between servers.

3. **MCP instructions are injected into the system prompt.** Each MCP server can provide instructions (like "use JQL syntax for queries"), and these get added via `getMcpInstructionsSection()`. There's even a delta mode (`MCP_INSTRUCTIONS_DELTA` feature flag) that only sends instruction changes rather than the full set each turn — an optimization for servers with large instruction sets.

4. **MCP auth is production-grade.** The codebase has `ClaudeAuthProvider` in `auth.ts` with OAuth support, token refresh, and "step-up" detection (when a 401 requires re-authentication mid-session). This is way beyond the simple stdin/stdout demo, but the protocol is the same underneath.

### Tips for the Audience

- **Tip:** To add MCP servers to Claude Code, edit your settings file (`.claude/settings.json` or global settings). Add servers under `mcpServers` with their command and args. Claude Code will auto-discover tools on startup — you'll see "Discovered X tools" just like the demo.
- **Tip:** The 1000+ community MCP servers are real — check modelcontextprotocol.io for the registry. But quality varies wildly. Look for servers with good tool descriptions and error handling. A poorly-described MCP tool is worse than no tool at all.
- **Tip:** You can build your own MCP server in ~50 lines of Python using the `mcp` package. This is the highest-leverage thing you can do — connect Claude Code to your internal tools (deployment scripts, monitoring dashboards, ticket systems) without modifying Claude Code itself.

---

## Stage 5: Session Management — Multi-Turn Memory

### Facts from the Claude Code Codebase

1. **Claude Code has 4 layers of memory**, matching the script's table exactly:
   - **Conversation history:** Messages list grows each turn (Stage 5's approach)
   - **Session memory:** `src/services/SessionMemory/` — extracts key facts to `.claude/sessionMemory.md` using a background sub-agent. Triggers at **30K tokens** initially, then updates every **50K tokens** or **5 tool calls**
   - **Project context:** `CLAUDE.md` files loaded automatically from project root
   - **Persistent memory:** Memory files in `.claude/projects/<project>/memory/` that survive across sessions

2. **Context compression is multi-layered:**
   - **Microcompact:** Cached per `tool_use_id` — compresses individual tool results (lines 414-426 of query.ts)
   - **Autocompact:** Triggered by token thresholds — summarizes the entire conversation history
   - **Snip:** History trimming via the `HISTORY_SNIP` feature — removes old turns entirely
   - **Context collapse:** (`CONTEXT_COLLAPSE` feature) — maintains a persistent summary store that accumulates across compactions

3. **The "every token costs money" warning is real.** With Claude's 1M token context window, a long session with many tool calls can accumulate massive context. Claude Code tracks this with `tokenBudget.ts` — there's a **90% completion threshold** (`COMPLETION_THRESHOLD`) and it stops after **3 continuations with <500 token delta** to prevent runaway spending.

4. **`CLAUDE.md` is more powerful than most people realize.** The script calls it "one of the most powerful and underused features." In the codebase, CLAUDE.md content is loaded via `loadMemoryPrompt()` and injected as a system-reminder block. It supports project-level (`./CLAUDE.md`), user-level, and nested directory-level files — all merged together.

### Tips for the Audience

- **Tip:** When your Claude Code session gets long and sluggish, use `/compact` to manually trigger context compression. The agent summarizes old messages so it can keep working with a fresh context. It's like the genius writing a summary of what happened so far and throwing away the old papers.
- **Tip:** For information you want Claude Code to remember across sessions, create memory files in `.claude/projects/<project>/memory/`. Or simply tell Claude "remember that we use PostgreSQL 15 and deploy to AWS ECS" — it'll save it automatically.
- **Tip:** `CLAUDE.md` is your highest-leverage file. Put your coding standards, architecture decisions, deployment process, and team conventions there. Every conversation starts with Claude reading it — so you never have to repeat yourself.
- **Tip:** Watch the token count. A session with 50+ tool calls can easily hit 100K+ tokens. If you're doing a massive refactor, consider breaking it into smaller sessions rather than one marathon conversation. Each new session starts with a fresh context and clean budget.

---

## Bonus: The "Build Skills, Not Agents" Closing Point

This is backed by the codebase. Claude Code has `SkillTool` — a mechanism for loading custom skills (slash commands) that expand into full prompts. The architecture is designed so that the loop, tools, and memory are infrastructure — **your value-add is the domain knowledge you bring via CLAUDE.md, MCP servers, hooks, and custom agents in `.claude/agents/`**.
