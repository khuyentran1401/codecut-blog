"""Grade a routing decision with an LLM judge."""

import re

from llm import ask_claude

JUDGE_PROMPT = """You are grading an email router for a bank's support team.
You will see a customer email, the correct queue chosen by a person, and the router's answer.
Rate the router's answer as a whole from 1 (poor) to 5 (excellent),
considering both whether it picked the correct queue and how helpful its reason is to the support agent who receives the email.
Reply with the number only."""

PASS_SCORE = 5


def grade(email: str, expected: str, answer: str) -> dict:
    message = f"Email: {email}\nCorrect queue: {expected}\n\nRouter answer:\n{answer}"
    reply = ask_claude(JUDGE_PROMPT, message)
    match = re.search(r"[1-5]", reply)
    score = int(match.group()) if match else 0
    return {"score": score, "passed": score >= PASS_SCORE, "judge_reply": reply}
