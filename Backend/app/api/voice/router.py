import json
from fastapi import APIRouter
from app.api.voice.ws import ws_router

router = APIRouter(prefix="/voice", tags=["voice"])
router.include_router(ws_router)