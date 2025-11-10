from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    VISION_AGENT_API_KEY: str

    FLASK_ENV: str = "development"
    SECRET_KEY: str = "your_secret_here"


    OPENAI_MODEL: str = "gpt-5"
    ADE_PARSE_MODEL: str = "dpt-2-latest"
    ADE_EXTRACT_MODEL: str = "extract-latest"

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True

    STORAGE_DIR: str = "data"
    STATIC_PDFS_DIR: str = "static/uploads"
    STATIC_GRAPHS_DIR: str = "static/graphs"

    @field_validator("OPENAI_API_KEY", "VISION_AGENT_API_KEY")
    @classmethod
    def must_exist(cls, v, field):
        if not v:
            raise RuntimeError(
                f"Missing {field.field_name}. Put it in .env (see .env.example)."
            )
        return v

    class Config:
        env_file = ".env"

settings = Settings()

# Ensure folders exist
Path(settings.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.STATIC_PDFS_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.STATIC_GRAPHS_DIR).mkdir(parents=True, exist_ok=True)
Path("data/outputs").mkdir(parents=True, exist_ok=True)
