"""Call Claude through the Claude Code CLI, so calls run on a Claude subscription."""

import json
import subprocess

CLAUDE_FLAGS = [
    "--tools", "",
    "--setting-sources", "",
    "--disable-slash-commands",
    "--strict-mcp-config",
    "--output-format", "json",
]


def ask_claude(system: str, user: str, model: str = "haiku") -> str:
    """Send one message with a system prompt and return the reply text."""
    completed = subprocess.run(
        ["claude", "-p", "--model", model, "--system-prompt", system, *CLAUDE_FLAGS, user],
        capture_output=True,
        text=True,
        timeout=120,
    )
    stdout = completed.stdout
    response = json.loads(stdout[stdout.index("{"):])
    if response.get("is_error"):
        raise RuntimeError(response.get("result"))
    return response["result"].strip()
