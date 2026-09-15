#!/bin/bash
echo "🚀 Перезапуск автономного сервера Suomi Master v5.4..."
pkill -f uvicorn || true
sleep 1

source /workspaces/Suomi_Master/venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null || true

nohup uvicorn main:app --host 127.0.0.1 --port 8000 > server.log 2>&1 &

echo "⏳ Ожидание инициализации Uvicorn (5 секунд)..."
sleep 5

if ! pgrep -f uvicorn > /dev/null; then
    echo "❌ Лог ошибок сервера:"
    cat server.log
    exit 1
fi

python3 test_and_auto_fix.py
