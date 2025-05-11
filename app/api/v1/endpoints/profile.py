from fastapi import APIRouter
from fastapi.responses import JSONResponse
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
