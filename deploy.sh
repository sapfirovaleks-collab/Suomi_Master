#!/bin/bash
set -e

echo "=== ПОДГОТОВКА И ПЕРЕНОС В GOOGLE CLOUD ==="

cat << 'PYEOF' > main.py
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
PYEOF

cat << 'DOCKEREOF' > Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir fastapi uvicorn gunicorn requests jinja2
EXPOSE 8080
CMD exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --worker-class uvicorn.workers.UvicornWorker main:app
DOCKEREOF

echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

echo "=== ЗАПУСК АВТОРИЗАЦИИ ==="
gcloud auth login --no-launch-browser

echo "=== НАСТРОЙКА ПРОЕКТА И ДЕПЛОЙ ==="
gcloud config set project suomi-master-app 2>/dev/null || gcloud projects create suomi-master-app --name="Suomi Master"
gcloud config set project suomi-master-app

gcloud services enable artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com
gcloud run deploy suomi-master \
  --source . \
  --region europe-north1 \
  --allow-unauthenticated \
  --port 8080
