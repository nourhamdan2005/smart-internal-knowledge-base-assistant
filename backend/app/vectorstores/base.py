from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class VectorStoreError(RuntimeError):
    """Base error for vector-store operations."""


class VectorStoreUnavailableError(VectorStoreError):
    """Raised when the configured vector store cannot be reached."""


class VectorStoreConfigurationError(VectorStoreError):
    """Raised when vector-store configuration is incompatible."""


class VectorValidationError(VectorStoreError, ValueError):
    """Raised when a vector point or query vector is invalid."""


@dataclass(slots=True)
class VectorPoint:
    chunk_id: str
    document_id: str
    embedding: list[float]
    content: str
    title: str
    category: str
    chunk_index: int
    is_active: bool
    embedding_model: str
    embedding_dimensions: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VectorSearchResult:
    chunk_id: str
    document_id: str
    score: float
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VectorOperationStats:
    processed: int = 0
    failed: int = 0
    batches: int = 0


class VectorStore(ABC):
    collection_name: str

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize and validate the backing collection."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return whether the provider is reachable and usable."""

    @abstractmethod
    async def upsert_chunks(
        self,
        points: list[VectorPoint],
    ) -> VectorOperationStats:
        """Create or replace vector points by deterministic ID."""

    @abstractmethod
    async def search(
        self,
        embedding: list[float],
        limit: int,
        category: str | None = None,
        document_ids: list[str] | None = None,
    ) -> list[VectorSearchResult]:
        """Return nearest active vector points."""

    @abstractmethod
    async def delete_by_chunk_ids(
        self,
        chunk_ids: list[str],
    ) -> int:
        """Delete vector points for the supplied chunk IDs."""

    @abstractmethod
    async def delete_by_document_id(
        self,
        document_id: str,
    ) -> int:
        """Delete all vector points for a document."""

    @abstractmethod
    async def count(
        self,
        document_id: str | None = None,
    ) -> int:
        """Count vector points, optionally for one document."""

    @abstractmethod
    async def close(self) -> None:
        """Close provider resources."""
