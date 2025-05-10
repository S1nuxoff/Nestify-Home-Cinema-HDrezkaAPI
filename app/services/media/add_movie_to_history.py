from app.db.session import async_session
from sqlalchemy import select
from app.models.watch_history import WatchHistory
from app.models.movies import Movie
from datetime import datetime


async def add_movie_to_history(
    movie_id,
    translator_id,
    action,
    season,
    episode,
    position_seconds,
):
    async with async_session() as session:
        async with session.begin():
            movie = await session.execute(select(Movie).where(Movie.id == movie_id))
            movie = movie.scalars().first()

            if not movie:
                return None

            existing_movie = await session.execute(
                select(WatchHistory).where(WatchHistory.movie_id == movie_id)
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
