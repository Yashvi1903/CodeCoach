from pydantic import BaseModel,Field

class SampleTest(BaseModel):
    input: str
    output: str

class Problem(BaseModel):
    problem_id: str | None=None
    title: str
    time_limit: str
    memory_limit: str
    legend: str
    input_spec: str
    output_spec: str
    constraints_raw: str
    raw_text: str
    samples: list[SampleTest] = Field(default_factory=list)
    note: str| None=None
    has_figures: bool=False
    raw_text: str