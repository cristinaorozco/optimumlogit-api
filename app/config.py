# app/config.py

pip install pydantic-settings

from functools import lru_cache
from pathlib import Path
from typing import List, Optional
import json

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # === Claves/secretos ===
    MAPBOX_TOKEN: str = Field(..., description="pk.eyJ1IjoiY3Jpc3RpbmFvIiwiYSI6ImNtZjA2bW9oODA2dWMya3BwZG9pbWRxd3AifQ.kpc9uO4Ecrca_pWwCudMTQ")

    # === Parámetros por defecto (puedes cambiarlos) ===
    DEFAULT_COUNTRY: str = "AE"
    DEFAULT_CITY: str = "Dubai"

    # === Rutas a datasets locales ===
    TOLLS_DATA_PATH: Path = Path("data/tolls_dubai.geojson")

    # === CORS (opcional) ===
    CORS_ALLOW_ORIGINS: List[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_tolls_dataset(path: Path) -> Optional[dict]:
    """
    Carga el GeoJSON de peajes (pórticos) si existe.
    Devuelve el dict del GeoJSON o None si no existe.
    """
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)