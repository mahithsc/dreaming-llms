# dreaming-llm

A minimal coding agent that dreams.

Agents accumulate context over the course of a day — they help you build projects, debug problems, learn new tools. But when the conversation ends, that knowledge is gone. Existing memory systems try to fix this by storing fragments of past interactions, but what you get back is sharded context: bits and pieces that lack the structure of what the agent actually *learned*.

dreaming-llm is a simple implementation of what it looks like for an agent to go to "sleep" and organize the important work it's done throughout the day into meaningful, reusable skills.

## How it works
I kept the repo really small to express the concept simply.

At its core, the repo is a bare bones coding agent with `read`, `write`, `edit`, `grep`, `glob`, and `bash` tools.

- **main.py** — the chat loop. Handles user input, saves conversation transcripts to `session/`, and dispatches `/new-chat` and `/dream` commands. This is the entrypoint.
- **agent.py** — builds the agent. Constructs the system prompt, injects any learned skills from `skills/skills_index.json`, and wires up the tools. Every conversation and every dream starts by calling `create_agent()`.
- **dream.py** — the dreaming phase. When `/dream` is triggered, a fresh agent is given a reflection prompt: review new sessions, decide what's worth remembering, and write skill files. Not every conversation produces a skill — the agent uses its judgment.
- **tools.py** — six tools the agent can use: `read`, `write`, `edit`, `glob`, `grep`, `bash`. Deliberately minimal. The bash tool streams output line-by-line with a configurable timeout.
- **skills/** — where learned skills live. Plain markdown files with structured knowledge (when to use, step-by-step approach, code patterns, failure cases). Human-readable, editable, version-controllable. Gitignored by default so each agent develops its own memory.
- **session/** — raw conversation transcripts. A manifest tracks which chats have been dreamed on and which are new. Also gitignored.


## Quickstart

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), an OpenAI API key.

```bash
# 1. Install uv (if you don't already have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and install dependencies
git clone https://github.com/mahithchigurupati/dreaming-llm.git
cd dreaming-llm
uv sync

# 3. Set your API key
echo "OPENAI_API_KEY=sk-..." > .env

# 4. Start chatting
uv run python main.py
```

Use the agent like normal — ask it to build things, debug code, whatever. When you're done with a conversation, type `/new-chat` to save it. When you want the agent to reflect on what it's learned, type `/dream`.