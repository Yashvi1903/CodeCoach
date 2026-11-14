from typing import Protocol,Type,TypeVar
from pydantic import BaseModel
from app.llm.client import generate_structured


T = TypeVar("T",bound=BaseModel)

class LLMCall(Protocol):
    def __call__(self, prompt: str, schema: Type[T], *, strong: bool = False) -> T: ...


def default_llm(prompt: str, schema: Type[T], *, strong: bool = False) -> T:
    return generate_structured(prompt, schema, use_strong_model=strong)