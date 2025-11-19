import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from database import db, create_document, get_documents
from schemas import Configuration, Customer

app = FastAPI(title="Commercial Vehicle Offer Configurator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Catalog mock (could be moved to DB later) -----
# For now we serve static catalog data from backend for vehicles, colors, upholstery, options.
# These are read-only lists and do not require persistence.
VEHICLES = [
    {"id": "van-s", "name": "City Van S", "base_price": 18990},
    {"id": "van-m", "name": "Transit M", "base_price": 23990},
    {"id": "truck-l", "name": "Cargo Truck L", "base_price": 44990},
]

COLORS = [
    {"code": "WHI", "name": "Arctic White", "price": 0},
    {"code": "BLK", "name": "Midnight Black", "price": 450},
    {"code": "SLV", "name": "Glacier Silver", "price": 450},
    {"code": "RED", "name": "Signal Red", "price": 690},
]

UPHOLSTERIES = [
    {"code": "FAB-G", "name": "Fabric Grey", "price": 0},
    {"code": "FAB-B", "name": "Fabric Black", "price": 120},
    {"code": "LEA-B", "name": "Leather Black", "price": 890},
]

FACTORY_OPTIONS = [
    {"code": "PKG-COMF", "name": "Comfort Package", "price": 990},
    {"code": "NAV-PRO", "name": "Navigation Pro", "price": 1290},
    {"code": "ACC-ADAPT", "name": "Adaptive Cruise Control", "price": 790},
    {"code": "CAM-360", "name": "360° Camera", "price": 650},
]

ACCESSORIES = [
    {"code": "MAT-RUB", "name": "Rubber Floor Mats", "price": 99},
    {"code": "RACK-ROOF", "name": "Roof Rack", "price": 299},
    {"code": "BOX-TOOL", "name": "Tool Storage Box", "price": 179},
]

# Utility to calculate price

def calculate_total(cfg: Configuration) -> float:
    base_price = next((v["base_price"] for v in VEHICLES if v["id"] == cfg.vehicle_id), 0)
    color_price = next((c["price"] for c in COLORS if c["code"] == cfg.color_code), 0)
    up_price = next((u["price"] for u in UPHOLSTERIES if u["code"] == cfg.upholstery_code), 0)
    opt_sum = sum(o["price"] for o in FACTORY_OPTIONS if o["code"] in cfg.factory_options)
    acc_sum = sum(a["price"] for a in ACCESSORIES if a["code"] in cfg.accessories)
    return float(base_price + color_price + up_price + opt_sum + acc_sum)

# ----- Read-only catalog endpoints -----

@app.get("/api/catalog/vehicles")
def get_vehicles():
    return VEHICLES

@app.get("/api/catalog/colors")
def get_colors():
    return COLORS

@app.get("/api/catalog/upholsteries")
def get_upholsteries():
    return UPHOLSTERIES

@app.get("/api/catalog/factory-options")
def get_factory_options():
    return FACTORY_OPTIONS

@app.get("/api/catalog/accessories")
def get_accessories():
    return ACCESSORIES

# ----- Offer submission -----

class OfferRequest(BaseModel):
    configuration: Configuration

class OfferResponse(BaseModel):
    offer_id: str
    total_price: float

@app.post("/api/offers", response_model=OfferResponse)
def create_offer(payload: OfferRequest):
    cfg = payload.configuration
    # derive names for vehicle/color/upholstery for convenience if missing
    vehicle = next((v for v in VEHICLES if v["id"] == cfg.vehicle_id), None)
    color = next((c for c in COLORS if c["code"] == cfg.color_code), None)
    upholstery = next((u for u in UPHOLSTERIES if u["code"] == cfg.upholstery_code), None)
    if not vehicle or not color or not upholstery:
        raise HTTPException(status_code=400, detail="Invalid catalog selection")

    cfg.vehicle_name = vehicle["name"]
    cfg.color_name = color["name"]
    cfg.upholstery_name = upholstery["name"]

    total = calculate_total(cfg)
    cfg.total_price = total

    # Persist configuration document
    data = cfg.model_dump()
    try:
        offer_id = create_document("configuration", data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return OfferResponse(offer_id=offer_id, total_price=total)

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

@app.get("/")
def root():
    return {"message": "Configurator API ready"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
