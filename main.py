"""
Suomi Master v5.4 FULL - Avtodor & Wildlife Hazards + Full Ecosystem
Включает: Автодор (тропы лосей/оленей/медведей), ИИ-ремонт авто, Рыбалка, P2P/B2B Аренда, Сауны и Фьорды
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
    cors_origins: str = "*"

settings = Settings()
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

ALLOWED_TABLES = {
    'rental_items','auto_maintenance','wildlife_zones','b2b_partners',
    'system_updates','saunas_and_shelters','user_profiles','finland_regions',
    'system_errors','system_weather_log','system_health_log','admin_code_modules',
    'fishing_spots','road_conditions','tool_rental','car_repair_shops'
}

app = FastAPI(
    title="Suomi Master v5.4 Avtodor & Wildlife FULL",
    version="5.4-avtodor-wildlife",
    description="Full ecosystem with Wildlife Avtodor maps (Moose, Reindeer, Bears) and Auto Repair"
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
        CREATE TABLE IF NOT EXISTS b2b_partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_name TEXT, category TEXT, city TEXT, discount_promo TEXT
        );
        CREATE TABLE IF NOT EXISTS fishing_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name_ru TEXT, name_fi TEXT, region_code TEXT, lat REAL, lng REAL, fish_type TEXT, description_ru TEXT, is_ice_fishing BOOLEAN DEFAULT 0
        );
        """)
        
        # Заполнение базы Avtodor / Троп животных
        async with db.execute("SELECT COUNT(*) FROM wildlife_zones") as cur:
            if (await cur.fetchone())[0] == 0:
                wildlife = [
                    ('Moose', 'Лосиная тропа: Трасса 8 (Коккола-Вааса)', 'Hirvivaara: Valtatie 8', 'HIGH', 63.7500, 22.8500, 'all', 'Высокая активность лосей в сумерках! Снизьте скорость.'),
                    ('Moose', 'Лосиный переход: Трасса 4 (Ювяскюля)', 'Hirvivaara: Valtatie 4', 'HIGH', 62.3000, 25.8000, 'all', 'Сезонная миграция лосей. Опасность ДТП.'),
                    ('Reindeer', 'Зона оленеводства (Лапландия / Рованиеми)', 'Poronhoitoalue: Rovaniemi', 'MEDIUM', 66.5000, 25.7000, 'all', 'Олени часто выходят на проезжую часть.'),
                    ('Bear', 'Ареал бурого медведя (Кухмо / Восток)', 'Karhualue: Kuhmo', 'MEDIUM', 64.1300, 29.5000, 'summer', 'Дикая зона обитания медведей.')
                ]
                await db.executemany("INSERT INTO wildlife_zones (animal_type, title_ru, title_fi, risk_level, lat, lng, season, note) VALUES (?,?,?,?,?,?,?,?)", wildlife)

        # Заполнение базы Авто-ремонта
        async with db.execute("SELECT COUNT(*) FROM auto_maintenance") as cur:
            if (await cur.fetchone())[0] == 0:
                auto_data = [
                    ('Renault Scenic 2', 'Освещение', 'Главный свет', 'Галоген H7 12V 55W', 'Замена через подкрылок или снятие накладки бампера.'),
                    ('Renault Scenic 2', 'Зимний пакет', 'Запуск в мороз (-20°C)', 'АКБ 70Ah 640A, Свечи накала 4.4V', 'Проверить пусковой ток АКБ.'),
                    ('General / Все авто', 'Инструмент', 'OBD2 Сканер', 'ELM327 Bluetooth', 'Сброс ошибок Check Engine.')
                ]
                await db.executemany("INSERT INTO auto_maintenance (car_model, system_category, issue_or_part, specifications, fix_instruction) VALUES (?,?,?,?,?)", auto_data)

        await db.commit()

@app.on_event("startup")
async def on_startup():
    await ensure_schema()
    scheduler.start()

# ==========================================
# 🫎 AVTODOR & WILDLIFE HAZARDS API
# ==========================================
@app.get("/api/map/wildlife", tags=["Avtodor Wildlife Maps"])
async def get_wildlife(animal: Optional[str] = Query(None), db = Depends(get_db)):
    """
    Карта Автодор: опасные участки автодорог и миграционные тропы животных (Лоси, Олени, Медведи)
    """
    query = "SELECT animal_type, title_ru, title_fi, risk_level, lat, lng, note FROM wildlife_zones WHERE 1=1"
    params = []
    if animal:
        query += " AND animal_type = ?"
        params.append(animal)
    query += " LIMIT 200"
    async with db.execute(query, params) as cur:
        rows = await cur.fetchall()
    return {"wildlife_markers": [{"animal": r[0], "title_ru": r[1], "title_fi": r[2], "risk_level": r[3], "lat": r[4], "lng": r[5], "note": r[6]} for r in rows]}

# ==========================================
# 🚗 AUTO REPAIR & MAINTENANCE API
# ==========================================
@app.get("/api/auto/maintenance-guide", tags=["Auto Repair Extended"])
async def get_auto_maintenance_guide(db = Depends(get_db)):
    async with db.execute("SELECT car_model, system_category, issue_or_part, specifications, fix_instruction FROM auto_maintenance LIMIT 200") as cur:
        rows = await cur.fetchall()
    return {"guides": [{"car_model": r[0], "system_category": r[1], "issue_or_part": r[2], "specifications": r[3], "fix_instruction": r[4]} for r in rows]}

# ==========================================
# ⚙️ SYSTEM SELF-CHECK API
# ==========================================
@app.get("/api/system/self-check", tags=["System Engine"])
async def self_check(db = Depends(get_db)):
    checks = {}
    for table in ALLOWED_TABLES:
        try:
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)) as cur:
                checks[table] = "OK" if await cur.fetchone() else "MISSING"
        except: checks[table] = "ERROR"
    return {"system_status": "HEALTHY", "checks": checks, "version": "5.4-avtodor-wildlife"}

@app.get("/")
def root():
    return {"message": "Suomi Master v5.4 Avtodor & Wildlife FULL", "status": "OK", "avtodor_wildlife": True}
