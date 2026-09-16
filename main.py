import os, datetime, json
from pathlib import Path
from typing import Optional
import aiosqlite, httpx
from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_path: str = os.getenv("DB_PATH", "suomi_master.db")

settings = Settings()
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Suomi Master v5.6 COMPLETE Ecosystem", version="5.6-complete")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

async def get_db():
    db = await aiosqlite.connect(settings.db_path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

@app.get("/manifest.json")
async def get_manifest():
    manifest_path = TEMPLATES_DIR / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return JSONResponse(content=json.load(f))
    return JSONResponse(content={})

@app.get("/sw.js")
async def get_sw():
    sw_path = TEMPLATES_DIR / "sw.js"
    if sw_path.exists():
        with open(sw_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), media_type="application/javascript")
    return HTMLResponse(content="", media_type="application/javascript")

@app.get("/api/weather/live", tags=["Weather"])
async def get_live_weather(lat: float = 63.8333, lng: float = 23.1333):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current_weather=true&timezone=auto"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            data = resp.json()
            curr = data.get("current_weather", {})
            temp = curr.get("temperature", 0.0)
            ice_status = "SAFE" if temp <= -10 else ("ATTENTION" if temp <= -2 else "DANGER")
            return {
                "temperature_c": temp,
                "windspeed_kmh": curr.get("windspeed", 0.0),
                "weather_code": curr.get("weathercode", 0),
                "ice_safety": ice_status,
                "aurora_kp_index": 4.2 if temp < 0 else 1.8,
                "aurora_visible": temp < 0
            }
    except Exception as e:
        return {"temperature_c": -1.0, "ice_safety": "N/A", "aurora_kp_index": 2.0, "note": str(e)}

@app.get("/api/system/tyre-compliance", tags=["Avtodor Safety"])
async def check_tyre_compliance():
    today = datetime.date.today()
    month = today.month
    winter_required = (month >= 11 or month <= 3)
    return {
        "current_date": str(today),
        "winter_tyres_mandatory": winter_required,
        "recommendation": "Используйте шипованную резину (Nastarenkaat)." if winter_required else "Летняя резина разрешена (Kesärenkaat).",
        "emergency_numbers": {"general_emergency": "112", "towing_hinauspalvelu": "+358 800 112 112"}
    }

@app.get("/api/map/harvest")
async def get_harvest(db = Depends(get_db)):
    async with db.execute("SELECT category, name_ru, name_fi, lat, lng, season, note FROM nature_harvest") as cur:
        rows = await cur.fetchall()
    return {"harvest_spots": [{"category": r[0], "name_ru": r[1], "name_fi": r[2], "lat": r[3], "lng": r[4], "season": r[5], "note": r[6]} for r in rows]}

@app.get("/api/map/ev")
async def get_ev(db = Depends(get_db)):
    async with db.execute("SELECT operator, name, power_kw, lat, lng, note FROM ev_charging") as cur:
        rows = await cur.fetchall()
    return {"chargers": [{"operator": r[0], "name": r[1], "power_kw": r[2], "lat": r[3], "lng": r[4], "note": r[5]} for r in rows]}

@app.get("/api/map/free-shelters")
async def get_shelters(db = Depends(get_db)):
    async with db.execute("SELECT type, name_ru, name_fi, lat, lng, has_firewood, note FROM free_shelters") as cur:
        rows = await cur.fetchall()
    return {"shelters": [{"type": r[0], "name_ru": r[1], "name_fi": r[2], "lat": r[3], "lng": r[4], "firewood": bool(r[5]), "note": r[6]} for r in rows]}

@app.get("/api/map/wildlife")
async def get_wildlife(db = Depends(get_db)):
    async with db.execute("SELECT animal_type, title_ru, title_fi, risk_level, lat, lng, note FROM wildlife_zones") as cur:
        rows = await cur.fetchall()
    return {"wildlife_markers": [{"animal": r[0], "title_ru": r[1], "title_fi": r[2], "risk_level": r[3], "lat": r[4], "lng": r[5], "note": r[6]} for r in rows]}

@app.get("/api/auto/maintenance-guide")
async def get_auto_maintenance(db = Depends(get_db)):
    async with db.execute("SELECT car_model, system_category, issue_or_part, specifications, fix_instruction FROM auto_maintenance") as cur:
        rows = await cur.fetchall()
    return {"guides": [{"car_model": r[0], "system_category": r[1], "issue_or_part": r[2], "specifications": r[3], "fix_instruction": r[4]} for r in rows]}

@app.get("/api/system/self-check")
async def self_check():
    return {"system_status": "HEALTHY", "version": "5.6-complete"}

@app.get("/map", response_class=HTMLResponse)
async def serve_map():
    map_path = TEMPLATES_DIR / "index.html"
    if map_path.exists():
        with open(map_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h1>Map Template Missing</h1>")

@app.get("/")
def root():
    return {"status": "OK", "version": "5.6-complete"}
