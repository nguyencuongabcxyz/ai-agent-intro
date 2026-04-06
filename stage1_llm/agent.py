"""
Stage 1: LLM Only (No Tools, No Loop, No Memory)

The simplest AI app: send a message to an LLM, get text back.
The LLM cannot search the web, read files, or take actions — it only generates text.

Run:
  python stage1_llm.py "What is Python?"
  python stage1_llm.py  (interactive mode)
"""

import os
import sys
import threading
from openai import OpenAI
from dotenv import load_dotenv

# Step 1: Load environment variables from .env file (like OPENAI_API_KEY)
load_dotenv()

# Step 2: Create the OpenAI client — it uses OPENAI_API_KEY from the environment
client = OpenAI()

# Step 3: Pick which model to use, defaulting to gpt-4o if not set in .env
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


# --- Colored output helpers (make the demo visual) ---

YELLOW = "\033[93m"
BLUE = "\033[94m"
GREEN = "\033[92m"
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
    print(f"\n{BOLD}[USER]{RESET}")
    print(f"  {text}")


def print_llm(text):
    print(f"\n{GREEN}{BOLD}[LLM RESPONSE]{RESET}")
    for line in text.strip().split('\n'):
        print(f"{GREEN}  {line}{RESET}")


def print_error(text):
    print(f"\n{RED}{BOLD}[ERROR]{RESET} {RED}{text}{RESET}")


# Step 4: Define the system prompt — this controls the LLM's personality and behavior
SYSTEM_PROMPT = """You are a helpful AI assistant.

You can answer questions, explain concepts, write text, and have conversations.
Be concise and clear in your responses."""


def call_llm(user_message: str) -> str:
    """Send a single message to the LLM and return its text response."""

    # Step 5: Build the messages list — this is everything the LLM will see
    # "system" = instructions for the LLM, "user" = what the human typed
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    print_system(SYSTEM_PROMPT)
    print_user(user_message)

    # Step 6: Show a "thinking" spinner while waiting for the API response
    # We use a background thread so the animation runs while the API call blocks
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

    # Step 7: Call the OpenAI API — send messages in, get a response back
    # Note: no tools= parameter, so the LLM can only generate text
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )
    except Exception as e:
        stop_spinner.set()
        spinner_thread.join()
        print_error(f"API call failed: {e}")
        return f"Error: {e}"

    # Step 8: Stop the spinner now that we have the response
    stop_spinner.set()
    spinner_thread.join()

    # Step 9: Extract the text from the response object
    result = response.choices[0].message.content or ""
    print_llm(result)
    return result


def main():
    # Step 10: Check that the API key exists before trying to call the LLM
    if not os.getenv("OPENAI_API_KEY"):
        print_error(
            "OPENAI_API_KEY not found!\n"
            "  1. Copy .env.example to .env\n"
            "  2. Add your OpenAI API key\n"
            "  3. Run again"
        )
        sys.exit(1)

    print_header("STAGE 1: LLM ONLY")
    print(f"{DIM}  Model: {MODEL}")
    print(f"  Type 'quit' or 'exit' to stop.{RESET}")

    # Step 11: If a message was passed as a command-line argument, use it directly
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        call_llm(task)
        return

    # Step 12: Start an interactive loop so the user can keep chatting
    # Each turn is stateless — the LLM has no memory of previous turns
    while True:
        print(f"\n{BOLD}Ask the LLM anything:{RESET}")
        try:
            user_input = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM}Goodbye!{RESET}")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print(f"{DIM}Goodbye!{RESET}")
            break

        call_llm(user_input)


if __name__ == "__main__":
    main()
