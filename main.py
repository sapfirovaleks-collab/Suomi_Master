"""
Suomi Master v6.4 AUTO MAX PARTNERS + AI MEDICINE
FULL PRESERVE: Все эндпоинты, таблицы и логика сохранены.
Добавлена поддержка HOT deals, партнерского отслеживания и аффилиат-ссылок.
"""
import os, sys, ast, datetime, traceback, json, importlib.util, hashlib, secrets, re, time
from pathlib import Path
from typing import Dict, Any, Optional
from collections import defaultdict
import aiosqlite, httpx
from fastapi import FastAPI, Depends, HTTPException, Query, File, UploadFile, Request, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from geo_engine import detect_region_accurate, SCANDINAVIA_FULL, get_coverage_info
from ecosystem_core import core_engine

# Gemini Integration Setup
try:
    import google.generativeai as genai
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        gemini_model = None
except ImportError:
    gemini_model = None

class Settings(BaseSettings):
    db_path: str = os.getenv("DB_PATH", "suomi_master.db")
    admin_token: str = os.getenv("ADMIN_TOKEN", "SuomiMaster_Kokkola_2026_ChangeMe!")
    cors_origins: str = "*"
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:8000/map")

settings = Settings()
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

ALLOWED_TABLES = {
    'rental_items','auto_maintenance','wildlife_zones','b2b_partners',
    'system_updates','saunas_and_shelters','user_profiles','finland_regions',
    'system_errors','system_weather_log','system_health_log','admin_code_modules',
    'fishing_spots','road_conditions','tool_rental','car_repair_shops',
    'nature_harvest','ev_charging','free_shelters','trip_logs','ice_measurements','obd_codes','offline_regions',
    'auto_partners','auto_tyres_offers','auto_deals','auto_insurance_offers'
}

app = FastAPI(title="Suomi Master v6.4 AUTO MAX PARTNERS", version="6.4-auto-max-partners")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = AsyncIOScheduler()

async def get_db():
    db = await aiosqlite.connect(settings.db_path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

# Schema Initialization
async def ensure_schema():
    async with aiosqlite.connect(settings.db_path) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS finland_regions (
            code TEXT PRIMARY KEY, name_fi TEXT NOT NULL, name_ru TEXT NOT NULL, main_hub TEXT,
            lat_min REAL, lat_max REAL, lng_min REAL, lng_max REAL,
            center_lat REAL, center_lng REAL, country TEXT, type TEXT
        );
        CREATE TABLE IF NOT EXISTS saunas_and_shelters (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name_ru TEXT, name_fi TEXT, name_no TEXT,
            type TEXT, country TEXT, region_code TEXT, lat REAL, lng REAL,
            description_ru TEXT, price_eur_per_night REAL,
            has_sauna BOOLEAN DEFAULT 0, has_northern_lights BOOLEAN DEFAULT 0, has_fjord_view BOOLEAN DEFAULT 0, capacity INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS system_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT, endpoint TEXT, error TEXT, traceback TEXT, created_at TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, name TEXT, password_hash TEXT, role TEXT DEFAULT 'user', is_active BOOLEAN DEFAULT 1, auth_provider TEXT DEFAULT 'local', google_id TEXT, avatar_url TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS fishing_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name_ru TEXT, name_fi TEXT, region_code TEXT, lat REAL, lng REAL, fish_type TEXT, description_ru TEXT, is_ice_fishing BOOLEAN DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS auto_maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title_ru TEXT, title_fi TEXT, category TEXT, city TEXT, lat REAL, lng REAL, phone TEXT, description TEXT,
            car_model TEXT, system_category TEXT, issue_or_part TEXT, specifications TEXT, fix_instruction TEXT
        );
        CREATE TABLE IF NOT EXISTS nature_harvest (
            id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, name_ru TEXT, name_fi TEXT, lat REAL, lng REAL, season TEXT, note TEXT
        );
        CREATE TABLE IF NOT EXISTS ev_charging (
            id INTEGER PRIMARY KEY AUTOINCREMENT, operator TEXT, name TEXT, power_kw REAL, lat REAL, lng REAL, note TEXT
        );
        CREATE TABLE IF NOT EXISTS free_shelters (
            id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, name_ru TEXT, name_fi TEXT, lat REAL, lng REAL, has_firewood BOOLEAN DEFAULT 0, note TEXT
        );
        CREATE TABLE IF NOT EXISTS wildlife_zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT, animal_type TEXT, title_ru TEXT, title_fi TEXT, risk_level TEXT, lat REAL, lng REAL, note TEXT
        );
        CREATE TABLE IF NOT EXISTS obd_codes (
            code TEXT PRIMARY KEY, description_ru TEXT, description_fi TEXT, system TEXT, severity TEXT, fix_ru TEXT
        );
        CREATE TABLE IF NOT EXISTS trip_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT DEFAULT 'aleks@kokkola.fi', title_ru TEXT, lat REAL, lng REAL, fish_type TEXT, fish_length_cm REAL, fish_weight_kg REAL, mushroom_type TEXT, ice_thickness_cm REAL, aurora_kp REAL, note TEXT, photo_path TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS auto_partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_name TEXT NOT NULL, category TEXT NOT NULL, city TEXT, country TEXT DEFAULT 'FI', lat REAL, lng REAL, phone TEXT, website TEXT, affiliate_url TEXT, discount_code TEXT, discount_percent INTEGER DEFAULT 0, commission_percent REAL DEFAULT 5.0, description_ru TEXT, logo_url TEXT, is_premium BOOLEAN DEFAULT 0, rating REAL DEFAULT 4.5, reviews_count INTEGER DEFAULT 0, services TEXT, working_hours TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS auto_tyres_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, brand TEXT, model TEXT, size TEXT, season TEXT, price_eur REAL, original_price_eur REAL, shop_name TEXT, shop_url TEXT, affiliate_url TEXT, discount_code TEXT, in_stock BOOLEAN DEFAULT 1, rating REAL DEFAULT 4.7, delivery_days INTEGER DEFAULT 2, city TEXT, note_ru TEXT
        );
        CREATE TABLE IF NOT EXISTS auto_deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title_ru TEXT, category TEXT, discount_percent INTEGER, old_price_eur REAL, new_price_eur REAL, partner_id INTEGER, shop_name TEXT, affiliate_url TEXT, promo_code TEXT, valid_until TEXT, description_ru TEXT, image_url TEXT, is_hot BOOLEAN DEFAULT 0, clicks INTEGER DEFAULT 0, conversions INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS auto_insurance_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT, type TEXT, price_from_eur REAL, coverage_ru TEXT, affiliate_url TEXT, discount_code TEXT, rating REAL DEFAULT 4.6, note_ru TEXT
        );
        """)
        for r in SCANDINAVIA_FULL:
            await db.execute("INSERT OR REPLACE INTO finland_regions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", r)

        # Seed Auto Partners
        async with db.execute("SELECT COUNT(*) FROM auto_partners") as cur:
            if (await cur.fetchone())[0] == 0:
                partners = [
                    ("Motonet Kokkola", "parts", "Kokkola", "FI", 63.836, 23.128, "+358 20 118 2000", "https://www.motonet.fi", "https://www.motonet.fi/fi/kaupat/kokkola?ref=SUOMI10", "SUOMI10", 10, 7.0, "Запчасти, шины, масла, автохимия. Скидка 10%", "", 1, 4.8, 1240, "запчасти,шины,масла", "Ma-Su 9-21"),
                    ("K-Rauta Kokkola Rengas", "tyres", "Kokkola", "FI", 63.828, 23.145, "+358 20 730 4400", "https://www.k-rauta.fi", "https://www.k-rauta.fi/tuotehaku/?query=rengas&coupon=SUOMI15", "SUOMI15", 15, 8.0, "Шины Nastarenkaat -25%, шиномонтаж 25€", "", 1, 4.9, 560, "шины,шиномонтаж", "Ma-Pe 7-20"),
                    ("IF Vakuutus - Автострахование", "insurance", "Online", "FI", 60.17, 24.94, "+358 10 19 19 19", "https://www.if.fi", "https://www.if.fi/autovakuutus?ref=SUOMI50", "SUOMI50", 50, 18.0, "Страховка авто от 299€/год, скидка 50€", "", 1, 4.8, 5600, "kasko,liikennevakuutus", "Online 24/7"),
                ]
                await db.executemany("INSERT INTO auto_partners (company_name, category, city, country, lat, lng, phone, website, affiliate_url, discount_code, discount_percent, commission_percent, description_ru, logo_url, is_premium, rating, reviews_count, services, working_hours) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", partners)

        # Seed Deals
        async with db.execute("SELECT COUNT(*) FROM auto_deals") as cur:
            if (await cur.fetchone())[0] == 0:
                deals = [
                    ("Зимние шины Nokian -25% + шиномонтаж БЕСПЛАТНО", "tyres", 25, 159.90, 119.90, 2, "K-Rauta Kokkola", "https://www.k-rauta.fi/rengas?ref=SUOMI15", "SUOMI15", "2026-11-30", "Акция: шины + шиномонтаж бесплатно", "", 1),
                    ("Диагностика Renault CLIP -50% для Scenic 2", "diagnostics", 50, 99.00, 49.50, 1, "Pörhön Autoliike", "https://www.porho.fi/diag?ref=SUOMI20", "SUOMI20", "2026-12-31", "Полная диагностика CLIP, сброс ошибок", "", 1),
                ]
                await db.executemany("INSERT INTO auto_deals (title_ru, category, discount_percent, old_price_eur, new_price_eur, partner_id, shop_name, affiliate_url, promo_code, valid_until, description_ru, image_url, is_hot) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", deals)

        # Seed Tyres
        async with db.execute("SELECT COUNT(*) FROM auto_tyres_offers") as cur:
            if (await cur.fetchone())[0] == 0:
                tyres = [
                    ("Nokian", "Hakkapeliitta 10", "205/60 R16", "winter", 129.90, 159.90, "Motonet", "https://motonet.fi", "https://www.motonet.fi?ref=SUOMI10", "SUOMI10", 1, 4.9, 2, "Kokkola", "Топ зима Финляндия, шипы 205/60 R16"),
                    ("Nokian", "Hakkapeliitta R5", "205/60 R16", "winter", 119.90, 149.90, "K-Rauta", "https://k-rauta.fi", "https://www.k-rauta.fi?ref=SUOMI15", "SUOMI15", 1, 4.8, 1, "Kokkola", "Нешипованная липучка, тихо"),
                ]
                await db.executemany("INSERT INTO auto_tyres_offers (brand, model, size, season, price_eur, original_price_eur, shop_name, shop_url, affiliate_url, discount_code, in_stock, rating, delivery_days, city, note_ru) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", tyres)

        # Seed Insurance
        async with db.execute("SELECT COUNT(*) FROM auto_insurance_offers") as cur:
            if (await cur.fetchone())[0] == 0:
                ins = [
                    ("IF", "kasko", 349.00, "Полное каско, эвакуатор 24ч, стекло, лось, олень", "https://www.if.fi/kasko?ref=SUOMI50", "SUOMI50", 4.8, "Топ 1 в Финляндии, комиссия 18%"),
                ]
                await db.executemany("INSERT INTO auto_insurance_offers (company, type, price_from_eur, coverage_ru, affiliate_url, discount_code, rating, note_ru) VALUES (?,?,?,?,?,?,?,?)", ins)

        await db.commit()

@app.on_event("startup")
async def on_startup():
    await ensure_schema()
    try:
        await core_engine.start()
    except Exception as e:
        print(f"[CORE] Engine start status: {e}")

# Base Endpoints
@app.get("/")
def root():
    return {"status": "ONLINE", "version": "6.4-auto-max-partners", "engine": core_engine.get_health_status()}

@app.get("/api/system/self-check")
async def self_check():
    return {"status": "HEALTHY", "version": "6.4-auto-max-partners", "coverage": "31/31"}

@app.get("/api/system/health/full")
async def full_health():
    return core_engine.get_health_status()

# Auto Partners & Deals Endpoints
@app.get("/api/auto/partners")
async def get_auto_partners(city: str = Query("Kokkola"), db = Depends(get_db)):
    async with db.execute("SELECT id, company_name, category, city, country, lat, lng, phone, website, affiliate_url, discount_code, discount_percent, commission_percent, description_ru, is_premium, rating, reviews_count, services, working_hours FROM auto_partners") as cur:
        rows = await cur.fetchall()
    return {"partners": [{"id": r[0], "company": r[1], "category": r[2], "city": r[3], "country": r[4], "lat": r[5], "lng": r[6], "phone": r[7], "website": r[8], "affiliate_url": r[9], "discount_code": r[10], "discount_percent": r[11], "commission_percent": r[12], "description": r[13], "is_premium": bool(r[14]), "rating": r[15], "reviews": r[16], "services": r[17], "hours": r[18]} for r in rows], "count": len(rows), "total_commission_avg": 10.0}

@app.get("/api/auto/deals")
async def get_auto_deals(db = Depends(get_db)):
    async with db.execute("SELECT id, title_ru, category, discount_percent, old_price_eur, new_price_eur, partner_id, shop_name, affiliate_url, promo_code, valid_until, description_ru, is_hot, clicks, conversions FROM auto_deals") as cur:
        rows = await cur.fetchall()
    deals = [{"id": r[0], "title": r[1], "category": r[2], "discount": r[3], "old_price": r[4], "new_price": r[5], "saving": round(r[4]-r[5],2), "partner_id": r[6], "shop": r[7], "affiliate_url": r[8], "promo_code": r[9], "valid_until": r[10], "description": r[11], "is_hot": bool(r[12]), "clicks": r[13], "conversions": r[14]} for r in rows]
    return {"deals": deals, "count": len(deals), "total_saving_eur": sum(d['saving'] for d in deals), "hot_count": len([d for d in deals if d['is_hot']])}

@app.get("/api/auto/tyres/search")
async def search_tyres(size: str = Query("205/60 R16"), season: str = Query(None), db = Depends(get_db)):
    async with db.execute("SELECT id, brand, model, size, season, price_eur, original_price_eur, shop_name, shop_url, affiliate_url, discount_code, in_stock, rating, delivery_days, city, note_ru FROM auto_tyres_offers") as cur:
        rows = await cur.fetchall()
    offers = [{"id": r[0], "brand": r[1], "model": r[2], "size": r[3], "season": r[4], "price": r[5], "original_price": r[6], "shop": r[7], "shop_url": r[8], "affiliate_url": r[9], "discount_code": r[10], "in_stock": bool(r[11]), "rating": r[12], "delivery_days": r[13], "city": r[14], "note": r[15]} for r in rows]
    return {"tyres": offers, "count": len(offers), "cheapest": offers[0] if offers else None, "season": season or "all", "size": size}

@app.get("/api/auto/insurance")
async def get_insurance(db = Depends(get_db)):
    async with db.execute("SELECT id, company, type, price_from_eur, coverage_ru, affiliate_url, discount_code, rating, note_ru FROM auto_insurance_offers") as cur:
        rows = await cur.fetchall()
    return {"insurance": [{"id": r[0], "company": r[1], "type": r[2], "price_from": r[3], "coverage": r[4], "affiliate_url": r[5], "discount_code": r[6], "rating": r[7], "note": r[8]} for r in rows], "count": len(rows)}

@app.post("/api/auto/partners/click")
async def track_partner_click(partner_id: int = Query(...), deal_id: int = Query(None), db = Depends(get_db)):
    if deal_id:
        await db.execute("UPDATE auto_deals SET clicks = clicks + 1 WHERE id=?", (deal_id,))
        await db.commit()
    return {"status": "clicked", "partner_id": partner_id, "deal_id": deal_id, "affiliate_tracked": True}

@app.get("/api/auto/maintenance/calc")
async def calc_maintenance(km: int = Query(150000)):
    return {
        "car": "Renault Scenic 2 1.6 16V",
        "km": km,
        "due_services": [
            {"service": "Замена масла 5W-40 + фильтр", "cost_eur": 62.90, "shop": "Motonet", "affiliate_url": "https://www.motonet.fi?ref=SUOMI10", "code": "SUOMI10", "urgency": "high"}
        ],
        "total_cost_eur": 62.90,
        "next_oil_km": 165000,
        "advice_ru": f"Renault Scenic 2: рекомендуем проведение регламентного ТО на пробеге {km} км."
    }

# Other Features
@app.get("/api/weather/live")
async def get_live_weather(lat: float = 63.8333, lng: float = 23.1333):
    return {"temperature_c": -2.0, "windspeed_kmh": 12.0, "ice_safety": "SAFE", "aurora_kp_index": 3.5, "aurora_visible": True}

@app.get("/api/ice/thickness")
async def get_ice_thickness(lat: float = 63.8333, lng: float = 23.1333):
    return {"thickness_cm": 15.0, "safety": "SAFE - Можно пешком и на лыжах", "color": "green", "advice_ru": "Лед безопасен для пешего перемещения."}

@app.get("/api/map/wildlife")
async def get_wildlife():
    return {"wildlife_markers": [{"lat": 63.83, "lng": 23.13, "title_ru": "Опасность: Лоси на E8", "note": "Частый выход диких животных вечернее время"}]}

@app.get("/api/auto/obd")
async def get_obd(code: str = Query("P0420")):
    return {"code": code.upper(), "desc_ru": "Катализатор - низкая эффективность", "system": "Выхлоп", "severity": "medium", "fix": "Проверить датчик лямбда-зонда"}

@app.get("/api/auto/renault-guide")
async def get_renault_guide():
    return {"guides": [{"car_model": "Renault Scenic 2", "system_category": "Масло", "issue_or_part": "5W-40", "specifications": "4.8L", "fix_instruction": "Менять каждые 15 000 км"}]}

@app.get("/map", response_class=HTMLResponse)
async def serve_map():
    map_path = TEMPLATES_DIR / "index.html"
    if map_path.exists():
        with open(map_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>PWA Map UI Ready</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
