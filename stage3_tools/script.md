# Stage 3: The Tools — Full Tool Suite

## What to Tell the Audience

### Opening (1 min)
- "Now we give the agent a real toolbox. Same loop as Stage 2, but with 7 tools instead of 3."
- "This is the key insight: **the loop doesn't change when you add tools**. Tools are a separate concern."
- "This is also how real products work — Claude Code's tool list grew from a handful to 10+ tools over time, but the core loop stayed the same."

### Core Concept (2 min)
- Tools follow a **3-part pattern** that every AI agent uses:
  1. **Schema** — JSON description the LLM reads (like API docs)
  2. **Registry** — Dictionary mapping tool names → Python functions
  3. **Dispatcher** — Takes the LLM's request, finds the function, executes it
- The LLM never sees your Python code. It only sees the JSON schema. It outputs "call read_file with path='main.py'" and YOUR code does the actual `open()`.

### Walk Through the Code (4 min)
- **`tools.py`** — all tools live in a separate file now. Clean separation.
- Show **one tool end-to-end**: `read_file`
  - Schema (line 60-74): name, description, parameters
  - Implementation (line 197-208): actual Python code
  - Registry entry (line 430): `"read_file": execute_read_file`
- **`agent.py`** (line 21): just `from tools import TOOL_SCHEMAS, execute_tool` — the agent loop is unchanged.
- **New tools**: `list_files`, `read_file`, `run_bash`, `grep` — the agent can now explore, search, and modify your system.

---

## What to Explain Further

### The LLM Doesn't Execute Code — You Do
- This is the most misunderstood part. People think the AI "runs commands."
- Reality: the LLM outputs a JSON string. Your harness code parses it and calls the function. The LLM is just making decisions.
- If `read_file` returned fake content, the LLM would believe it. It has no way to verify.

### Tool Design Matters More Than You Think
- **Description quality**: A vague description = the LLM picks the wrong tool. A precise description = correct tool choice.
- **Output format**: Tools should return useful, structured text. Too much output → context overflow. Too little → the LLM asks again.
- **Error messages**: Good error messages help the LLM recover. "File not found: main.py" is better than "Error."

### Claude Code's Actual Tool List
| Tool | Purpose |
|------|---------|
| `Read` | Read files (with line numbers) |
| `Edit` | Surgical string replacement |
| `Write` | Create/overwrite files |
| `Bash` | Run shell commands |
| `Grep` | Search file contents (ripgrep) |
| `Glob` | Find files by pattern |
| `Agent` | Spawn a sub-agent |
| `WebSearch` | Search the web |
| `WebFetch` | Fetch a URL |

### The Permission Layer
- Claude Code adds a **permission check** between the LLM's request and execution.
- `Read` and `Grep` run freely. `Bash`, `Write`, `Edit` ask for user approval.
- This is just an `if` statement wrapping the dispatcher — the loop doesn't change.

---

## Demo Examples

### Demo 1 (Warm-up): Simple File Exploration
```bash
python agent.py "List all files in this directory and read the README"
```
- Watch: `list_files` → `read_file` on README.md. The agent explores like a human would.
- "This is exactly what Claude Code does when you open a new project."

### Demo 2 (Main Demo): Fix Bugs in an Order Processing System — All 7 Tools

This is the showstopper demo. The `buggy-app/` folder contains a TypeScript **order processing system** — the kind of business logic you'd find in any e-commerce backend. It calculates order totals, applies discounts, handles tax, and updates inventory. But it has **2 real bugs**:

1. **Discount math is wrong** — `afterDiscount = subtotal + discountAmount` (should subtract, not add). A customer with a 10% discount actually pays MORE. This is the kind of billing bug that loses real money.
2. **Inventory decrements by 1** instead of by the ordered quantity — `product.stock -= 1` instead of `product.stock -= item.quantity`. Order 5 mice, only 1 leaves inventory. Classic off-by-logic bug.

**The prompt:**
```bash
python agent.py "There's a TypeScript order processing app in the ../buggy-app folder. Explore the project, run the tests to find what's failing, search the code for the bugs, fix them, and re-run the tests to confirm everything passes. Write a short bug report to bug_report.md when done."
```

**Expected tool chain (watch it unfold step by step):**

| Step | Human Analogy | Tool Used | What Happens |
|------|--------------|-----------|-------------|
| 1 | "Let me look at the project" | `list_files("../buggy-app/src")` | Discovers: types.ts, orderProcessor.ts, test.ts, main.ts |
| 2 | "What are the data models?" | `read_file("../buggy-app/src/types.ts")` | Reads Product, OrderItem, OrderResult interfaces |
| 3 | "Let me understand the logic" | `read_file("../buggy-app/src/orderProcessor.ts")` | Reads the order processing code |
| 4 | "Let me run the tests" | `run_bash("cd ../buggy-app && npm test")` | Sees: 10 passed, 2 failed — discount total is wrong, inventory is wrong |
| 5 | "Where's the discount bug?" | `grep("discountAmount", "../buggy-app/src")` | Finds `afterDiscount = subtotal + discountAmount` — should be minus! |
| 6 | "Let me check inventory logic" | `grep("stock", "../buggy-app/src/orderProcessor.ts")` | Finds `product.stock -= 1` — should be `item.quantity` |
| 7 | "Let me read the tests to confirm expectations" | `read_file("../buggy-app/src/test.ts")` | Reads what the tests expect |
| 8 | "I see both bugs, let me fix them" | `write_file("../buggy-app/src/orderProcessor.ts", ...)` | Fixes both: `subtotal - discountAmount` and `stock -= item.quantity` |
| 9 | "Let me verify" | `run_bash("cd ../buggy-app && npm test")` | All 12 tests pass! |
| 10 | "Let me document what I found" | `write_file("bug_report.md", ...)` | Writes a bug report explaining both fixes |

**Why this demo is powerful:**
- It uses **all 7 tools** in a single task.
- The bugs are **realistic** — wrong arithmetic operators and off-by-logic errors are among the most common production bugs. Everyone in the audience has shipped something like this.
- It mirrors exactly how a developer works: explore → understand → test → diagnose → fix → verify → document.
- The audience can watch the **Think → Act → Observe** loop from Stage 2 playing out on a real codebase.
- The agent makes decisions at each step — it wasn't told which file to read or what to grep for.
- "This is what Claude Code and Cursor do every day. The loop is the same. The tools are the same. The only difference is polish."

**Presenter tips:**
- Before the demo, briefly explain the app: "This is an order processor — takes products, quantities, applies discounts and tax, updates inventory. There are bugs. Let's see if the agent can find and fix them."
- Point out each iteration: "It's exploring... now it's running tests... 2 failures... it's searching for the discount logic... found it... now fixing..."
- At the end, open `bug_report.md` — the agent wrote a coherent report about real business logic it debugged.

### Demo 3 (Backup): Web Research + File Creation
```bash
python agent.py "Search the web for the top 3 AI frameworks in 2026, then create a comparison.md file with a summary table"
```
- Watch: `web_search` → `fetch_webpage` → `write_file`. Multiple tool types in one task.
- Use this if the buggy-app demo has issues or if time is short.

---

## Transition to Stage 4
> "We hardcoded 7 tools. But what if someone else already built tools for Jira, Slack, or GitHub? Do we copy-paste their code? No — we use MCP, and the agent discovers tools at runtime."
