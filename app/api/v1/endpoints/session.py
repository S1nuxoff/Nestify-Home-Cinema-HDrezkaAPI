# file: app/api/v1/endpoints/session.py

from fastapi import APIRouter
from app.services.session.add_session import add_session
from app.services.session.delete_session import delete_session

router = APIRouter()


@router.post("/add")
async def set_live_session(data: dict):
    await add_session(
        movie_id=data["movie_id"],
        position=data.get("position", 0),
        translator_id=data.get("translator_id"),
        season_id=data.get("season_id"),
        episode_id=data.get("episode_id"),
    )
    return {"status": "ok"}


@router.post("/remove")
async def remove_live_session(data: dict):
    await delete_session()
    return {"status": "ok"}
