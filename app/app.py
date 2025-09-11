from datetime import datetime
import logging
from typing import Optional, Dict

from fastapi import FastAPI, Depends, Header, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from src.inference import predict_one
from app.pricing_rules import get_rules_for_client, postprocess_rate
from app.route_features_mapbox import compute_route_features

# ---------------------------
# FastAPI app
# ---------------------------
app = FastAPI(
    title="Optimal Logit AI – Freight Rate API",
    version="1.1.0",
    description="Multi-tenant freight rate prediction (per-client rules via x-client-id).",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # in prod: set your UI domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("uvicorn.error")
MODEL_VERSION = "freight_rf_v1"

# ---------------------------
# Simple security (demo)
# In production: store these in env vars or a secret manager.
# ---------------------------
CLIENT_API_KEYS: Dict[str, str] = {
    "acme": "ACME_SECRET_123",
    "masterlogistics": "MASTER_SECRET_456",
}
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def require_auth(
    x_client_id: str = Header(..., description="Client identifier, e.g. acme"),
    x_api_key: Optional[str] = Depends(api_key_header),
) -> str:
    if x_client_id not in CLIENT_API_KEYS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown client_id")
    if x_api_key != CLIENT_API_KEYS[x_client_id]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    return x_client_id

# ---------------------------
# Schemas
# ---------------------------
class FreightRequest(BaseModel):
    client_type: str = Field(..., examples=["retailer"])
    origin: str = Field(..., examples=["Jebel Ali Port"])
    destination: str = Field(..., examples=["Al Quoz"])
    distance_km: float = Field(gt=0, examples=[30])
    load_type: str = Field(..., examples=["dry"])
    load_weight_tons: float = Field(gt=0, examples=[3.2])
    vehicle_type: str = Field(..., examples=["7t_truck"])
    fuel_price_aed_per_litre: float = Field(gt=0, examples=[3.1])
    salik_gates: int = Field(ge=0, examples=[2])
    salik_charges_aed: float = Field(ge=0, examples=[8.0])
    customs_fees_aed: float = Field(ge=0, examples=[60.0])
    waiting_time_hours: float = Field(ge=0, examples=[1.5])
    contract_type: str = Field(..., examples=["spot"])
    backhaul_available: int = Field(ge=0, le=1, examples=[0])
    month: int = Field(ge=1, le=12, examples=[8])
    season: str = Field(..., examples=["summer"])
    weather: str = Field(..., examples=["hot"])
    peak_demand_factor: float = Field(gt=0, examples=[1.06])

# ---------------------------
# Root & Health
# ---------------------------
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "freight-rate-api", "version": MODEL_VERSION}

# ---------------------------
# Prediction endpoints
# ---------------------------
@app.post("/v1/predict", tags=["rates"])
def predict(req: FreightRequest, client_id: str = Depends(require_auth)):
    """
    Predicts a raw rate with the ML model and applies client business rules
    (minimums, fixed charges, rounding) loaded from clients/<client_id>/pricing_rules.json.
    """
    try:
        payload = req.dict()
        yhat = predict_one(payload)
        raw_rate = float(round(yhat, 2))
        low, high = round(raw_rate * 0.94, 2), round(raw_rate * 1.06, 2)  # ±6% heuristic interval

        rules = get_rules_for_client(client_id)
        pp = postprocess_rate(raw_rate, payload["vehicle_type"], rules)

        return {
            "tenant": {"client_id": client_id},
            "model": {
                "predicted_rate_aed_raw": raw_rate,
                "conf_interval_aed_raw": [low, high],
                "version": MODEL_VERSION,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
            "business_rules": {
                "vehicle_minimum_applied": pp["vehicle_minimum_applied"],
                "fixed_charges": pp["fixed_charges"],
                "rounded_to": pp["rounded_multiple"],
            },
            "breakdown": {
                "raw_rate": pp["raw_rate"],
                "after_minimum": pp["after_minimum"],
                "after_fixed_charges": pp["after_fixed_charges"],
                "final_rate_aed": pp["final_rate"],
            },
            "currency": "AED",
            "notes": "Rules loaded per client from clients/<client_id>/pricing_rules.json.",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Prediction failed")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/v1/rules", tags=["rates"])
def rules(client_id: str = Depends(require_auth)):
    """
    Returns active rules (defaults merged with client's JSON). Useful for audit and demos.
    """
    try:
        r = get_rules_for_client(client_id)
        return {"client_id": client_id, "rules": r}
    except Exception as e:
        logger.exception("Rules fetch failed")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------------------------
# Route features (Mapbox)
# ---------------------------
router_routes = APIRouter(prefix="/v1", tags=["routes"])

@router_routes.get("/route_features")
def route_features(
    origin: str,
    destination: str,
    client_id: str = Depends(require_auth),
):
    """
    Returns distance_km, salik_gates, and salik_charges_aed for a free-text origin/destination in UAE.
    Powered by Mapbox (Geocoding + Directions). Requires MAPBOX_TOKEN in environment.
    """
    return compute_route_features(origin, destination)

# Include router
app.include_router(router_routes)