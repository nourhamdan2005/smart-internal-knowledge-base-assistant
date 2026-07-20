import logging
import math
import uuid
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from app.core.config import Settings, settings
from app.vectorstores.base import (
    VectorOperationStats,
    VectorPoint,
    VectorSearchResult,
    VectorStore,
    VectorStoreConfigurationError,
    VectorStoreUnavailableError,
    VectorValidationError,
)


logger = logging.getLogger(__name__)


def deterministic_point_id(chunk_id: str) -> str:
    """Create a stable Qdrant-compatible UUID for a chunk."""
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"document-chunk:{chunk_id}",
        )
    )


class QdrantVectorStore(VectorStore):
    def __init__(
        self,
        configuration: Settings = settings,
        client: AsyncQdrantClient | None = None,
    ) -> None:
        self.configuration = configuration
        self.collection_name = (
            configuration.qdrant_collection_name
        )
        self.vector_size = configuration.qdrant_vector_size
        self.distance = self._resolve_distance(
            configuration.qdrant_distance
        )
        self.batch_size = configuration.qdrant_batch_size
        self.client = client or AsyncQdrantClient(
            url=configuration.qdrant_url,
            api_key=configuration.qdrant_api_key,
            timeout=configuration.qdrant_timeout_seconds,
        )

    @staticmethod
    def _resolve_distance(value: str) -> models.Distance:
        distances = {
            "cosine": models.Distance.COSINE,
            "dot": models.Distance.DOT,
            "euclid": models.Distance.EUCLID,
            "manhattan": models.Distance.MANHATTAN,
        }

        try:
            return distances[value.lower()]
        except KeyError as exc:
            raise VectorStoreConfigurationError(
                f"Unsupported Qdrant distance: {value}."
            ) from exc

    async def initialize(self) -> None:
        try:
            exists = await self.client.collection_exists(
                self.collection_name
            )

            if exists:
                await self._validate_existing_collection()
            else:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=self.distance,
                    ),
                )

                logger.info(
                    "Created Qdrant collection %s",
                    self.collection_name,
                )

            await self._create_payload_indexes()
        except VectorStoreConfigurationError:
            raise
        except Exception as exc:
            raise VectorStoreUnavailableError(
                "Qdrant initialization failed."
            ) from exc

    async def _validate_existing_collection(self) -> None:
        information = await self.client.get_collection(
            self.collection_name
        )
        vectors = information.config.params.vectors

        if not isinstance(vectors, models.VectorParams):
            raise VectorStoreConfigurationError(
                "Named Qdrant vectors are not supported for this "
                "collection."
            )

        if vectors.size != self.vector_size:
            raise VectorStoreConfigurationError(
                "Qdrant collection vector size "
                f"{vectors.size} does not match configured size "
                f"{self.vector_size}."
            )

        if vectors.distance != self.distance:
            raise VectorStoreConfigurationError(
                "Qdrant collection distance "
                f"{vectors.distance} does not match configured "
                f"distance {self.distance}."
            )

    async def _create_payload_indexes(self) -> None:
        index_fields = {
            "chunk_id": models.PayloadSchemaType.KEYWORD,
            "document_id": models.PayloadSchemaType.KEYWORD,
            "category": models.PayloadSchemaType.KEYWORD,
            "is_active": models.PayloadSchemaType.BOOL,
            "embedding_model": models.PayloadSchemaType.KEYWORD,
        }

        for field_name, field_schema in index_fields.items():
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name=field_name,
                field_schema=field_schema,
                wait=True,
            )

    async def health_check(self) -> bool:
        try:
            return await self.client.collection_exists(
                self.collection_name
            )
        except Exception:
            logger.warning(
                "Qdrant health check failed",
                exc_info=True,
            )
            return False

    def _validate_embedding(
        self,
        embedding: list[float],
    ) -> list[float]:
        if not isinstance(embedding, list) or not embedding:
            raise VectorValidationError(
                "Embedding must be a non-empty numeric list."
            )

        if len(embedding) != self.vector_size:
            raise VectorValidationError(
                f"Embedding has {len(embedding)} dimensions; "
                f"expected {self.vector_size}."
            )

        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in embedding
        ):
            raise VectorValidationError(
                "Embedding values must be finite numbers."
            )

        return [float(value) for value in embedding]

    def _point_struct(
        self,
        point: VectorPoint,
    ) -> models.PointStruct:
        embedding = self._validate_embedding(point.embedding)

        if point.embedding_dimensions != len(embedding):
            raise VectorValidationError(
                "Embedding metadata does not match vector dimensions."
            )

        payload: dict[str, Any] = {
            **point.metadata,
            "chunk_id": point.chunk_id,
            "document_id": point.document_id,
            "chunk_index": point.chunk_index,
            "title": point.title,
            "category": point.category,
            "content": point.content,
            "is_active": point.is_active,
            "embedding_model": point.embedding_model,
            "embedding_dimensions": point.embedding_dimensions,
        }

        return models.PointStruct(
            id=deterministic_point_id(point.chunk_id),
            vector=embedding,
            payload=payload,
        )

    async def upsert_chunks(
        self,
        points: list[VectorPoint],
    ) -> VectorOperationStats:
        if not points:
            return VectorOperationStats()

        point_structs = [
            self._point_struct(point)
            for point in points
        ]
        stats = VectorOperationStats()

        try:
            for start in range(0, len(point_structs), self.batch_size):
                batch = point_structs[start : start + self.batch_size]

                await self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                    wait=True,
                )

                stats.processed += len(batch)
                stats.batches += 1

            return stats
        except Exception as exc:
            stats.failed = len(point_structs) - stats.processed
            raise VectorStoreUnavailableError(
                "Qdrant vector upsert failed."
            ) from exc

    @staticmethod
    def _match_condition(
        key: str,
        value: Any,
    ) -> models.FieldCondition:
        return models.FieldCondition(
            key=key,
            match=models.MatchValue(value=value),
        )

    def _search_filter(
        self,
        category: str | None,
        document_ids: list[str] | None,
    ) -> models.Filter:
        conditions: list[models.Condition] = [
            self._match_condition("is_active", True),
        ]

        if category:
            conditions.append(
                self._match_condition("category", category)
            )

        if document_ids:
            conditions.append(
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchAny(any=document_ids),
                )
            )

        return models.Filter(must=conditions)

    async def search(
        self,
        embedding: list[float],
        limit: int,
        category: str | None = None,
        document_ids: list[str] | None = None,
    ) -> list[VectorSearchResult]:
        query_vector = self._validate_embedding(embedding)
        query_filter = self._search_filter(
            category,
            document_ids,
        )

        try:
            if hasattr(self.client, "query_points"):
                response = await self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    with_payload=True,
                    with_vectors=False,
                )
                points = response.points
            else:
                points = await self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    with_payload=True,
                    with_vectors=False,
                )
        except Exception as exc:
            raise VectorStoreUnavailableError(
                "Qdrant semantic search failed."
            ) from exc

        results: list[VectorSearchResult] = []

        for point in points:
            payload = dict(point.payload or {})
            chunk_id = str(payload.get("chunk_id", ""))

            if not chunk_id:
                continue

            results.append(
                VectorSearchResult(
                    chunk_id=chunk_id,
                    document_id=str(
                        payload.get("document_id", "")
                    ),
                    score=float(point.score),
                    payload=payload,
                )
            )

        return results

    async def delete_by_chunk_ids(
        self,
        chunk_ids: list[str],
    ) -> int:
        unique_chunk_ids = list(dict.fromkeys(chunk_ids))

        if not unique_chunk_ids:
            return 0

        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[
                        deterministic_point_id(chunk_id)
                        for chunk_id in unique_chunk_ids
                    ]
                ),
                wait=True,
            )
        except Exception as exc:
            raise VectorStoreUnavailableError(
                "Qdrant chunk deletion failed."
            ) from exc

        return len(unique_chunk_ids)

    async def delete_by_document_id(
        self,
        document_id: str,
    ) -> int:
        count_before = await self.count(document_id=document_id)
        document_filter = models.Filter(
            must=[
                self._match_condition(
                    "document_id",
                    document_id,
                )
            ]
        )

        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=document_filter
                ),
                wait=True,
            )
        except Exception as exc:
            raise VectorStoreUnavailableError(
                "Qdrant document deletion failed."
            ) from exc

        return count_before

    async def count(
        self,
        document_id: str | None = None,
    ) -> int:
        count_filter = None

        if document_id:
            count_filter = models.Filter(
                must=[
                    self._match_condition(
                        "document_id",
                        document_id,
                    )
                ]
            )

        try:
            result = await self.client.count(
                collection_name=self.collection_name,
                count_filter=count_filter,
                exact=True,
            )
        except Exception as exc:
            raise VectorStoreUnavailableError(
                "Qdrant count operation failed."
            ) from exc

        return int(result.count)

    async def close(self) -> None:
        await self.client.close()
