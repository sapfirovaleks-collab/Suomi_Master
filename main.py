import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI(title="Suomi Master Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    import ecosystem_core
    if hasattr(ecosystem_core, "router"):
        app.include_router(ecosystem_core.router)
except Exception:
    pass

try:
    import geo_engine
    if hasattr(geo_engine, "router"):
        app.include_router(geo_engine.router)
    elif hasattr(geo_engine, "geo_router"):
        app.include_router(geo_engine.geo_router)
except Exception:
    pass

@app.get("/api/auto/partners")
@app.get("/partners")
async def get_partners():
    return [{"id": 1, "title": "Auto Max Partners", "name": "Auto Max Partners", "rating": "6.4", "car": "Renault Scenic 2 1.6 16V", "services": "Партнеры Коккола, шины, страховка, ТО", "discount": "15%"}]

@app.get("/api/auto/deals")
@app.get("/deals")
async def get_deals():
    return [{"id": 1, "title": "HOT Deals Kokkola", "discount": "20%", "price": "50€", "link": "#"}]

@app.get("/api/auto/insurance")
@app.get("/insurance")
async def get_insurance():
    return [{"id": 1, "title": "Страховка авто", "provider": "Liikennevakuutus", "price": "120€", "link": "#"}]

for folder in ["static", "public", "dist", "frontend", "assets"]:
    if os.path.exists(folder):
        try:
            app.mount(f"/{folder}", StaticFiles(directory=folder), name=folder)
        except Exception:
            pass

@app.get("/")
async def serve_index():
    for p in ["index.html", "static/index.html", "public/index.html", "dist/index.html", "frontend/index.html"]:
        if os.path.exists(p):
            return FileResponse(p)
    return JSONResponse(status_code=200, content={"status": "online", "engine": "Google Cloud Run Autonomous Core"})
