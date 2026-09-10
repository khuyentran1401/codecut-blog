"""The summary schema the summarizer fills."""

from pydantic import BaseModel

SECTIONS = ["decisions", "action_items", "risks", "open_questions"]


class DraftSummary(BaseModel):
    """What the summarizer returns. Claim ids are added afterwards."""

    decisions: list[str] = []
    action_items: list[str] = []
    risks: list[str] = []
    open_questions: list[str] = []
