from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.routes import router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0", default_response_class=ORJSONResponse)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(router)

@app.get("/")
async def root() -> dict:
    return {"service": settings.app_name, "status": "ok"}
