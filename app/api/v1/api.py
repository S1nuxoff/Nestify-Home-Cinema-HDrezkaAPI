from fastapi import APIRouter
from app.api.v1.endpoints import rezka, session


api_router = APIRouter()
api_router.include_router(rezka.router, prefix="/rezka", tags=["Rezka"])
api_router.include_router(session.router, prefix="/session", tags=["Rezka"])
# api_router.include_router(media.router, prefix="/media", tags=["Media"])
