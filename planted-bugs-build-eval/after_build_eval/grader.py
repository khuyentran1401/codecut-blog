"""Grade a routing decision with a deterministic check on the `Queue:` line."""

import re

QUEUES = ("cards", "billing", "account", "transfers", "top-up")


def parse_queue(answer: str) -> str | None:
    """Return the queue named on the router's `Queue:` line, or None if there isn't a valid one.

    The result must be one of QUEUES. None means "format failure", which is scored
    separately from "picked the wrong queue".
    """
    # Lenient: ignore case, markdown, and "top up" vs "top-up"; a hedge like
    # "billing or account" or a missing Queue: line is a format failure.
    match = re.search(r"queue:\s*(.+)", answer.replace("*", ""), re.IGNORECASE)
    if not match:
        return None
    value = match.group(1).strip().lower().replace("top up", "top-up").rstrip(".")
    return value if value in QUEUES else None


def grade(expected: str, answer: str) -> dict:
    queue = parse_queue(answer)
    return {
        "grade": {"accuracy": float(queue == expected), "format_ok": float(queue is not None)},
        "predicted": queue,
    }
