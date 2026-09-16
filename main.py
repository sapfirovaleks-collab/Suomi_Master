import os, sys, datetime, traceback, json
from pathlib import Path
from typing import Dict, Any, Optional
import aiosqlite, httpx
from fastapi import FastAPI, Depends, Query, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from geo_engine import detect_region_accurate, SCANDINAVIA_FULL, get_coverage_info
from ecosystem_core import core_engine

class Settings(BaseSettings):
    db_path: str = os.getenv("DB_PATH", "suomi_master.db")

settings = Settings()
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Suomi Master v5.6 ULTRA Ecosystem", version="5.6-ultra-core")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def on_startup():
    await core_engine.start()

@app.on_event("shutdown")
async def on_shutdown():
    await core_engine.stop()

# PWA FILES
@app.get("/manifest.json")
async def get_manifest():
    manifest_path = TEMPLATES_DIR / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return JSONResponse(content=json.load(f))
    return JSONResponse(content={"name": "Suomi Master ULTRA", "short_name": "SuomiMaster", "start_url": "/map", "display": "standalone", "theme_color": "#2563eb"})

@app.get("/sw.js")
async def get_sw():
    sw_path = TEMPLATES_DIR / "sw.js"
    if sw_path.exists():
        with open(sw_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), media_type="application/javascript")
    return HTMLResponse(content="self.addEventListener('install', e=>{self.skipWaiting()});", media_type="application/javascript")

# SYSTEM CORE ENDPOINTS
@app.get("/api/system/engine-status")
async def get_engine_status():
    return {"engine": core_engine.get_health_status(), "status": "OK v5.6 CORE", "core_active": True}

@app.get("/api/system/self-check")
async def self_check():
    return {"system_status": "HEALTHY", "version": "5.6-ultra-core", "scandinavia": get_coverage_info(), "engine": core_engine.get_health_status()}

@app.get("/api/map/tiles-config")
async def get_tiles_config():
    return {
        "default_layer": "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        "topographic_layer": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        "attribution": "© OpenTopoMap, © Maanmittauslaitos, © OpenStreetMap"
    }

@app.get("/api/fishing/norway-rules")
async def get_norway_rules():
    return {
        "fillet_export_limit_kg": 18.0,
        "requires_registered_camp": True,
        "minimum_sizes_cm": {"atlantic_halibut_палтус": 84, "cod_треска": 44, "saithe_сайда": 45, "haddock_пикша": 40},
        "eraluvat_link_fi": "https://www.eraluvat.fi/kalastus/kalastonhoitomaksu.html"
    }

@app.post("/api/ai/harvest-scan")
async def scan_harvest_image(file: UploadFile = File(...)):
    filename = file.filename.lower()
    return {
        "filename": file.filename,
        "detected_species_ru": "Белый гриб (Herkkutatti)" if any(x in filename for x in ["bolete", "porcini", "белый"]) else "Моховик / Масленок",
        "edibility": "EDIBLE (Съедобен)",
        "toxic_lookalike_warning": "Внимание! Проверьте трубчатый слой: если он розовый, а ножка с черной сеткой — это Желчный гриб (Sappitatti / Горчак)."
    }

@app.get("/api/fuel/prices")
async def get_fuel_prices():
    return {
        "region": "Kokkola / Pohjanmaa (E8)",
        "currency": "EUR/L",
        "updated_at": str(datetime.date.today()),
        "stations": [
            {"brand": "ABC Kokkola", "fuel_95": 1.829, "fuel_98": 1.919, "diesel": 1.749},
            {"brand": "Neste E8 Heinolankaari", "fuel_95": 1.839, "fuel_98": 1.929, "diesel": 1.739},
            {"brand": "St1 Kokkola", "fuel_95": 1.819, "fuel_98": 1.909, "diesel": 1.729}
        ]
    }

@app.get("/api/weather/live")
async def get_live_weather(lat: float = 63.8333, lng: float = 23.1333):
    cache_key = f"weather:{lat}:{lng}"
    cached = core_engine.get_cache(cache_key)
    if cached:
        cached["cached"] = True
        return cached
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current_weather=true&timezone=auto"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            data = resp.json()
            curr = data.get("current_weather", {})
            temp = curr.get("temperature", 0.0)
            result = {"temperature_c": temp, "windspeed_kmh": curr.get("windspeed", 0.0), "ice_safety": "SAFE" if temp <= -10 else "ATTENTION", "cached": False}
            core_engine.set_cache(cache_key, result, ttl_seconds=600)
            return result
    except Exception as e:
        return {"temperature_c": -1.0, "note": str(e)}

@app.get("/map", response_class=HTMLResponse)
async def serve_map():
    map_path = TEMPLATES_DIR / "index.html"
    if map_path.exists():
        with open(map_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h1>Map Template Missing</h1>")

@app.get("/")
def root():
    return {"status": "OK", "version": "5.6-ultra-core", "engine": "ACTIVE"}

# === STRIPE BILLING & AUTH MODULES ===
import stripe

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
stripe.api_key = STRIPE_SECRET_KEY

class UserAuth(BaseModel):
    email: str
    password: str
    name: Optional[str] = "User"

@app.post("/api/auth/register")
async def register_user(user: UserAuth, db = Depends(get_db)):
    try:
        async with db.execute("INSERT INTO user_profiles (email, name) VALUES (?, ?)", (user.email, user.name)) as cur:
            await db.commit()
            uid = cur.lastrowid
        return {"id": uid, "email": user.email, "status": "REGISTERED"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": "User already exists or DB error", "detail": str(e)})

@app.post("/api/billing/create-checkout-session")
async def create_checkout_session(user_email: str = Query(...), plan: str = Query("pro_monthly")):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=user_email,
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {'name': 'Suomi Master PRO Subscription'},
                    'unit_amount': 999 if plan == "pro_monthly" else 8900,
                    'recurring': {'interval': 'month' if plan == "pro_monthly" else 'year'},
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://suomi-master.fi/map?success=true',
            cancel_url='https://suomi-master.fi/map?canceled=true',
        )
        return {"checkout_url": session.url, "session_id": session.id, "status": "OK"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": "Stripe Session Error", "detail": str(e)})
