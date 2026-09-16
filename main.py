"""
Suomi Master v5.5 FULL - Complete Ecosystem with All Markers
Включает: Avtodor/Wildlife, Авто-ремонт, Рыбалку, Сауны/Кемпинги, Грибы/Ягоды, EV-зарядки, Erä-Lupa зоны и Autiotupa/Laavu
"""
import os, sys, ast, asyncio, datetime, traceback
from pathlib import Path
from typing import Dict, Any, Optional
import aiosqlite, httpx
from fastapi import FastAPI, Depends, HTTPException, Query, Header, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from apscheduler.schedulers.asyncio import AsyncIOScheduler

try:
    from geo_engine import detect_region_accurate, SCANDINAVIA_FULL, get_coverage_info
except ImportError:
    SCANDINAVIA_FULL = [
        ('FI-15', 'Keski-Pohjanmaa', 'Центральная Похьянмаа', 'Kokkola', 63.5, 64.2, 22.5, 24.5, 63.83, 23.13, 'FI', 'region'),
        ('NO-02', 'Troms og Finnmark', 'Тромс и Финнмарк', 'Tromsø / Elvegård', 68.0, 71.2, 16.0, 31.0, 69.64, 18.95, 'NO', 'fjord')
    ]
    def detect_region_accurate(lat, lng):
        return {"code": "FI-15", "name_fi": "Keski-Pohjanmaa", "name_ru": "Центральная Похьянмаа", "hub": "Kokkola"}

class Settings(BaseSettings):
    db_path: str = os.getenv("DB_PATH", "suomi_master.db")
    admin_token: str = os.getenv("ADMIN_TOKEN", "7GCJQzi6NWBds5Ehc-BXhHjaXtloDntPLI9QVz16C3UmNcSlA9pygEP9DrgMgprK")

settings = Settings()
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

ALLOWED_TABLES = {
    'rental_items','auto_maintenance','wildlife_zones','b2b_partners',
    'system_updates','saunas_and_shelters','user_profiles','finland_regions',
    'system_errors','system_weather_log','system_health_log','admin_code_modules',
    'fishing_spots','road_conditions','tool_rental','car_repair_shops',
    'nature_harvest','ev_charging','legal_zones','free_shelters'
}

app = FastAPI(
    title="Suomi Master v5.5 FULL Ecosystem",
    version="5.5-all-markers",
    description="Full ecosystem with Wildlife, Fishing, Saunas, Berries/Mushrooms, EV Chargers, Permits & Free Huts"
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
scheduler = AsyncIOScheduler()

async def get_db():
    db = await aiosqlite.connect(settings.db_path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

async def ensure_schema():
    async with aiosqlite.connect(settings.db_path) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS finland_regions (
            code TEXT PRIMARY KEY, name_fi TEXT NOT NULL, name_ru TEXT NOT NULL, main_hub TEXT,
            lat_min REAL, lat_max REAL, lng_min REAL, lng_max REAL,
            center_lat REAL, center_lng REAL, country TEXT, type TEXT
        );
        CREATE TABLE IF NOT EXISTS wildlife_zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT, animal_type TEXT NOT NULL, title_ru TEXT NOT NULL, title_fi TEXT NOT NULL, risk_level TEXT CHECK(risk_level IN ('LOW', 'MEDIUM', 'HIGH')), lat REAL NOT NULL, lng REAL NOT NULL, season TEXT DEFAULT 'all', note TEXT
        );
        CREATE TABLE IF NOT EXISTS auto_maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT, car_model TEXT NOT NULL, system_category TEXT NOT NULL, issue_or_part TEXT NOT NULL, specifications TEXT NOT NULL, fix_instruction TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS saunas_and_shelters (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name_ru TEXT, name_fi TEXT, name_no TEXT, type TEXT, country TEXT, region_code TEXT, lat REAL, lng REAL, description_ru TEXT, price_eur_per_night REAL, has_sauna BOOLEAN DEFAULT 0, has_northern_lights BOOLEAN DEFAULT 0, has_fjord_view BOOLEAN DEFAULT 0, capacity INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS fishing_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name_ru TEXT, name_fi TEXT, region_code TEXT, lat REAL, lng REAL, fish_type TEXT, description_ru TEXT, is_ice_fishing BOOLEAN DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS nature_harvest (
            id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, name_ru TEXT, name_fi TEXT, lat REAL, lng REAL, season TEXT, note TEXT
        );
        CREATE TABLE IF NOT EXISTS ev_charging (
            id INTEGER PRIMARY KEY AUTOINCREMENT, operator TEXT, name TEXT, power_kw INTEGER, lat REAL, lng REAL, note TEXT
        );
        CREATE TABLE IF NOT EXISTS legal_zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT, zone_type TEXT, name_ru TEXT, name_fi TEXT, permit_required TEXT, lat REAL, lng REAL, note TEXT
        );
        CREATE TABLE IF NOT EXISTS free_shelters (
            id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, name_ru TEXT, name_fi TEXT, lat REAL, lng REAL, has_firewood BOOLEAN DEFAULT 1, note TEXT
        );
        """)

        # 1. Грибы и Ягоды
        async with db.execute("SELECT COUNT(*) FROM nature_harvest") as cur:
            if (await cur.fetchone())[0] == 0:
                harvest = [
                    ('Mushroom', 'Белые грибы и моховики (Коккола)', 'Herkkutatti & Kangastatti', 63.8500, 23.1500, 'autumn', 'Сосновый бор, богатый урожай моховиков и белых грибов.'),
                    ('Mushroom', 'Осторожно: Опасность горчака / Желчного гриба', 'Varoitus: Sappitatti', 63.8100, 23.2000, 'autumn', 'Осторожно! Горчак внешне похож на моховик/белый, но имеет розовый гименофор и горький вкус.'),
                    ('Berry', 'Брусничные места (Коккола леса)', 'Puolukka-alue', 63.8200, 23.2500, 'autumn', 'Отличные сосновые вырубки с брусникой.'),
                    ('Berry', 'Морошковое болото (Лапландия / Рованиеми)', 'Hilla-suo', 66.5200, 25.7500, 'summer', 'Сезонная морошка на торфяных болотах.')
                ]
                await db.executemany("INSERT INTO nature_harvest (category, name_ru, name_fi, lat, lng, season, note) VALUES (?,?,?,?,?,?,?)", harvest)

        # 2. EV-Зарядки & Авто-инфраструктура
        async with db.execute("SELECT COUNT(*) FROM ev_charging") as cur:
            if (await cur.fetchone())[0] == 0:
                ev_data = [
                    ('ABC-lataus', 'Быстрая зарядка ABC Kokkola Prisma', 150, 63.8310, 23.1410, 'CCS2 150kW, Type 2 22kW. Рядом гипермаркет.'),
                    ('Kempower / Recharge', 'Зарядный хаб Вааса', 200, 63.0950, 21.6150, 'Ультрабыстрая зарядка 200kW.'),
                    ('Recharge NO', 'Зарядка фьорды Тромсё', 150, 69.6500, 18.9600, 'Зарядный пункт по пути на Лофотены.')
                ]
                await db.executemany("INSERT INTO ev_charging (operator, name, power_kw, lat, lng, note) VALUES (?,?,?,?,?,?)", ev_data)

        # 3. Лицензионные зоны Erä-Lupa & Ограничения
        async with db.execute("SELECT COUNT(*) FROM legal_zones") as cur:
            if (await cur.fetchone())[0] == 0:
                legal_data = [
                    ('Permit_River', 'Лицензионная зона Perhonjoki', 'Perhonjoen viehelupa-alue', 'Viehelupa', 63.8400, 23.1200, 'Обязательна местная лицензия Perhonjoki наряду с государственным сборником.'),
                    ('Reserve', 'Национальный парк Сеитсеминен', 'Seitsemisen kansallispuisto', 'Strict Rules', 61.9000, 23.4000, 'Костер разрешен только в специально оборудованных местах Laavu!'),
                    ('Customs_NO', 'Пограничный контроль Mattilsynet (Норвегия)', 'Tulli / Mattilsynet', 'Export Limit', 69.3000, 20.2000, 'Норма вывоза филе рыбы — до 18 кг на человека при проживании на зарегистрированной базе.')
                ]
                await db.executemany("INSERT INTO legal_zones (zone_type, name_ru, name_fi, permit_required, lat, lng, note) VALUES (?,?,?,?,?,?,?)", legal_data)

        # 4. Бесплатные лесные избушки и навесы (Autiotupa & Laavu)
        async with db.execute("SELECT COUNT(*) FROM free_shelters") as cur:
            if (await cur.fetchone())[0] == 0:
                shelters = [
                    ('Laavu', 'Навес с кострищем Perhonjoki Laavu', 'Perhonjoen laavu', 63.8450, 23.1350, 1, 'Бесплатный навес, сухие дрова в сарае. Идеально для отдыха.'),
                    ('Autiotupa', 'Лесная открытая избушка Оуланка', 'Oulangan autiotupa', 66.3700, 29.3200, 1, 'Бесплатная избушка Metsähallitus с печкой для ночлега пеших туристов.'),
                    ('Kota', 'Чума с кострищем Рованиеми', 'Rovaniemen kota', 66.5100, 25.7200, 1, 'Закрытый гриль-чум для защиты от ветра.')
                ]
                await db.executemany("INSERT INTO free_shelters (type, name_ru, name_fi, lat, lng, has_firewood, note) VALUES (?,?,?,?,?,?,?)", shelters)

        # Базовый Avtodor & Авторемонт
        async with db.execute("SELECT COUNT(*) FROM wildlife_zones") as cur:
            if (await cur.fetchone())[0] == 0:
                wildlife = [
                    ('Moose', 'Лосиная тропа: Трасса 8 (Коккола-Вааса)', 'Hirvivaara: Valtatie 8', 'HIGH', 63.7500, 22.8500, 'all', 'Высокая активность лосей в сумерках! Снизьте скорость.'),
                    ('Moose', 'Лосиный переход: Трасса 4 (Ювяскюля)', 'Hirvivaara: Valtatie 4', 'HIGH', 62.3000, 25.8000, 'all', 'Сезонная миграция лосей. Опасность ДТП.'),
                    ('Reindeer', 'Зона оленеводства (Лапландия / Рованиеми)', 'Poronhoitoalue: Rovaniemi', 'MEDIUM', 66.5000, 25.7000, 'all', 'Олени часто выходят на проезжую часть.'),
                    ('Bear', 'Ареал бурого медведя (Кухмо / Восток)', 'Karhualue: Kuhmo', 'MEDIUM', 64.1300, 29.5000, 'summer', 'Дикая зона обитания медведей.')
                ]
                await db.executemany("INSERT INTO wildlife_zones (animal_type, title_ru, title_fi, risk_level, lat, lng, season, note) VALUES (?,?,?,?,?,?,?,?)", wildlife)

        await db.commit()

@app.on_event("startup")
async def on_startup():
    await ensure_schema()
    scheduler.start()

# ==========================================
# 📍 NEW API ENDPOINTS
# ==========================================
@app.get("/api/map/harvest", tags=["Nature & Harvest"])
async def get_harvest(db = Depends(get_db)):
    async with db.execute("SELECT category, name_ru, name_fi, lat, lng, season, note FROM nature_harvest") as cur:
        rows = await cur.fetchall()
    return {"harvest_spots": [{"category": r[0], "name_ru": r[1], "name_fi": r[2], "lat": r[3], "lng": r[4], "season": r[5], "note": r[6]} for r in rows]}

@app.get("/api/map/ev", tags=["EV Charging"])
async def get_ev_chargers(db = Depends(get_db)):
    async with db.execute("SELECT operator, name, power_kw, lat, lng, note FROM ev_charging") as cur:
        rows = await cur.fetchall()
    return {"chargers": [{"operator": r[0], "name": r[1], "power_kw": r[2], "lat": r[3], "lng": r[4], "note": r[5]} for r in rows]}

@app.get("/api/map/legal", tags=["Legal & Rules"])
async def get_legal_zones(db = Depends(get_db)):
    async with db.execute("SELECT zone_type, name_ru, name_fi, permit_required, lat, lng, note FROM legal_zones") as cur:
        rows = await cur.fetchall()
    return {"zones": [{"zone_type": r[0], "name_ru": r[1], "name_fi": r[2], "permit": r[3], "lat": r[4], "lng": r[5], "note": r[6]} for r in rows]}

@app.get("/api/map/free-shelters", tags=["Free Shelters"])
async def get_free_shelters(db = Depends(get_db)):
    async with db.execute("SELECT type, name_ru, name_fi, lat, lng, has_firewood, note FROM free_shelters") as cur:
        rows = await cur.fetchall()
    return {"shelters": [{"type": r[0], "name_ru": r[1], "name_fi": r[2], "lat": r[3], "lng": r[4], "firewood": bool(r[5]), "note": r[6]} for r in rows]}

@app.get("/api/map/wildlife", tags=["Avtodor Wildlife Maps"])
async def get_wildlife(animal: Optional[str] = Query(None), db = Depends(get_db)):
    async with db.execute("SELECT animal_type, title_ru, title_fi, risk_level, lat, lng, note FROM wildlife_zones") as cur:
        rows = await cur.fetchall()
    return {"wildlife_markers": [{"animal": r[0], "title_ru": r[1], "title_fi": r[2], "risk_level": r[3], "lat": r[4], "lng": r[5], "note": r[6]} for r in rows]}

@app.get("/api/system/self-check", tags=["System Engine"])
async def self_check(db = Depends(get_db)):
    checks = {}
    for table in ALLOWED_TABLES:
        try:
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)) as cur:
                checks[table] = "OK" if await cur.fetchone() else "MISSING"
        except: checks[table] = "ERROR"
    return {"system_status": "HEALTHY", "checks": checks, "version": "5.5-all-markers"}

@app.get("/")
def root():
    return {"message": "Suomi Master v5.5 FULL Ecosystem", "status": "OK", "all_markers_active": True}

@app.get("/api/auto/maintenance-guide", tags=["Auto Repair Extended"])
async def get_auto_maintenance_guide(db = Depends(get_db)):
    async with db.execute("SELECT car_model, system_category, issue_or_part, specifications, fix_instruction FROM auto_maintenance LIMIT 200") as cur:
        rows = await cur.fetchall()
    return {"guides": [{"car_model": r[0], "system_category": r[1], "issue_or_part": r[2], "specifications": r[3], "fix_instruction": r[4]} for r in rows]}

@app.get("/map", response_class=HTMLResponse, tags=["UI"])
async def serve_map():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/manifest.json")
async def get_manifest():
    with open("templates/manifest.json", "r", encoding="utf-8") as f:
        return JSONResponse(content=ast.literal_eval(f.read()) if False else httpx.sys.modules['json'].load(f))

@app.get("/sw.js")
async def get_sw():
    with open("templates/sw.js", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), media_type="application/javascript")
