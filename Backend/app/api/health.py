import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.common import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    settings = get_settings()

    try:
        db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        logger.exception("Database health check failed")
        database_status = "unavailable"

    return HealthResponse(
        status="ok",
        environment=settings.environment,
        database=database_status,
    )
