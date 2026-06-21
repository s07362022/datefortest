from fastapi import APIRouter

from app.api.v1 import auth, profiles, preferences, photos, tags, discover, likes

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(profiles.router)
api_router.include_router(preferences.router)
api_router.include_router(photos.router)
api_router.include_router(tags.router)
api_router.include_router(discover.router)
api_router.include_router(likes.router)
