from langchain_core.prompts import FewShotPromptTemplate,PromptTemplate
from pydantic import BaseModel,Field
from app.llm.client import generate_structured

class ConstraintExtraction(BaseModel):
   class ConstraintExtraction(BaseModel):
    max_n: int = Field(description="Upper bound of the structural input size (ignore element values like a_i <= 10^9).")
    exact_quote_in_text: str = Field(description="Exact substring from the text containing this constraint.")
    llm_proposed_big_o: str = Field(description="Proposed Big-O ceiling, e.g. 'O(N log N)', 'O(N^2)', 'O(N)'.")

class ComplexityResult(BaseModel):
  max_n:int | None=None
  big_o:str
  label:str
  verified:bool


EXAMPLES = [
    {
        "input_text": "The first line contains t (1 <= t <= 10^4). Each test case contains n (1 <= n <= 2 * 10^5) followed by n integers a_i (1 <= a_i <= 10^9). The sum of n over all test cases does not exceed 2 * 10^5.",
        "output_json": '{"max_n": 200000, "exact_quote_in_text": "sum of n over all test cases does not exceed 2 * 10^5", "proposed_big_o": "O(N log N)"}',
    },
    {
        "input_text": "The first line contains two integers n and m (1 <= n, m <= 500) — the rows and columns of the grid.",
        "output_json": '{"max_n": 500, "exact_quote_in_text": "1 <= n, m <= 500", "proposed_big_o": "O(N^3)"}',
    },
    {
        "input_text": "A single integer n (1 <= n <= 18) representing the number of items.",
        "output_json": '{"max_n": 18, "exact_quote_in_text": "1 <= n <= 18", "proposed_big_o": "O(2^N)"}',
    },
]

EXAMPLE_PROMPT=PromptTemplate(
  input_variables=["input_text","output_json"],
  template="Input text: {input_text}\nOutput: {output_json}",
)

CEILING_PROMPT = FewShotPromptTemplate(
    examples=EXAMPLES,
    example_prompt=EXAMPLE_PROMPT,
    prefix=(
        "You are an algorithmic complexity analyzer for competitive programming.\n"
        "Given a problem's input specification and legend, extract the structural input bound "
        "that governs total runtime (ignoring element value limits like a_i <= 10^9 unless the algorithm "
        "loops over values), and propose the slowest acceptable Big-O ceiling (~10^8 operations/sec).\n\n"
        "--- EXAMPLES ---"
    ),
    suffix=(
        "\n--- TASK ---\n"
        "Analyze the following problem text and return the JSON result:\n\n"
        "Input text:\n\"\"\"\n{constraints_text}\n\"\"\""
    ),
    input_variables=["constraints_text"],
)

def _normalize_ws(s:str)->str:
  return " ".join(s.split())

def get_constraint_complexity(constraints_text:str,has_editorial:bool=False)->ComplexityResult:
    formatted_prompt=CEILING_PROMPT.format(constraints_text=constraints_text)
    extracted=generate_structured(
      prompt=formatted_prompt,
      schema=ConstraintExtraction,
      use_strong_model=False,
      temperature=0.1,
    )

    verified = _normalize_ws(extracted.exact_quote_in_text) in _normalize_ws(constraints_text)
    label = "From constraints" if has_editorial else "Estimated"

    return ComplexityResult(
        big_o=extracted.proposed_big_o,
        label=label,
        verified=verified,
        max_n=extracted.max_n,
    )