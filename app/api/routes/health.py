from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.redis import get_redis
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict:
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    redis_status = "ok"
    try:
        get_redis().ping()
    except Exception:
        redis_status = "unavailable"

    services_ok = db_status == "ok" and redis_status == "ok"
    return {
        "status": "ok" if services_ok else "degraded",
        "database": db_status,
        "redis": redis_status,
    }
