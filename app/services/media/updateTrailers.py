import asyncio
from sqlalchemy import select, update
from app.models.movies import Movie
from app.db.session import async_session
from app.utils.utils import check_video_exists


async def updateTrailers():
    async with async_session() as session:
        async with session.begin():
            # Получаем все фильмы
            result = await session.execute(select(Movie))
            movies = result.scalars().all()

            for item in movies:
                movie_trailer = item.trailer  # Доступ к полю trailer
                result = check_video_exists(movie_trailer)

                if result is None:
                    # Если видео недоступно, обновляем поле trailer на None
                    await session.execute(
                        update(Movie).where(Movie.id == item.id).values(trailer=None)
                    )
                    print(f"Трейлер для фильма {item.id} обновлен на None")

                # Пауза между запросами (например, 1 секунда)
                await asyncio.sleep(1)

            # Сохраняем изменения
            await session.commit()

        print("Обновление завершено.")
