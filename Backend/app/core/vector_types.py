"""Embedding vector column type for RAG chunk storage.

Same dialect-branch shape as `GeographyPoint` in `app/core/geo_types.py`: real
pgvector storage (with distance-operator support) on PostgreSQL, and a plain
JSON-encoded fallback on the SQLite database used by the test suite (see
app/tests/conftest.py), which has no vector extension. Retrieval code branches
on `db.bind.dialect.name` the same way `complaint_repository.list_within_radius`
does for PostGIS vs. a Python-side Haversine fallback.
"""

import json

from pgvector.sqlalchemy import Vector as PgVector
from sqlalchemy.types import Text, TypeDecorator


class EmbeddingVector(TypeDecorator):
    impl = Text
    cache_ok = True

    def __init__(self, dimensions: int, *args, **kwargs) -> None:
        self.dimensions = dimensions
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PgVector(self.dimensions))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: list[float] | None, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect) -> list[float] | None:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return list(value)
        return json.loads(value)
