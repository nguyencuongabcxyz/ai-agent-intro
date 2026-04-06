# TDD Demo — Agent Writes Tests First, Then Implements

## What This Demo Shows

Traditional demo (buggy-app): agent **finds and fixes** existing bugs.
This demo: agent **builds from scratch** using TDD — tests first, code second.

---

## Demo Steps

### Step 1: Agent writes tests ONLY

**Prompt:**
```
Read the requirements in ../tdd-demo/requirements.md. Write ONLY the test file at ../tdd-demo/src/validatePassword.test.ts. Cover every rule and the examples in the requirements. Do NOT write the implementation yet.
```

**What to say:**
- "We give the agent a spec. It writes tests first — no code yet. This is the RED phase of TDD."
- Run `npm test` after → all tests fail. Wall of red.

### Step 2: Agent implements to make tests pass

**Prompt:**
```
Now write ../tdd-demo/src/validatePassword.ts to make all the tests pass. Read the test file to understand what's expected. Run npm test in ../tdd-demo to verify.
```

**What to say:**
- "Now it reads the tests as its spec and writes code to satisfy them."
- When tests go green: "RED → GREEN. That's TDD."

---

## Why This Works as a Demo

- **4 simple rules** — the audience can hold them all in their head.
- **Fast** — small scope means the agent finishes quickly, keeps the demo tight.
- **Everyone understands passwords** — no domain knowledge needed.
- **Clean TDD arc** — write tests → fail → implement → pass. No ambiguity.
