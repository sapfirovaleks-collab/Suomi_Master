"""
Suomi Master v6.2 ULTRA PRO MAX SECURE - Full Clean Fix
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

class Settings(BaseSettings):
    db_path: str = os.getenv("DB_PATH", "suomi_master.db")
    admin_token: str = os.getenv("ADMIN_TOKEN", "SuomiMaster_Kokkola_2026_ChangeMe!")
    cors_origins: str = "*"
    weather_lat: float = 63.8333
    weather_lng: float = 23.1333
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:8000/map")

settings = Settings()
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

DB_PATH = Path(settings.db_path)
if not DB_PATH.is_absolute():
    DB_PATH = BASE_DIR / DB_PATH
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Suomi Master v6.2 ULTRA PRO MAX SECURE", version="6.2-ultra-pro-max-secure")

async def initialize_database() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL DEFAULT 'User',
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email)"
        )
        await db.commit()

@app.on_event("startup")
async def startup_event():
    await initialize_database()

# SECURITY: CORS & Rate Limit
allowed_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "https://suomi-master.fi,http://localhost:8000").split(",") if o.strip()]
allow_credentials_flag = False if "*" in allowed_origins else True
if "*" in allowed_origins:
    allowed_origins = ["*"]
    allow_credentials_flag = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials_flag,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Token"]
)

security = HTTPBearer(auto_error=False)
rate_limit_store: Dict[str, list] = defaultdict(list)
RATE_LIMIT = int(os.getenv("RATE_LIMIT_RPS", "20"))

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = rate_limit_store[ip]
    window[:] = [t for t in window if now - t < 60]
    if len(window) >= RATE_LIMIT * 3:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded - 60 req/min"})
    window.append(now)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# DATABASE DEPENDENCY FIRST
async def get_db():
    await initialize_database()
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${h}"

def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split("$", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == h
    except:
        return False

def sanitize_input(text: str, max_len: int = 500) -> str:
    if not text:
        return text
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE|re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    return text[:max_len].strip()

# MODELS
class UserAuth(BaseModel):
    email: str
    password: str
    name: Optional[str] = "User"

class UserRegister(BaseModel):
    email: str = Field(..., max_length=100)
    name: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=100)

# ENDPOINTS
@app.get("/")
def root():
    return {"status": "ONLINE", "version": "6.2-ultra-pro-max-secure"}

@app.get("/api/system/self-check")
async def self_check(db = Depends(get_db)):
    return {"status": "HEALTHY", "version": "6.2-ultra-pro-max-secure"}

@app.post("/api/auth/register")
async def register_user(user: UserRegister, db = Depends(get_db)):
    email = user.email.lower().strip()
    name = sanitize_input(user.name, 100) or "User"
    pwd_hash = hash_password(user.password)
    try:
        async with db.execute(
            "INSERT INTO user_profiles (email, name, password_hash) VALUES (?, ?, ?)",
            (email, name, pwd_hash),
        ) as cur:
            await db.commit()
            uid = cur.lastrowid
        return {"id": uid, "email": email, "status": "REGISTERED"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": "Registration failed", "detail": str(e)})

@app.get("/map", response_class=HTMLResponse)
async def serve_map():
    map_path = TEMPLATES_DIR / "index.html"
    if map_path.exists():
        with open(map_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>PWA Map UI - Ready</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
