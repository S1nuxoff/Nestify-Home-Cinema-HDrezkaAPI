import uvicorn
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.api import api_router
from fastapi.middleware.cors import CORSMiddleware
from app.db.base import create_all_tables
from app.api.v1.endpoints import ws_live_session
from app.api.v1.endpoints import session

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_live_session.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или конкретный список доменов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await create_all_tables()
    print("Database initialized.")


@app.get("/")
async def root():
    return {"message": "Welcome to the API"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
