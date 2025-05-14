from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.services.user.get_users import get_all_users
import os
import json


AVATARS_JSON_PATH = os.path.join("app", "data", "avatars.json")

router = APIRouter()


@router.get("/avatars")
def get_avatars():
    try:
        with open(AVATARS_JSON_PATH, "r", encoding="utf-8") as f:
            avatars = json.load(f)

        for avatar in avatars:
            avatar["local_url"] = f"/static/avatars/{avatar['filename']}"

        return JSONResponse(content=avatars)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/users")
async def list_users():
    users = await get_all_users()
    return [
        {
            "id": user.id,
            "name": user.name,
            "avatar_url": user.avatar_url,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }
        for user in users
    ]
