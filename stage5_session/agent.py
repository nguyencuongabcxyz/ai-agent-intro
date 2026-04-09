"""
Stage 5: Session Management (Multi-Turn Memory)

Adds multi-turn memory so the agent remembers the entire conversation.
The messages list persists across turns instead of resetting each time.
The agent loop is the same as Stage 3 — only the outer CLI loop changes.

Run:
  python stage5_agent_session.py  (interactive mode — try multi-turn!)
  python stage5_agent_session.py "first message"
"""

import os
import sys
import json
import threading
from openai import OpenAI
from dotenv import load_dotenv
from tools import TOOL_SCHEMAS, execute_tool

load_dotenv()

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
MAX_ITERATIONS = 15

# Step 1: Define color constants for terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
WHITE = "\033[97m"


# Step 2: Helper functions to print formatted, colored output
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


def print_session_info(message_count):
    """Show how many messages are currently in the session."""
    print(f"\n{WHITE}{BOLD}[SESSION]{RESET} {WHITE}{message_count} messages in memory{RESET}")


# Step 3: Define the system prompt — tells the LLM what tools it has and how to behave
SYSTEM_PROMPT = """You are a helpful AI assistant that accomplishes tasks by using tools.

You have access to these tools:
- web_search: Search the web for current information
- fetch_webpage: Fetch and read the content of a specific URL/webpage
- list_files: List files in a directory (use this to find files before reading them)
- read_file: Read the contents of a local file
- write_file: Write content to a file
- run_bash: Execute short-lived shell commands (ls, mkdir, npm install, etc.)
- grep: Search for text patterns across files in a directory

INSTRUCTIONS:
1. Break the task into steps and think about what to do.
2. Use one or more tools to accomplish each step.
3. After each tool result, analyze it and decide what to do next.
4. When the task is FULLY COMPLETE, respond with your final answer as plain text WITHOUT calling any tools.
5. You have memory of our entire conversation — refer back to earlier context when relevant.

IMPORTANT: Only stop (respond without tools) when the task is truly done.
Think step by step. Be thorough but efficient."""


# Step 4: The agent loop — accepts a messages list and returns it so memory persists
def run_agent(user_task: str, messages: list) -> tuple[str, list]:
    """Run the agent loop for one user turn. Mutates and returns messages for memory."""

    # Step 4a: Add the user's message to the conversation history
    messages.append({"role": "user", "content": user_task})
    print_user(user_task)

    iteration = 0
    while iteration < MAX_ITERATIONS:
        iteration += 1
        print_iteration(iteration, len(messages))

        # Step 4b: Start a spinner animation while waiting for the API
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

        # Step 4c: Call the OpenAI API with the full message history and tool schemas
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
            return f"Error: {e}", messages

        # Step 4d: Stop the spinner now that we have a response
        stop_spinner.set()
        spinner_thread.join()

        # Step 4e: Add the assistant's reply to the conversation history
        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        if assistant_message.content:
            print_llm(assistant_message.content)

        # Step 4f: If no tool calls, the agent is done — return the final answer
        if not assistant_message.tool_calls:
            print_done(assistant_message.content)
            return assistant_message.content or "", messages

        # Step 4g: Execute each tool the LLM requested and add results to messages
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}

            print_tool_call(tool_name, tool_args)

            result = execute_tool(tool_name, tool_args)

            print_tool_result(tool_name, result)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    print_error(f"Agent stopped after {MAX_ITERATIONS} iterations (safety limit)")
    return "Agent reached maximum iterations without completing the task.", messages


# Step 5: CLI entry point — creates the session and runs the interactive loop
def main():
    # Step 5a: Check that the API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print_error(
            "OPENAI_API_KEY not found!\n"
            "  1. Copy .env.example to .env\n"
            "  2. Add your OpenAI API key\n"
            "  3. Run again"
        )
        sys.exit(1)

    print_header("STAGE 5: SESSION MANAGEMENT (MULTI-TURN MEMORY)")
    print(f"{DIM}  Model: {MODEL}")
    print(f"  Max iterations per turn: {MAX_ITERATIONS}")
    print(f"  Tools: web_search, fetch_webpage, list_files, read_file, write_file, run_bash, grep")
    print(f"  Type 'quit' or 'exit' to stop.{RESET}")

    # Step 5b: Create the messages list ONCE — this is the session's memory
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print_system(SYSTEM_PROMPT)

    # Step 5c: If a command-line argument was provided, use it as the first turn
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        _, messages = run_agent(task, messages)

    # Step 5d: Interactive loop — pass the SAME messages list every turn for memory
    while True:
        print_session_info(len(messages))

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

        # Step 5e: Run the agent with the persistent messages list
        _, messages = run_agent(task, messages)


if __name__ == "__main__":
    main()
