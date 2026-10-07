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


def ask_claude(system: str, user: str, model: str = "haiku", meta: dict | None = None) -> str:
    """Send one message with a system prompt and return the reply text.

    If `meta` is given, it is filled with the call's usage, served models, and cost.
    """
    completed = subprocess.run(
        ["claude", "-p", "--model", model, "--system-prompt", system, *CLAUDE_FLAGS, user],
        capture_output=True,
        text=True,
        timeout=120,
    )
    stdout = completed.stdout
    response = json.loads(stdout[stdout.index("{"):])
    if meta is not None:
        meta.update({key: response.get(key) for key in ("usage", "modelUsage", "total_cost_usd", "duration_ms", "stop_reason")})
    if response.get("is_error"):
        raise RuntimeError(response.get("result"))
    return response["result"].strip()
