"""
stage4_agent_mcp.py — Stage 4: MCP (Model Context Protocol)

Instead of hardcoded tools (Stage 3), this stage discovers tools
at runtime from an external MCP server (Atlassian).
The agent loop is the same — only the tool backend changes.

Setup: pip install mcp-atlassian, configure .env with Atlassian creds.
Run:   python stage4_agent_mcp.py "your task"  or  interactive mode.
"""

import os
import sys
import json
import asyncio
import threading
from openai import OpenAI
from dotenv import load_dotenv

# Step 1: Import the MCP client (replaces the hardcoded tools from Stage 3)
from mcp_client import MCPClient, create_atlassian_client

load_dotenv()

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
MAX_ITERATIONS = 15

# Step 2: Define color codes for terminal output
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
    print(f"\n{YELLOW}{BOLD}[MCP TOOL CALL]{RESET} {YELLOW}{name}{RESET}")
    if isinstance(arguments, dict):
        for key, value in arguments.items():
            display_value = str(value)
            if len(display_value) > 200:
                display_value = display_value[:200] + "..."
            print(f"{YELLOW}  {key}: {display_value}{RESET}")


def print_tool_result(name, result):
    print(f"\n{CYAN}{BOLD}[MCP TOOL RESULT]{RESET} {CYAN}from {name}{RESET}")
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


def print_mcp_info(text):
    """Print MCP-related status messages."""
    print(f"{CYAN}{BOLD}[MCP]{RESET} {CYAN}{text}{RESET}")


# Step 3: Build the system prompt from whatever tools the MCP server provides
def build_system_prompt(tool_names: list[str]) -> str:
    """Build the system prompt dynamically from discovered MCP tools."""
    tools_list = "\n".join(f"- {name}" for name in tool_names)

    return f"""You are a helpful AI assistant that accomplishes tasks using MCP (Model Context Protocol) tools.

You have access to tools provided by the Atlassian MCP server, which lets you interact with Jira and Confluence:

{tools_list}

INSTRUCTIONS:
1. Break the task into steps and think about what to do.
2. Use the available tools to accomplish each step.
3. For Jira searches, use JQL (Jira Query Language) syntax.
4. After each tool result, analyze it and decide what to do next.
5. When the task is FULLY COMPLETE, respond with your final answer as plain text WITHOUT calling any tools.

IMPORTANT: Only stop (respond without tools) when the task is truly done.
Think step by step. Be thorough but efficient."""


# Step 4: The agent loop — same structure as Stage 3, but tool calls go to the MCP server
async def run_agent(mcp: MCPClient, user_task: str) -> str:
    """Run the AI agent loop using MCP tools."""

    # Step 4a: Set up system prompt and seed the conversation
    system_prompt = build_system_prompt(mcp.get_tool_names())
    messages = [{"role": "system", "content": system_prompt}]
    print_system(system_prompt)

    messages.append({"role": "user", "content": user_task})
    print_user(user_task)

    # Step 4b: Loop until the LLM responds without tool calls (or we hit the limit)
    iteration = 0
    while iteration < MAX_ITERATIONS:
        iteration += 1
        print_iteration(iteration, len(messages))

        # Step 4c: Start a spinner while waiting for the API response
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

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=mcp.openai_tools,
            )
        except Exception as e:
            # Step 4d: Stop spinner before printing error
            stop_spinner.set()
            spinner_thread.join()
            print_error(f"API call failed: {e}")
            return f"Error: {e}"

        # Step 4e: Stop spinner after successful response
        stop_spinner.set()
        spinner_thread.join()

        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        if assistant_message.content:
            print_llm(assistant_message.content)

        # Step 4f: If no tool calls, the agent is done
        if not assistant_message.tool_calls:
            print_done(assistant_message.content)
            return assistant_message.content or ""

        # Step 4g: Execute each tool call via the MCP server
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}

            print_tool_call(tool_name, tool_args)

            # Route to MCP server instead of a local function
            result = await mcp.call_tool(tool_name, tool_args)

            print_tool_result(tool_name, result)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    print_error(f"Agent stopped after {MAX_ITERATIONS} iterations (safety limit)")
    return "Agent reached maximum iterations without completing the task."


# Step 5: Main entry point — connect to MCP server, then run the agent
async def main():
    # Step 5a: Validate environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print_error(
            "OPENAI_API_KEY not found!\n"
            "  1. Copy .env.example to .env\n"
            "  2. Add your OpenAI API key\n"
            "  3. Run again"
        )
        sys.exit(1)

    if not os.getenv("ATLASSIAN_URL"):
        print_error(
            "Atlassian config not found! Add to .env:\n"
            "  ATLASSIAN_URL=https://yoursite.atlassian.net\n"
            "  ATLASSIAN_USERNAME=you@example.com\n"
            "  ATLASSIAN_API_TOKEN=your-api-token\n\n"
            "  Get your API token at:\n"
            "  https://id.atlassian.com/manage-profile/security/api-tokens"
        )
        sys.exit(1)

    print_header("STAGE 4: MCP (DYNAMIC TOOL DISCOVERY)")
    print(f"{DIM}  Model: {MODEL}")
    print(f"  Max iterations per turn: {MAX_ITERATIONS}")
    print(f"  Tools: Discovered dynamically from Atlassian MCP server")
    print(f"  Loop:  YES — same agent loop as Stages 2-3")
    print(f"  Memory: NONE — each turn starts fresh{RESET}")

    # Step 5b: Connect to the Atlassian MCP server
    print(f"\n{CYAN}{BOLD}Connecting to Atlassian MCP server...{RESET}")

    try:
        mcp = await create_atlassian_client()
    except FileNotFoundError:
        print_error(
            "mcp-atlassian not found! Install it:\n"
            "  pip install mcp-atlassian"
        )
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to connect to MCP server: {e}")
        sys.exit(1)

    # Step 5c: Show discovered tools
    tool_names = mcp.get_tool_names()
    print_mcp_info(f"Connected! Discovered {len(tool_names)} tools:")
    for name in tool_names:
        print(f"{CYAN}  • {name}{RESET}")
    print(f"\n{DIM}  Compare with Stage 3: tools came from an external server, not hardcoded!{RESET}")
    print(f"{DIM}  Type 'quit' or 'exit' to stop.{RESET}")

    # Step 5d: Run in single-shot mode (CLI arg) or interactive mode
    try:
        if len(sys.argv) > 1:
            task = " ".join(sys.argv[1:])
            await run_agent(mcp, task)
        else:
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

                await run_agent(mcp, task)

    finally:
        # Step 5e: Clean shutdown — disconnect from MCP server
        print_mcp_info("Disconnecting from MCP server...")
        await mcp.close()
        print_mcp_info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
