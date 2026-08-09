from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Internal Knowledge Base Assistant API"
    cors_allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "smart_knowledge_base"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    embedding_provider: str = "ollama"
    embedding_model: str = "nomic-embed-text"

    gemini_api_key: str | None = None
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_dimensions: int = Field(
        default=768,
        gt=0,
    )

    llm_provider: str = "ollama"

    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"
    groq_request_timeout_seconds: float = Field(default=60, gt=0)

    ollama_generation_num_predict: int = Field(default=192, gt=0)
    ollama_generation_num_ctx: int = Field(default=4096, gt=0)
    ollama_generation_temperature: float = Field(default=0.2, ge=0, le=2)
    ollama_generation_top_p: float = Field(default=0.9, gt=0, le=1)
    ollama_generation_top_k: int = Field(default=40, gt=0)
    ollama_generation_repeat_penalty: float = Field(default=1.1, gt=0)
    ollama_keep_alive: str = "5m"
    ollama_request_timeout_seconds: float = Field(default=180, gt=0)
    query_streaming_enabled: bool = True

    query_profiling_enabled: bool = False
    query_profiling_log_level: str = "INFO"
    query_profiling_include_counts: bool = True
    query_profiling_slow_threshold_ms: float = Field(default=30000, gt=0)
    query_profiling_server_timing_enabled: bool = False

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

    auth_enabled: bool = True
    jwt_secret_key: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(
        default=60,
        gt=0,
    )
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_full_name: str = "System Administrator"

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

    @field_validator(
        "jwt_secret_key",
        "bootstrap_admin_email",
        "bootstrap_admin_password",
        "groq_api_key",
        "gemini_api_key",
        mode="before",
    )
    @classmethod
    def normalize_optional_secret_value(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = str(value).strip()

        return normalized_value or None

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(
        cls,
        value: str | None,
    ) -> str | None:
        if value is not None and len(value) < 32:
            raise ValueError(
                "JWT secret key must contain at least 32 characters."
            )

        return value

    @field_validator("jwt_algorithm")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        normalized_value = value.strip().upper()

        if normalized_value != "HS256":
            raise ValueError(
                "Only the HS256 JWT algorithm is supported."
            )

        return normalized_value

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

    @field_validator("query_profiling_log_level")
    @classmethod
    def validate_query_profiling_log_level(cls, value: str) -> str:
        normalized_value = value.strip().upper()
        if normalized_value not in {"DEBUG", "INFO", "WARNING"}:
            raise ValueError("Query profiling log level must be DEBUG, INFO, or WARNING.")
        return normalized_value

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
