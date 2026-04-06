"""
tools.py — Stage 2 Tool Definitions
====================================

The 3 tools the agent can use: web_search, fetch_webpage, write_file.

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
import re
import urllib.request


# ============================================================
# PART 1: TOOL SCHEMAS (what the LLM sees)
# ============================================================
# These are JSON Schema definitions in OpenAI's tool format.
# The LLM reads these to know what tools are available and
# what parameters each tool expects.
# ============================================================

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
    {
        "type": "function",
        "function": {
            "name": "fetch_webpage",
            "description": "Fetch a webpage URL and return its text content. Use this to read the full content of a specific article or page.",
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
    },
]


# ============================================================
# PART 2: TOOL IMPLEMENTATIONS (what actually runs)
# ============================================================
# These are plain Python functions. Each one performs a real
# action. The LLM doesn't run these — YOUR code calls them.
# Every function returns a STRING because the result gets
# sent back to the LLM as a message.
# ============================================================

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


def execute_fetch_webpage(url: str) -> str:
    """Fetch a webpage and return its text content (HTML tags stripped)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > MAX_OUTPUT_CHARS:
            text = text[:MAX_OUTPUT_CHARS] + "\n\n[... PAGE TRUNCATED ...]"
        return text if text else "Page fetched but no readable text found."
    except Exception as e:
        return f"Error fetching URL: {e}"


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


# ============================================================
# PART 3: TOOL DISPATCHER (the bridge)
# ============================================================
# Maps tool names to Python functions. When the LLM says
# "call web_search", this is how we find the right function.
# ============================================================

TOOL_REGISTRY = {
    "web_search": execute_web_search,
    "fetch_webpage": execute_fetch_webpage,
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
