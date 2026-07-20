import pytest
from pydantic import ValidationError

from app.core.config import Settings


def make_settings(**values):
    return Settings(_env_file=None, **values)


def test_qdrant_settings_have_safe_defaults():
    configuration = make_settings()

    assert configuration.qdrant_enabled is True
    assert configuration.qdrant_url == "http://localhost:6333"
    assert configuration.qdrant_vector_size == 768
    assert configuration.qdrant_distance == "cosine"
    assert configuration.qdrant_batch_size == 100
    assert configuration.qdrant_fallback_enabled is True


def test_empty_qdrant_api_key_is_normalized():
    configuration = make_settings(qdrant_api_key="   ")

    assert configuration.qdrant_api_key is None


@pytest.mark.parametrize(
    "field_name",
    [
        "qdrant_vector_size",
        "qdrant_batch_size",
        "qdrant_semantic_limit",
        "qdrant_timeout_seconds",
    ],
)
def test_qdrant_positive_settings_are_validated(field_name):
    with pytest.raises(ValidationError):
        make_settings(**{field_name: 0})
