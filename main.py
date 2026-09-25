# -*- coding: utf-8 -*-
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# --- SECURITY & CORS HARDENING ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшне заменить на конкретный домен .fi
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

app = FastAPI(
    title="Suomi Master Ecosystem",
    description="Full 9-Layer Outdoor & Service Platform for Finland",
    version="2.1.0"
)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    if os.path.exists("templates/index.html"):
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return f.read()

# --- LEGAL ROUTES ---
@app.get('/terms')
async def get_terms():
    if os.path.exists('templates/terms.html'):
        return FileResponse('templates/terms.html')
    return {"detail": "Terms document not found"}

@app.get('/privacy')
async def get_privacy():
    if os.path.exists('templates/privacy.html'):
        return FileResponse('templates/privacy.html')
    return {"detail": "Privacy document not found"}

# --- GEO LOCATIONS API ---
@app.get('/api/locations')
async def get_locations():
    from geo_engine import get_all_locations
    return {"status": "ok", "count": len(get_all_locations()), "data": get_all_locations()}

# --- GEMINI AI CORE WITH MAXIMUM POWERS ---
from google import genai
from google.genai.types import GenerateContentConfig, HttpOptions, Tool, ToolCodeExecution

class AIQueryRequest(BaseModel):
    prompt: str
    lat: float = 64.0
    lng: float = 26.0

@app.post('/api/ai-calc')
async def ai_calculator(req: AIQueryRequest):
    try:
        client = genai.Client(http_options=HttpOptions(api_version='v1'))
        code_tool = Tool(code_execution=ToolCodeExecution())
        
        system_instruction = (
            "Olet Suomi Master -ekosysteemin tehokas tekoäly-assistentti. "
            "Sinulla on täydet valtuudet ja syvä asiantuntemus kaikissa 9 ekosysteemin osiossa: "
            "1. Kalastus ja syvyyskartat. "
            "2. Rantasaunat, puusaunat ja avannot. "
            "3. Laavut, autiotuvat ja nuotiopaikat. "
            "4. Lappi, Joulupukin kylä ja Napapiiri. "
            "5. Husky- ja porosafarit sekä moottorikelkat. "
            "6. Majoitus ja mökkivuokraus. "
            "7. Autoilu, matkailuautot, huolto, varaosat ja tiepalvelu. "
            "8. Metsät, marjastus (hilla, mustikka) ja sienestys (mohovikit, kantarellit). "
            "9. TYÖKALUJEN JA VARUSTEIDEN VUOKRAUS: Akkukoneet, polttomoottorikairat, kaikuluotaimet, generaattorit, lumikengät ja trailerit. "
        )
        
        full_prompt = f"{system_instruction}
Käyttäjän sijainti: lat={req.lat}, lng={req.lng}
Kysymys: {req.prompt}"
        
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=full_prompt,
            config=GenerateContentConfig(
                tools=[code_tool],
                temperature=0.1,
            )
        )
        
        return {
            'status': 'ok',
            'answer': response.text,
            'executed_code': response.executable_code,
            'result': response.code_execution_result
        }
    except Exception as e:
        return {'status': 'error', 'detail': str(e)}

@app.get('/about')
async def get_about():
    from fastapi.responses import FileResponse
    return FileResponse('templates/about.html')


# --- B2B LISTING PRICING CONFIG ---
# --- B2B & C2C LISTING PRICING CONFIG (UPDATED HIGH-MARGIN RATES) ---
LISTING_PRICING = {
    "c2c_single": {
        "name": "Yksityishenkilö (1 ilmoitus)",
        "price_eur": 3.90,
        "period": "30 päivää",
        "description": "Yksittäisen työkalun, veneen, mökin tai varusteen vuokrausilmoitus."
    },
    "c2c_boost": {
        "name": "Yksityishenkilö VIP / Nosto",
        "price_eur": 6.90,
        "period": "14 päivää",
        "description": "Nosto kartan kärkeen, VIP-kuvake + AI-suositukset."
    },
    "b2b_basic": {
        "name": "Yritys Perus (Mökit, Saunat, Huolto)",
        "price_eur": 14.90,
        "period": "kuukausi",
        "description": "Suorat yhteystiedot, kotisivulinkit ja paikka kartalla."
    },
    "b2b_pro": {
        "name": "Yritys Pro + AI Suositukset",
        "price_eur": 29.90,
        "period": "kuukausi",
        "description": "Tekoäly suosittelee kohdettasi käyttäjille + VIP-näkyvyys."
    }
}

@app.get('/api/pricing')
async def get_pricing():
    return {"status": "ok", "pricing": LISTING_PRICING}
