# app/routers/geo.py
from fastapi import APIRouter, Depends
from app.config import get_settings
from app.services.mapbox import suggest_places, get_route

router = APIRouter()

@router.get("/suggest")
def suggest(q: str, settings = Depends(get_settings)):
    return {"suggestions": suggest_places(q, settings.MAPBOX_TOKEN)}

@router.get("/route")
def route(origin: str, destination: str, settings = Depends(get_settings)):
    data = get_route(origin, destination, settings.MAPBOX_TOKEN)
    return data