from typing import Literal
from pydantic import BaseModel,Field


LABEL_GROUNDED="Grounded in editorial"
LABEL_ESTIMATED="Estimated"

MIN_HINTS=2
MAX_HINTS=8

class LLMHintOutput(BaseModel):
    hints:list[str]=Field(description="Hints from vaguest to most specific.Between 2 and 8.")
    time_complexity: str = Field(description="Time complexity of the intended solution, e.g O(nlogn).")
    space_complexity: str | None=Field(default=None,description="Space Complexity, of null if unknown.")
    complexity_stated_in_editorial: bool=Field(
        default=False,
        description="True ONLY if the editorial text itself explicitly states the complexity.",
    )
    other_approaches: list[str]=Field(
        default_factory=list,
        description="Other approaches the editorial mentions, oneshort phrase each."
    )


class HintSet(BaseModel):
    contest_id: int
    index: str
    status: Literal["ok", "failed"] = "ok"
    label: str = LABEL_ESTIMATED
    hints: list[str] = Field(default_factory=list)
    time_complexity: str | None = None
    space_complexity: str | None = None
    complexity_label: str = "Not available"
    other_approaches: list[str] = Field(default_factory=list)
    error: str | None = None
    schema_version: int = 1