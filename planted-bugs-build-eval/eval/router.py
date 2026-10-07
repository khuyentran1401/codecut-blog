"""Route a customer email to one support queue."""

from llm import ask_claude

SYSTEM_PROMPT = """You route customer emails for a bank to one of five queues:
cards, billing, account, transfers, top-up.

Reply in this format:
Queue: <queue>
Reason: <one sentence>

Examples:

Email: My top up is pending.
Queue: top-up
Reason: The customer is asking about a top-up that has not completed.

Email: I lost my card
Queue: cards
Reason: The customer needs help with a lost card.

Email: Can I have a refund?
Queue: billing
Reason: Refunds are handled by billing.
"""


def route_email(email: str) -> str:
    return ask_claude(SYSTEM_PROMPT, email)
