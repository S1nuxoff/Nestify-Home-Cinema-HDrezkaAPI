from app.db.session import async_session
from sqlalchemy import select
from app.models.watch_history import WatchHistory
from app.models.movies import Movie
from datetime import datetime


async def add_movie_to_history(
    user_id: int,
    movie_id: str,
    translator_id: str | None,
    action: str,
    season: int | None,
    episode: int | None,
    position_seconds: int,
):
    async with async_session() as session:
        async with session.begin():
            movie = await session.execute(select(Movie).where(Movie.id == movie_id))
            movie = movie.scalars().first()

            if not movie:
                return None

            # ⬇️ тепер враховуємо user_id
            existing_movie = await session.execute(
                select(WatchHistory).where(
                    WatchHistory.movie_id == movie_id,
                    WatchHistory.user_id == user_id,
                )
            )
            existing_movie = existing_movie.scalars().first()
            if existing_movie:
                existing_movie.updated_at = datetime.utcnow()
                existing_movie.translator_id = translator_id
                existing_movie.season = season
                existing_movie.episode = episode
                return existing_movie

            if action == "get_movie":
                season = None
                episode = None

            new_movie = WatchHistory(
                user_id=user_id,
                movie_id=movie_id,
                translator_id=translator_id,
                season=season,
                episode=episode,
                position_seconds=position_seconds,
                watched_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(new_movie)
            await session.commit()
            return new_movie
