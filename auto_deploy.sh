#!/bin/bash
echo "🚀 Перезапуск Uvicorn сервера Suomi Master v5.6..."
pkill -f uvicorn || true
sleep 1

nohup uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
sleep 2

python3 test_and_auto_fix.py
