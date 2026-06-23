from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.api.ws import ws_router


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Dating App MVP — Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Phase 5 前收窄為 staging domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint — returns ok when the service is running."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env,
    }


app.include_router(api_router)
app.include_router(ws_router)


@app.get("/", tags=["System"])
def root():
    """Root redirect hint."""
    return {"message": "Dating App API is running. Visit /docs for API documentation."}
