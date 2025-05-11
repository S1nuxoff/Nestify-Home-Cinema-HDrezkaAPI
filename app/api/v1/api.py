from fastapi import APIRouter
from app.api.v1.endpoints import rezka, session, profile


api_router = APIRouter()
api_router.include_router(rezka.router, prefix="/rezka", tags=["Rezka"])
api_router.include_router(session.router, prefix="/session", tags=["Sesion"])
api_router.include_router(profile.router, prefix="/profile", tags=["Profile"])
