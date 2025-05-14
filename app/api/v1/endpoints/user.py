from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.services.user.create_user import create_user
from app.services.media.add_movie_to_history import add_movie_to_history

from sqlalchemy.exc import SQLAlchemyError
from app.schemas.rezka import MovieHistoryCreate

router = APIRouter()


class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    avatar_url: str | None = None


@router.post("/create")
async def create_user_endpoint(payload: CreateUserRequest):
    try:
        user = await create_user(name=payload.name, avatar_url=payload.avatar_url)
        return {
            "id": user.id,
            "name": user.name,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at,
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except SQLAlchemyError as se:
        raise HTTPException(status_code=500, detail="Database error")


@router.post(
    "/add_movie_to_history",
    summary="Add movie to watch history",
)
async def add_movie_to_history_ee(
    data: MovieHistoryCreate,
    user_id: int = Query(..., description="ID користувача"),
):
    result = await add_movie_to_history(
        user_id=user_id,
        movie_id=data.movie_id,
        translator_id=data.translator_id,
        action=data.action,
        season=data.season,
        episode=data.episode,
        position_seconds=data.position_seconds,
    )
    return result
