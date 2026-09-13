from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

router = APIRouter(prefix="/api")
engine = create_async_engine(settings.database_url, pool_pre_ping=True)

@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "backend", "time": datetime.now(timezone.utc).isoformat()}

@router.get("/ready")
async def ready() -> dict:
    db_ok = False
    redis_ok = False
    try:
        async with engine.connect() as conn:
            await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=2.5)
        db_ok = True
    except Exception:
        pass

    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        redis_ok = bool(await asyncio.wait_for(redis.ping(), timeout=2.5))
    except Exception:
        pass
    finally:
        await redis.aclose()

    return {
        "status": "ok" if db_ok and redis_ok else "degraded",
        "components": {
            "backend": "ok",
            "postgres": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
        },
        "time": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/demo")
async def demo() -> dict:
    return {"message": "Shared HackAlem environment is online."}
