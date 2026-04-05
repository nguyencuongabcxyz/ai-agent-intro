"""
Stage 2: The Agent Loop (LLM + Tools + Loop)

Builds on Stage 1 by adding a loop and tool calling.
The LLM can now call tools, read results, and keep going until the task is done.
This is the same core pattern used by Cursor, Claude Code, and Copilot agents.

Run:
  python stage2_agent_loop.py "search the web for the latest Python version"
  python stage2_agent_loop.py  (interactive mode)
"""

import os
import sys
import json
import threading
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Step 1: Safety limit to prevent infinite loops
MAX_ITERATIONS = 15


# Step 2: Color constants for terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_header(text):
    width = 60
    print(f"\n{BOLD}{MAGENTA}{'=' * width}")
    print(f"  {text}")
    print(f"{'=' * width}{RESET}\n")


def print_system(text):
    print(f"\n{BLUE}{BOLD}[SYSTEM PROMPT]{RESET}")
    print(f"{BLUE}{'─' * 50}{RESET}")
    for line in text.strip().split('\n'):
        print(f"{BLUE}  {line}{RESET}")
    print(f"{BLUE}{'─' * 50}{RESET}")


def print_user(text):
    print(f"\n{BOLD}[USER TASK]{RESET}")
    print(f"  {text}")


def print_iteration(n, message_count):
    print(f"\n{BOLD}{'━' * 50}")
    print(f"  ITERATION {n}  │  Messages in context: {message_count}")
    print(f"{'━' * 50}{RESET}")


def print_llm(text):
    if text:
        print(f"\n{GREEN}{BOLD}[LLM RESPONSE]{RESET}")
        for line in text.strip().split('\n'):
            print(f"{GREEN}  {line}{RESET}")


def print_tool_call(name, arguments):
    print(f"\n{YELLOW}{BOLD}[TOOL CALL]{RESET} {YELLOW}{name}{RESET}")
    if isinstance(arguments, dict):
        for key, value in arguments.items():
            display_value = str(value)
            if len(display_value) > 200:
                display_value = display_value[:200] + "..."
            print(f"{YELLOW}  {key}: {display_value}{RESET}")


def print_tool_result(name, result):
    print(f"\n{CYAN}{BOLD}[TOOL RESULT]{RESET} {CYAN}from {name}{RESET}")
    display = result if len(result) <= 500 else result[:500] + f"\n{DIM}  ... ({len(result)} chars total){RESET}"
    for line in display.split('\n'):
        print(f"{CYAN}  {line}{RESET}")


def print_done(text):
    print(f"\n{MAGENTA}{BOLD}{'=' * 50}")
    print(f"  AGENT FINISHED")
    print(f"{'=' * 50}{RESET}")
    if text:
        print(f"\n{GREEN}{text}{RESET}")


def print_error(text):
    print(f"\n{RED}{BOLD}[ERROR]{RESET} {RED}{text}{RESET}")


# Step 3: Tool schemas — JSON descriptions the LLM reads to know what tools exist
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information. Use this when you need to find up-to-date facts, data, or answers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file on the local filesystem. Creates the file if it doesn't exist, overwrites if it does.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
]


# Step 4: Tool implementations — the real Python functions that run when the LLM calls a tool
MAX_OUTPUT_CHARS = 5000


def execute_web_search(query: str) -> str:
    """Search the web using DuckDuckGo."""
    try:
        from ddgs import DDGS
        results = DDGS().text(query, max_results=5)
        if not results:
            return "No results found."
        output = []
        for i, r in enumerate(results, 1):
            output.append(f"{i}. {r['title']}\n   {r['body']}\n   URL: {r['href']}")
        return "\n\n".join(output)
    except Exception as e:
        return f"Search failed: {e}"


def execute_write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed."""
    try:
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


# Step 5: Tool registry — maps tool names to their Python functions
TOOL_REGISTRY = {
    "web_search": execute_web_search,
    "write_file": execute_write_file,
}


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name. This is the bridge between LLM intent and real code."""
    func = TOOL_REGISTRY.get(name)
    if not func:
        return f"Error: Unknown tool '{name}'"
    try:
        return func(**arguments)
    except Exception as e:
        return f"Error executing '{name}': {e}"


# Step 6: System prompt — tells the LLM what tools it has and how to use them
SYSTEM_PROMPT = """You are a helpful AI assistant that accomplishes tasks by using tools.

You have access to these tools:
- web_search: Search the web for current information
- write_file: Write content to a file

INSTRUCTIONS:
1. Break the task into steps and think about what to do.
2. Use one or more tools to accomplish each step.
3. After each tool result, analyze it and decide what to do next.
4. When the task is FULLY COMPLETE, respond with your final answer as plain text WITHOUT calling any tools.

IMPORTANT: Only stop (respond without tools) when the task is truly done.
Think step by step. Be thorough but efficient."""


def run_agent(user_task: str) -> str:
    """
    Run the AI agent loop until the task is complete.

    Args:
        user_task: What the user wants to accomplish

    Returns:
        The agent's final response text
    """

    # Step 7: Build the initial message list with system prompt and user task
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print_system(SYSTEM_PROMPT)

    messages.append({"role": "user", "content": user_task})
    print_user(user_task)

    # Step 8: Start the agent loop — keep calling the LLM until it stops using tools
    iteration = 0
    while iteration < MAX_ITERATIONS:
        iteration += 1
        print_iteration(iteration, len(messages))

        # Step 9: Show a spinner while waiting for the API response
        stop_spinner = threading.Event()

        def spinner():
            frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            i = 0
            while not stop_spinner.is_set():
                print(f"\r{YELLOW}{BOLD}  {frames[i % len(frames)]} Thinking...{RESET}", end="", flush=True)
                stop_spinner.wait(0.1)
            print(f"\r{' ' * 30}\r", end="")

        spinner_thread = threading.Thread(target=spinner, daemon=True)
        spinner_thread.start()

        # Step 10: Call the LLM with tools enabled so it can request tool calls
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOL_SCHEMAS,
            )
        except Exception as e:
            stop_spinner.set()
            spinner_thread.join()
            print_error(f"API call failed: {e}")
            return f"Error: {e}"

        # Step 11: Stop the spinner now that we have the response
        stop_spinner.set()
        spinner_thread.join()

        assistant_message = response.choices[0].message

        # Step 12: Add the LLM's response to the message history
        messages.append(assistant_message)

        if assistant_message.content:
            print_llm(assistant_message.content)

        # Step 13: Check the stop condition — no tool calls means the agent is done
        if not assistant_message.tool_calls:
            print_done(assistant_message.content)
            return assistant_message.content or ""

        # Step 14: Execute each tool the LLM requested and add results to messages
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}

            print_tool_call(tool_name, tool_args)

            result = execute_tool(tool_name, tool_args)

            print_tool_result(tool_name, result)

            # Step 15: Send the tool result back so the LLM can see it next iteration
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    print_error(f"Agent stopped after {MAX_ITERATIONS} iterations (safety limit)")
    return "Agent reached maximum iterations without completing the task."


# Step 16: CLI entry point — handles command-line args or starts interactive mode
def main():
    if not os.getenv("OPENAI_API_KEY"):
        print_error(
            "OPENAI_API_KEY not found!\n"
            "  1. Copy .env.example to .env\n"
            "  2. Add your OpenAI API key\n"
            "  3. Run again"
        )
        sys.exit(1)

    print_header("STAGE 2: AGENT LOOP (LLM + TOOLS + LOOP)")
    print(f"{DIM}  Model: {MODEL}")
    print(f"  Max iterations per turn: {MAX_ITERATIONS}")
    print(f"  Tools: web_search, write_file (2 simple tools)")
    print(f"  Type 'quit' or 'exit' to stop.{RESET}")

    # Step 17: If a task was passed as a command-line argument, run it directly
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        run_agent(task)
        return

    # Step 18: Interactive loop — each turn starts fresh (no memory across turns)
    while True:
        print(f"\n{BOLD}What should the agent do?{RESET}")
        try:
            task = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM}Goodbye!{RESET}")
            break

        if not task:
            continue
        if task.lower() in ("quit", "exit"):
            print(f"{DIM}Goodbye!{RESET}")
            break

        run_agent(task)


if __name__ == "__main__":
    main()
