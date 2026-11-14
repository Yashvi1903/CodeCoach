from pydantic import BaseModel, Field


class EditorialSection(BaseModel):
    """The part of a round's editorial that belongs to ONE problem."""

    contest_id: int
    index: str                       # "A", "B", "C1" ...
    heading: str = ""                # the heading text we matched, e.g. "980B - Marlin"
    text: str = ""                   # explanation with code blocks removed
    code: list[str] = Field(default_factory=list)   # code blocks, kept for the server only
    title_confirmed: bool = False    # True when the problem title appears in the section start