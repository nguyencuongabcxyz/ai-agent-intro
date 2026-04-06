# Stage 1: The Brain — LLM Only

## What to Tell the Audience

### Opening — The Analogy (2 min)

**"Imagine a genius locked in a room."**

- Picture the smartest person you've ever met — they speak every programming language, they've read every textbook, every Stack Overflow answer, every technical blog ever written.
- But they're **locked in a sealed room**. No windows, no phone, no internet. Just a mail slot in the door.
- You slide a question through the slot. They think hard, write an answer on paper, and slide it back. That's it. That's the entire interaction.
- They're brilliant — they can reason, explain, write code, translate languages, debate philosophy.
- But ask them: **"What files are on my desktop right now?"** They can't look. They'll guess. Maybe they'll make something up that sounds plausible.
- Ask them: **"What happened in the news today?"** They don't know. The last newspaper they saw was from months ago (their training cutoff date). Everything after that is a blind spot.
- Ask them: **"Create a file on my computer."** They can write the content on paper and slide it to you, but they can't reach through the slot and actually create it.

**"That's what an LLM is. A genius trapped in a room. Incredibly smart, but completely isolated from the real world."**

- They can **think** but they can't **act**.
- They can **reason** but they can't **verify**.
- They can **remember what they learned** but they can't **learn anything new**.

### Why This Matters (1 min)
- Every AI product you use — Claude Code, Cursor, ChatGPT — the LLM inside is still this genius in a room.
- The difference is what's built **around** the room. The tools, the loop, the connections to the outside world.
- Stage 1 is the room. By Stage 5, we'll have given the genius hands, eyes, and a memory.

### Walk Through the Code (3 min)
- **System prompt** (line 71-74): This is like the instructions you tape to the wall of the room — "You are a helpful assistant." It shapes HOW the genius answers, but doesn't give them new abilities.
- **Messages list** (line 82-85): The paper you slide through the mail slot — system instructions + your question. This is ALL the genius sees.
- **API call** (line 108-111): One function call — `client.chat.completions.create()`. You slide the paper in, they slide an answer back. That's the entire "AI" part.
- **No tools parameter**: Notice there's no `tools=` in the API call. The genius has no mail slot to the outside world — only to you.

---

## What to Explain Further

### The Genius Analogy — Going Deeper

**What the genius CAN do (impressively well):**
- Explain complex concepts ("How does a database index work?")
- Write code from scratch ("Write a Python function to sort a list")
- Translate between languages, summarize long texts, brainstorm ideas
- Reason step by step through a problem

**What the genius CANNOT do (and this is the trap):**
- Check if a file exists on your computer — they'll guess
- Look up today's weather, stock price, or news — they're stuck with old knowledge
- Run a command, install a package, or start a server — they can only describe how
- Verify their own answer — if they're wrong, they have no way to double-check

**The knowledge cutoff is like the last newspaper:**
- The genius read everything up to their cutoff date. After that, nothing.
- Ask about a library released last month? They might hallucinate a plausible-sounding answer.
- This is why LLMs confidently say wrong things — they don't know what they don't know.

### The System Prompt is Everything
- The system prompt shapes how the genius behaves. Same genius, different instructions = different personality.
- Claude Code's system prompt is ~12,000 tokens — like taping a small novel of instructions to the wall before the genius starts.
- Cursor's `.cursorrules` file gets injected into the system prompt — that's how you customize it.

### The API is Simpler Than People Think
- It's just an HTTP POST with JSON. The SDK wraps it, but underneath it's a REST call.
- Input: messages (list of role + content). Output: a message (role: assistant + content).
- You're paying per token — every word in, every word out has a cost.
- Think of it as paying the genius per page of reading and per page of writing.

---

## Demo Examples

### Demo 1: The Genius Shines (works perfectly)
```bash
python agent.py "What is Python and why is it popular?"
```
- Show that it gives a brilliant, fluent answer.
- "See? The genius is real. The knowledge is there. The reasoning is solid."

### Demo 2: The Walls Close In (fails — can't see the real world)
```bash
python agent.py "What files are in this directory?"
```
- It will make up file names or say "I can't access your filesystem."
- **Key moment**: "We just asked the genius to look out the window. But there IS no window. They're guessing."

### Demo 3: The Old Newspaper (fails — knowledge cutoff)
```bash
python agent.py "What is the latest version of Python released this week?"
```
- It will give outdated info or hedge with "as of my last update..."
- "The genius is reading from a newspaper that's months old. They don't know what happened yesterday."

### Demo 4: Can't Take Action (fails — no hands)
```bash
python agent.py "Create a file called hello.txt with the text 'Hello World'"
```
- It will describe how to create the file, maybe write the code, but it CAN'T actually create it.
- "The genius wrote instructions on how to do it and slid them back. But they can't reach through the slot and do it themselves."

---

## Transition to Stage 2
> "So we have a genius trapped in a room. Brilliant, but helpless. How do we break them out? We don't — we build a **mail system**. We give them a way to REQUEST actions, and we execute those actions for them. That's the agent loop. And that's Stage 2."
