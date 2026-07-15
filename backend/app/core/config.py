from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Internal Knowledge Base Assistant API"

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "smart_knowledge_base"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    embedding_model: str = "nomic-embed-text"

    retrieval_top_k: int = 5
    retrieval_min_score: int = 8
    retrieval_candidate_limit: int = 50
    retrieval_max_chunks_per_document: int = 2
    retrieval_overlap_threshold: float = 0.65
    retrieval_similarity_threshold: float = 0.85
    hybrid_keyword_weight: float = 0.4
    hybrid_semantic_weight: float = 0.6
    semantic_min_similarity: float = 0.25
    semantic_candidate_limit: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
