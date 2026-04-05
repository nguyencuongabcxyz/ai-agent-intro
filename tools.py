"""
tools.py — Tool Definitions and Implementations
=================================================

This file contains everything related to TOOLS — the capabilities
that make an AI agent more than just a chatbot.

There are 3 parts:
  1. TOOL SCHEMAS   — JSON descriptions that tell the LLM what tools exist
  2. TOOL FUNCTIONS — The actual Python code that runs when a tool is called
  3. TOOL DISPATCHER — The bridge that connects LLM requests to real code

KEY INSIGHT: The LLM never sees your Python code. It only sees the JSON
schemas. It outputs a JSON string saying "I want to call web_search with
query='...'" — and YOUR code (the harness) is responsible for actually
executing that function and returning the result.
"""

import os
import json
import subprocess
import re
import urllib.request
from ddgs import DDGS


# ============================================================
# PART 1: TOOL SCHEMAS (what the LLM sees)
# ============================================================
# These are JSON Schema definitions in OpenAI's tool format.
# They act as a CONTRACT between your code and the LLM:
# - The LLM reads these to know what tools are available
# - The LLM uses these to know what parameters each tool expects
# - Your code uses these to validate what the LLM asks for
#
# Think of it like an API documentation — the LLM reads the docs
# to know how to call your functions.
# ============================================================

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information. Use this when you need to find up-to-date facts, data, or answers that you don't already know.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up on the web"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the local filesystem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file to read"
                    }
                },
                "required": ["path"]
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
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": "Execute a shell command and return its output. Use this for short-lived commands like mkdir, ls, npm install, pip install, git, etc. Commands that finish quickly. Do NOT use this for long-running processes like servers — use run_background for those.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_background",
            "description": "Start a long-running process in the background (like a server, watcher, or dev tool). Returns immediately with the process ID. The process keeps running in the background.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to run in the background (e.g. 'npx serve -p 3000')"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path. Use this to discover what files exist before reading them, or to explore directory structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to list (defaults to current directory if not provided)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_webpage",
            "description": "Fetch a webpage URL and return its text content. Use this when you need to read the actual content of a specific webpage/URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL to fetch (e.g. https://example.com/page)"
                    }
                },
                "required": ["url"]
            }
        }
    }
]


# ============================================================
# PART 2: TOOL IMPLEMENTATIONS (what actually runs)
# ============================================================
# These are plain Python functions. Each one performs a real
# action on your computer. The LLM doesn't run these — YOUR
# code (the harness/agent loop) calls them.
#
# Every function returns a STRING. Why? Because the result
# gets sent back to the LLM as a message, and messages are text.
# ============================================================

MAX_OUTPUT_CHARS = 5000  # Prevent huge outputs from blowing up the context


def execute_web_search(query: str) -> str:
    """Search the web using DuckDuckGo and return top results."""
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return "No results found."

        output = []
        for i, r in enumerate(results, 1):
            output.append(f"{i}. {r['title']}\n   {r['body']}\n   URL: {r['href']}")
        return "\n\n".join(output)

    except Exception as e:
        return f"Search failed: {e}"


def execute_read_file(path: str) -> str:
    """Read a file's contents. Truncates large files to prevent context overflow."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read(MAX_OUTPUT_CHARS)
        if len(content) == MAX_OUTPUT_CHARS:
            content += "\n\n[... FILE TRUNCATED — too large to show in full ...]"
        return content
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error reading file: {e}"


def execute_write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed."""
    try:
        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


def _kill_process_tree(pid):
    """Kill a process and all its children. Works on Windows and Unix."""
    try:
        if os.name == "nt":
            # taskkill /T kills the entire process tree, /F forces it
            subprocess.run(
                f"taskkill /PID {pid} /T /F",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
        else:
            import signal
            os.killpg(os.getpgid(pid), signal.SIGKILL)
    except Exception:
        pass


def execute_run_bash(command: str) -> str:
    """Execute a shell command and return stdout + stderr."""
    import threading

    TIMEOUT = 30
    stdout_chunks = []
    stderr_chunks = []

    try:
        # Start the process — we read pipes in threads so nothing blocks
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Reader threads: read in small chunks so we capture PARTIAL output
        # even if the process gets killed mid-way. This is critical —
        # if npx prints "Need to install ... Ok to proceed?" and then hangs
        # waiting for input, we want the LLM to SEE that message so it
        # can react (e.g. retry with --yes or install the package first).
        def read_pipe(pipe, chunks):
            try:
                while True:
                    chunk = pipe.read(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
            except Exception:
                pass

        t_out = threading.Thread(target=read_pipe, args=(process.stdout, stdout_chunks), daemon=True)
        t_err = threading.Thread(target=read_pipe, args=(process.stderr, stderr_chunks), daemon=True)
        t_out.start()
        t_err.start()

        # Wait for the process to finish, with a timeout
        try:
            process.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            # Process didn't finish in time — kill the whole tree
            _kill_process_tree(process.pid)
            # Give threads a moment to finish after kill
            t_out.join(timeout=3)
            t_err.join(timeout=3)

            # Collect any PARTIAL output captured before the kill —
            # this lets the LLM see WHY the command hung (e.g. a
            # "Need to install package" prompt waiting for input)
            partial_out = b"".join(stdout_chunks).decode("utf-8", errors="replace").strip()
            partial_err = b"".join(stderr_chunks).decode("utf-8", errors="replace").strip()
            partial = ""
            if partial_out:
                partial += f"\n[Partial stdout before timeout]:\n{partial_out}"
            if partial_err:
                partial += f"\n[Partial stderr before timeout]:\n{partial_err}"

            return (
                f"Error: Command timed out after {TIMEOUT} seconds and was killed.\n"
                f"The command may be waiting for interactive input or running a long-lived process.{partial}"
            )

        # Process finished normally — wait for readers to complete
        t_out.join(timeout=5)
        t_err.join(timeout=5)

        stdout = b"".join(stdout_chunks).decode("utf-8", errors="replace")
        stderr = b"".join(stderr_chunks).decode("utf-8", errors="replace")

        output = ""
        if stdout:
            output += stdout
        if stderr:
            output += "\n[STDERR]\n" + stderr
        if process.returncode != 0:
            output += f"\n[Exit code: {process.returncode}]"

        if not output.strip():
            output = "(command produced no output)"

        # Truncate to prevent context overflow
        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + "\n\n[... OUTPUT TRUNCATED ...]"

        return output

    except Exception as e:
        return f"Error running command: {e}"


def execute_run_background(command: str) -> str:
    """Start a long-running process in the background (servers, watchers, etc.)."""
    try:
        # Start the process fully detached — it won't block the agent
        if os.name == "nt":
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            )
        else:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        return (
            f"Process started in background (PID: {process.pid}).\n"
            f"Command: {command}\n"
            f"Note: Output is not captured for background processes. "
            f"The process will keep running after the agent finishes."
        )

    except Exception as e:
        return f"Error starting background process: {e}"


def execute_list_files(path: str = ".") -> str:
    """List files and directories at the given path."""
    try:
        entries = os.listdir(path)
        if not entries:
            return f"Directory '{path}' is empty."

        output = []
        for entry in sorted(entries):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                output.append(f"  [DIR]  {entry}/")
            else:
                size = os.path.getsize(full_path)
                output.append(f"  [FILE] {entry} ({size} bytes)")
        return f"Contents of '{path}':\n" + "\n".join(output)

    except FileNotFoundError:
        return f"Error: Directory not found: {path}"
    except Exception as e:
        return f"Error listing files: {e}"


def execute_fetch_webpage(url: str) -> str:
    """Fetch a webpage and return its text content (HTML tags stripped)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Strip HTML tags to get readable text
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) > MAX_OUTPUT_CHARS:
            text = text[:MAX_OUTPUT_CHARS] + "\n\n[... PAGE TRUNCATED ...]"

        return text if text else "Page fetched but no readable text found."

    except Exception as e:
        return f"Error fetching URL: {e}"


# ============================================================
# PART 3: THE TOOL DISPATCHER (the bridge)
# ============================================================
# This is the HARNESS — the critical piece that connects the
# LLM's *intent* (a JSON string saying "call web_search")
# to the *actual execution* (running the Python function).
#
# Without this, the LLM can only SAY it wants to search the web.
# With this, it can actually DO it.
#
# This is what makes tools like Cursor and Claude Code work:
# they have a dispatcher like this that maps LLM tool requests
# to real actions on your computer.
# ============================================================

TOOL_REGISTRY = {
    "web_search": execute_web_search,
    "read_file": execute_read_file,
    "write_file": execute_write_file,
    "run_bash": execute_run_bash,
    "run_background": execute_run_background,
    "list_files": execute_list_files,
    "fetch_webpage": execute_fetch_webpage,
}


def execute_tool(name: str, arguments: dict) -> str:
    """
    Execute a tool by name with the given arguments.

    This function IS the tool harness. It:
    1. Looks up the tool function by name
    2. Calls it with the arguments the LLM provided
    3. Returns the result as a string
    4. Catches any errors so the agent doesn't crash
    """
    func = TOOL_REGISTRY.get(name)
    if not func:
        return f"Error: Unknown tool '{name}'. Available tools: {list(TOOL_REGISTRY.keys())}"

    try:
        return func(**arguments)
    except TypeError as e:
        return f"Error: Wrong arguments for tool '{name}': {e}"
    except Exception as e:
        return f"Error executing '{name}': {e}"
