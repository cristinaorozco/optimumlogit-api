# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, load_tolls_dataset
from app.routers import quote, geo, market


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Optimum Logit API", version="1.0.0")

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Estado global: dataset de peajes ---
    @app.on_event("startup")
    def _load_resources():
        tolls_geo = load_tolls_dataset(settings.TOLLS_DATA_PATH)
        # Guarda el geojson en app.state para que lo consuman services/tolls.py o routers
        app.state.tolls_geojson = tolls_geo

    # --- Routers ---
    # Asegúrate que quote.router usa el nuevo esquema (pallets, etc.)
    app.include_router(quote.router, prefix="/v1", tags=["quote"])
    app.include_router(geo.router,   prefix="/v1/geo", tags=["geo"])
    app.include_router(market.router, prefix="/v1/market", tags=["market"])

    return app


app = create_app()