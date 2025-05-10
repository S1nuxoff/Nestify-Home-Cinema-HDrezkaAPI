from sqlalchemy import select
from sqlalchemy.orm import aliased
from app.models.watch_history import WatchHistory
from app.models.movies import Movie
from app.db.session import async_session
from app.utils.utils import check_video_exists
from app.services.media.updateTrailers import updateTrailers


async def get_watch_history():
    async with async_session() as session:
        async with session.begin():
            # Сортировка по updated_at в порядке убывания
            result = await session.execute(
                select(WatchHistory).order_by(
                    WatchHistory.updated_at.desc()
                )  # Сортировка по дате обновления
            )
            history = result.scalars().all()
            data = []
            for item in history:
                movie_result = await session.execute(
                    select(Movie).where(Movie.id == item.movie_id)
                )
                movie = movie_result.scalars().first()
                # trailer = check_video_exists(movie.trailer)
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
                            "release_date": movie.release_date,
                            "duration": movie.duration,
                            "position": item.position_seconds,
                            "episode": item.episode,
                            "season": item.season,
                            "translator_id": item.translator_id,
                        }
                    )

            return data
