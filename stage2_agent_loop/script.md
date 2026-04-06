# Stage 2: The Agent Loop — LLM + Tools + Loop

## What to Tell the Audience

### Opening (1 min)

- "This is the moment a chatbot becomes an agent. We add **one thing**: a `while` loop."
- "The pattern is embarrassingly simple — call the LLM, check if it wants to use a tool, execute the tool, feed the result back, repeat."
- "This exact pattern powers Claude Code, Cursor, and every AI coding agent."

### Core Concept — The Human Analogy (3 min)

**"The agent loop is how humans actually work."**

Think about how YOU do a task — say, writing a report on AI trends:

1. **Think** — "I need to find recent AI trends. Let me search the web." (reasoning)
2. **Act** — You open a browser and search "AI trends 2026." (tool use)
3. **Observe** — You read the search results. Some are useful, some aren't. (read tool result)
4. **Think again** — "This article looks promising. Let me read the full thing." (reasoning based on observation)
5. **Act again** — You click the link and read the article. (another tool use)
6. **Observe again** — You now have the content. "I have enough info to write the report." (read tool result)
7. **Act one final time** — You write the report and save it. (final tool use)
8. **Done** — "The report is written. Task complete." (stop)

**Think → Act → Observe → Repeat.** That's the loop. You keep going until YOU decide the task is done.

This is exactly what the agent loop does:
- **Think** = the LLM reasons about what to do next
- **Act** = the LLM requests a tool call (search, read, write)
- **Observe** = our code executes the tool and sends the result back to the LLM
- **Repeat** = the LLM sees the result and decides: do I need another action, or am I done?

The key points:
- The **agent loop** is the heartbeat. It's literally a `while True` loop that simulates this human pattern.
- **Stop condition**: when the LLM responds with plain text (no tool calls), it's saying "I'm done" — just like you deciding the report is finished.
- The LLM **decides** when to use tools and when to stop. Your code just executes what it asks for.
- This is the fundamental shift: the LLM is now the **decision maker**, not just a text generator.

> This pattern is known in AI research as **ReAct** (Reasoning + Acting). It was formalized in a 2022 paper, but it's really just how humans have always worked — the researchers noticed and wrote it down.

### Walk Through the Code (4 min)

- **Tool schemas** (line 107-163): JSON descriptions that tell the LLM what tools exist. The LLM reads these like API docs.
- **Tool implementations** (line 170-219): Real Python functions — `web_search`, `write_file`, `fetch_webpage`. The LLM never sees this code.
- **Tool registry** (line 216-220): A simple dict mapping names to functions. This is the "dispatcher."
- **The loop** (line 278-352): The magic 30 lines. Walk through it step by step:
  1. Call the LLM with messages + tool schemas
  2. Check: did it return tool calls?
  3. YES → execute each tool, add results to messages, loop again
  4. NO → done, return the text response
- **Safety limit** (line 29): `MAX_ITERATIONS = 15` — prevents infinite loops. Claude Code uses similar limits.

---

## What to Explain Further

### How Tool Calling Actually Works Under the Hood

- The LLM doesn't "run" tools. It outputs a **structured JSON** saying "I want to call web_search with query='...'"
- Your code (the harness) parses that JSON, finds the function, calls it, and sends the result back as a message.
- The LLM then sees the result and decides what to do next — call another tool, or give a final answer.

### The Messages List is the "Memory" of a Single Turn

- Every tool call and result gets appended to the messages list.
- By iteration 5, the LLM might see: system prompt + user task + 4 rounds of (tool call + result).
- This is why context windows matter — long tasks burn through tokens fast.

### Parallel Tool Calls

- The LLM can request **multiple tool calls** in a single response.
- Claude Code and Cursor exploit this — e.g., read 3 files at once instead of one at a time.
- Our demo handles this: the `for tool_call in assistant_message.tool_calls` loop.

---

## Demo Examples

### Demo 1: Web Search (single tool, single iteration)

```bash
python agent.py "What is the latest version of Node.js?"
```

- Watch: the agent calls `web_search`, gets results, then summarizes. 2 iterations.
- Compare with Stage 1: "Remember when it couldn't answer current questions? Now it can."

### Demo 2: Multi-Step Task (multiple iterations)

```bash
python agent.py "Search the web for the top 3 AI trends in 2026 and write a summary to AI_trends.txt"
```

- Watch: search → fetch pages → write file. 3-5 iterations.
- Point out the iteration counter and message count growing.
- "Each colored block is one round of the loop. The LLM decided what to do at each step."

### Demo 3: Show the Stop Condition

```bash
python agent.py "What is 2 + 2?"
```

- The LLM answers immediately without calling any tools. 1 iteration.
- "The LLM decided it didn't need tools for this. The loop ran once and stopped."

---

## Transition to Stage 3

> "We have 3 tools here — web search, fetch, write. But real agents like Claude Code have 10+ tools. Stage 3 shows what happens when you give the agent a full toolbox."

Note:

- Higher models of support built-in tools https://developers.openai.com/api/docs/guides/tools
