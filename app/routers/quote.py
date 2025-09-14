# app/routers/quote.py
from app.schemas import QuoteRequest, QuoteResponse
from app.services.pallets import compute_volume_m3, compute_density, estimate_pallet_positions

@router.post("/v1/quote", response_model=QuoteResponse)
def make_quote(req: QuoteRequest):
    resp = QuoteResponse( /* lo que ya tenías */ )

    if req.pallets:
        L = req.pallets.dimensions_cm.length_cm
        W = req.pallets.dimensions_cm.width_cm
        H = req.pallets.dimensions_cm.height_cm
        count = req.pallets.count

        vol = compute_volume_m3(L, W, H, count)
        dens = compute_density(req.weight_kg, vol)
        positions = estimate_pallet_positions(req.pallets.dimensions_cm, count, req.pallets.stackable)

        resp.volume_m3 = round(vol, 3)
        resp.density_kg_m3 = round(dens, 1) if dens else None
        resp.pallet_positions = positions

    # si ya integras peajes/costo combustible, añade resp.tolls_count / resp.tolls_cost aquí

    return resp