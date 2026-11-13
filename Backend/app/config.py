from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_api_key: str
    small_model:str="gemini-2.5-flash"
    strong_model: str = "gemini-2.5-flash"

    class Config:
        env_file=".env"
        extra="ignore"

settings=Settings()