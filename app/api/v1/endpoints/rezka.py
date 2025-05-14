from fastapi import APIRouter, HTTPException, Query
from typing import List
import datetime

from app.services.media.add_movie import add_movie
from app.services.rezka import extract_id_from_url, get_search
from app.services.media.get_movie import get_movie_db

from app.services.media.get_watch_history import get_watch_history

from app.schemas.rezka import (
    Rezka,
    FilmCard,
    GetSourceResponse,
    TopNavCategoriesResponse,
    WatchHistoryItem,
    MovieHistoryCreate,
)
from app.services.rezka import (
    get_movie,
    search,
    get_page,
    get_movie_ifo,
    get_categories,
)
from app.core.config import settings
from app.services.rezka import get_source

router = APIRouter()


@router.get("/get_movie", response_model=Rezka, summary="Get rezka movie by link")
async def fetch_movie(link: str):
    id = extract_id_from_url(link)
    movie = await get_movie_db(id)
    if not movie:
        movie = await get_movie(link)
        if not movie:
            raise HTTPException(status_code=404, detail="movie not found")
        await add_movie(movie)
        return movie
    else:
        return movie


@router.get("/get_watch_history")
async def fetch_watch_history(user_id: int = Query(..., description="ID користувача")):
    try:
        result = await get_watch_history(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[FilmCard])
async def search_movie(title: str):
    search_result = await search(f"{settings.SEARCH_URL_BASE}{title}")
    if not search_result:
        raise HTTPException(status_code=404, detail="movie not found")
    return search_result


@router.get("/get_search")
async def get_searh_suggestions(title: str):
    search_result = await get_search(title)
    if not search_result:
        raise HTTPException(status_code=404, detail="movie not found")
    return search_result


@router.get("/get_page", response_model=List[FilmCard])
async def fetch_page(link: str):
    page = await get_page(link)
    if not page:
        raise HTTPException(status_code=404, detail="movie not found")
    return page


@router.get(
    "/get_source",
    response_model=GetSourceResponse,
    summary="Get direct video links (minimal)",
)
def fetch_source_api(
    film_id: str,
    translator_id: str,
    season_id: int = 0,
    episode_id: int = 0,
    action: str = "get_stream",
):
    """
    Возвращает список source_links по указанному фильму/сериалу, переводчику, сезону и эпизоду.
    """

    params = {"t": datetime.datetime.now()}
    favs_value = ""

    translators = [{"id": translator_id, "name": ""}]
    episodes = []

    source_result = get_source(
        film_id=film_id,
        translators=translators,
        season_from_url=season_id,
        episode_from_url=episode_id,
        episodes=episodes,
        ctrl_favs_value=favs_value,
        action=action,
        params=params,
    )

    if not source_result:
        raise HTTPException(status_code=404, detail="No source links found")

    # Возвращаем в виде { "sources": [...] }
    return GetSourceResponse(sources=source_result)


@router.get(
    "/get_categories",
    response_model=TopNavCategoriesResponse,
    summary="Получить категории верхнего меню с подменю",
)
def get_topnav_categories(url: str):
    try:
        result = get_categories(url)
        if not result.get("categories"):
            raise HTTPException(status_code=404, detail="Категории не найдены")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
