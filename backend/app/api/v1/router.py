from fastapi import APIRouter

from app.api.v1 import auth, profiles, preferences

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(profiles.router)
api_router.include_router(preferences.router)
