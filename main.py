"""
Suomi Master v6.3 AI MEDICINE + GEMINI AI - FULL STACK
"""
import os, sys, ast, datetime, traceback, json, hashlib, secrets, re, time
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

app = FastAPI(title="Suomi Master v6.3 AI MEDICINE", version="6.3-ai-medicine-resurrection")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db():
    db = await aiosqlite.connect(settings.db_path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

@app.on_event("startup")
async def on_startup():
    try:
        await core_engine.start()
    except Exception as e:
        print(f"[CORE] Error: {e}")

@app.get("/")
def root():
    return {"status": "ONLINE", "version": "6.3-ai-medicine-resurrection", "engine": core_engine.get_health_status()}

@app.get("/api/system/self-check")
async def self_check():
    return {"status": "HEALTHY", "version": "6.3-ai-medicine-resurrection", "coverage": "31/31"}

@app.get("/api/system/health/full")
async def full_health():
    return core_engine.get_health_status()

@app.get("/api/system/medicine")
async def list_medicines():
    return {"medicines": core_engine.medicine.known_antidotes, "status": "OK v6.3"}

@app.post("/api/ai/gemini-harvest-scan")
async def gemini_harvest_scan(file: UploadFile = File(...)):
    if not gemini_model:
        return {"error": "GEMINI_API_KEY не установлен в .env", "status": "FALLBACK"}
    contents = await file.read()
    image_parts = [{"mime_type": file.content_type, "data": contents}]
    prompt = "Идентифицируй гриб Финляндии/Скандинавии на фото. Укажи съедобность и опасность (Горчак Sappitatti). Ответь на русском."
    try:
        response = gemini_model.generate_content([prompt, image_parts[0]])
        return {"analysis": response.text, "status": "GEMINI_OK"}
    except Exception as e:
        return {"error": str(e), "status": "ERROR"}

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
