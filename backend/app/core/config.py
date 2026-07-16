from pydantic import Field, field_validator
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

    qdrant_enabled: bool = True
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "document_chunks"
    qdrant_vector_size: int = Field(default=768, gt=0)
    qdrant_distance: str = "cosine"
    qdrant_timeout_seconds: int = Field(
        default=10,
        gt=0,
    )
    qdrant_semantic_limit: int = Field(default=30, gt=0)
    qdrant_batch_size: int = Field(default=100, gt=0)
    qdrant_sync_on_write: bool = True
    qdrant_fallback_enabled: bool = True

    @field_validator("qdrant_api_key", mode="before")
    @classmethod
    def normalize_qdrant_api_key(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = str(value).strip()

        return normalized_value or None

    @field_validator("qdrant_distance")
    @classmethod
    def validate_qdrant_distance(cls, value: str) -> str:
        normalized_value = value.strip().lower()

        if normalized_value not in {
            "cosine",
            "dot",
            "euclid",
            "manhattan",
        }:
            raise ValueError(
                "Qdrant distance must be cosine, dot, "
                "euclid, or manhattan."
            )

        return normalized_value

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
