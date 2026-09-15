#!/bin/bash
echo "🚀 Перезапуск автономного сервера Suomi Master v5.4..."
pkill -f uvicorn || true
sleep 1

source venv/bin/activate 2>/dev/null || source /workspaces/Suomi_Master/venv/bin/activate 2>/dev/null || true

nohup uvicorn main:app --host 127.0.0.1 --port 8000 > server.log 2>&1 &

echo "⏳ Ожидание запуска сервера Uvicorn (5 секунд)..."
sleep 5

if ! pgrep -f uvicorn > /dev/null; then
    echo "❌ Uvicorn упал! Содержимое server.log:"
    cat server.log
    exit 1
fi

python3 test_and_auto_fix.py
