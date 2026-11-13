from typing import Type,TypeVar
from google import genai
from google.genai import types
from pydantic import BaseModel
from app.config import settings

T=TypeVar("T",bound=BaseModel)

_client=genai.Client(api_key=settings.llm_api_key)

def generate_structured(
        prompt:str,
        schema:Type[T],
        use_strong_model: bool = False,
        temperature: float=0.1,
)->T:
    """
    Calls the LLM with a prompt template and enforces a Pydantic structured output schema.
    """
    model_name=settings.strong_model if use_strong_model else settings.small_model
    response=_client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
        ),
    )

    return schema.model_validate_json(response.text)