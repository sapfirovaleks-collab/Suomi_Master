#!/bin/bash
set -e

echo "=================================================="
echo "  Suomi Master - Docker Production Deploy"
echo "=================================================="

if [ ! -f .env ]; then
  echo "❌ Нет .env файла! Создаю .env с генерацией секретов..."
  ADMIN_TOKEN_NEW=$(openssl rand -base64 32 | tr -d '\n')
  POSTGRES_PW_NEW=$(openssl rand -base64 16 | tr -d '\n')
  echo "ADMIN_TOKEN=$ADMIN_TOKEN_NEW" > .env
  echo "POSTGRES_PASSWORD=$POSTGRES_PW_NEW" >> .env
  echo "SECURITY_MODE=production" >> .env
  echo "✅ .env создан с уникальными ключами"
fi

docker compose up -d db redis
sleep 5
docker compose up -d app
echo "=================================================="
echo "  Production запущен на http://localhost:8000"
echo "=================================================="
