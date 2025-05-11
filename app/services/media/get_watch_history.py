from sqlalchemy import select
from app.models.watch_history import WatchHistory
from app.models.movies import Movie
from app.db.session import async_session


async def get_watch_history(user_id: int):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(WatchHistory)
                .where(WatchHistory.user_id == user_id)
                .order_by(WatchHistory.updated_at.desc())
            )
            history = result.scalars().all()
            data = []

            for item in history:
                movie_result = await session.execute(
                    select(Movie).where(Movie.id == item.movie_id)
                )
                movie = movie_result.scalars().first()

                if movie:
                    data.append(
                        {
                            "id": item.movie_id,
                            "title": movie.title,
                            "link": movie.link,
                            "origin_name": movie.origin_name,
                            "release_date": movie.release_date,
                            "description": movie.description,
                            "updated_at": item.updated_at,
                            "age": movie.age,
                            "trailer": movie.trailer,
                            "genre": movie.genre,
                            "image": movie.image,
                            "country": movie.country,
                            "duration": movie.duration,
                            "position": item.position_seconds,
                            "episode": item.episode,
                            "season": item.season,
                            "translator_id": item.translator_id,
                        }
                    )

            return data
