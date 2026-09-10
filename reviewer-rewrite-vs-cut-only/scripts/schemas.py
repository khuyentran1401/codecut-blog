"""Draft claims, and the three edits a restricted reviewer may return.

Every one removes something. None can add or rewrite text.
"""

from typing import Literal, Union

from pydantic import BaseModel, Field

SECTIONS = ["decisions", "action_items", "risks", "open_questions"]


class DraftSummary(BaseModel):
    """What the summarizer returns. Claim ids are added afterwards."""

    decisions: list[str] = []
    action_items: list[str] = []
    risks: list[str] = []
    open_questions: list[str] = []


class Delete(BaseModel):
    op: Literal["delete"]
    claim_id: str


class MarkUnsupported(BaseModel):
    op: Literal["mark_unsupported"]
    claim_id: str


class DropSection(BaseModel):
    op: Literal["drop_section"]
    claim_id: Literal["decisions", "action_items", "risks", "open_questions"]


Operation = Union[Delete, MarkUnsupported, DropSection]


class ReviewPlan(BaseModel):
    """No field anywhere can hold a sentence, so the reviewer cannot write."""

    operations: list[Operation] = Field(default_factory=list, max_length=25)
