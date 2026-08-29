import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.rate_limit import reset_all_rate_limiters
from app.main import app
from app.rag.retrieval import _cached_query_embedding

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _reset_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    # Rate limiter buckets are process-global (see app/core/rate_limit.py),
    # so without this a test earlier in the run could exhaust a limiter's
    # quota for a later, unrelated test using the same TestClient "IP".
    reset_all_rate_limiters()
    yield


@pytest.fixture(autouse=True)
def _reset_rag_embedding_cache():
    # The query-embedding cache (app/rag/retrieval.py) is a process-global
    # lru_cache keyed only by query text; without a reset, two unrelated
    # tests that happen to use the same query string but monkeypatch
    # ai_service.embed_text differently would leak a stale vector from
    # whichever test ran first.
    _cached_query_embedding.cache_clear()
    yield


@pytest.fixture
def db_session() -> Session:
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
