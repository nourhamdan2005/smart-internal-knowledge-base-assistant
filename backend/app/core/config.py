from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Internal Knowledge Base Assistant API"

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "smart_knowledge_base"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()