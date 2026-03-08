from tools import *
from agno.agent import Agent
from agno.models.openai.responses import OpenAIResponses
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are a helpful coding agent.
When using back commands, use the non interactive mode.

Keep timeout for bash commands in 20 seconds.

TOOLS = {
    "read": (
        "Read file with line numbers (file path, not directory)",
        {"path": "string", "offset": "number?", "limit": "number?"},
        read,
    ),
    "write": (
        "Write content to file",
        {"path": "string", "content": "string"},
        write,
    ),
    "edit": (
        "Replace old with new in file (old must be unique unless all=true)",
        {"path": "string", "old": "string", "new": "string", "all": "boolean?"},
        edit,
    ),
    "glob": (
        "Find files by pattern, sorted by mtime",
        {"pat": "string", "path": "string?"},
        glob,
    ),
    "grep": (
        "Search files for regex pattern",
        {"pat": "string", "path": "string?"},
        grep,
    ),
    "bash": (
        "Run shell command",
        {"cmd": "string", "timeout": "number?"},
        bash,
    ),
}
"""

def _create_agent():
    agent = Agent(
        system_message=SYSTEM_PROMPT,
        tools=[read, write, edit, glob, grep, bash],
        model=OpenAIResponses("gpt-5.4", reasoning_effort="medium"),
    )
    return agent

coding_agent = _create_agent()