# app/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List

class PalletDimensions(BaseModel):
    length_cm: float = Field(..., gt=0)
    width_cm: float = Field(..., gt=0)
    height_cm: float = Field(..., gt=0)

class PalletsInfo(BaseModel):
    count: int = Field(..., gt=0)
    dimensions_cm: PalletDimensions
    stackable: bool = True

class QuoteRequest(BaseModel):
    origin: str
    destination: str
    weight_kg: float
    pallets: Optional[PalletsInfo] = None   # <— NUEVO

class QuoteResponse(BaseModel):
    # lo que ya tengas…
    volume_m3: Optional[float] = None       # <— NUEVO
    density_kg_m3: Optional[float] = None   # <— NUEVO
    pallet_positions: Optional[int] = None  # <— NUEVO
    tolls_count: Optional[int] = None       # si ya cuentas peajes
    tolls_cost: Optional[float] = None

class GeoSuggestResponse(BaseModel):
    suggestions: List[str]

class RouteLeg(BaseModel):
    distance_km: float
    duration_min: float
    geometry_polyline: str

class RouteResponse(BaseModel):
    legs: List[RouteLeg]
    distance_km: float
    duration_min: float

class FuelPrice(BaseModel):
    product: str  # e.g., "Special 95", "Super 98", "Diesel"
    price_per_liter: float
    effective_from: str

class FuelPricesResponse(BaseModel):
    country: str
    prices: List[FuelPrice]