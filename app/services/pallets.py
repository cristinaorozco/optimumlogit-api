# app/services/pallets.py
def compute_volume_m3(L, W, H, count):
    return (L*W*H)/1e6 * count

def compute_density(weight_kg, volume_m3):
    return weight_kg / volume_m3 if volume_m3 > 0 else None

def estimate_pallet_positions(dim_cm, count, stackable):
    # regla simple inicial; ajusta a tu flota
    per_position = 1 if not stackable else 0.5
    return int((count * per_position) + 0.999)