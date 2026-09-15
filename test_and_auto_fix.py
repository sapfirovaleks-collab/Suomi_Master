import urllib.request
import urllib.error
import time

def check_endpoint(url, name):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'HealthCheck/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            if status == 200:
                print(f"✅ [{name}] {url} -> HTTP 200 OK")
                return True
            else:
                print(f"⚠️ [{name}] {url} -> HTTP {status}")
                return False
    except Exception as e:
        print(f"❌ [{name}] {url} -> Ошибка: {e}")
        return False

print("="*60)
print("🔍 Диагностика эндпоинтов Suomi Master v5.4 FULL...")
print("="*60)

endpoints = [
    ("http://127.0.0.1:8000/api/system/self-check", "Самопроверка базы и модулей"),
    ("http://127.0.0.1:8000/api/map/wildlife", "Avtodor: Карта троп зверей"),
    ("http://127.0.0.1:8000/api/auto/maintenance-guide", "Авто-диагностика & Ремонт"),
    ("http://127.0.0.1:8000/", "Корневой статус системы")
]

failed = 0
for url, name in endpoints:
    if not check_endpoint(url, name):
        failed += 1

print("-" * 60)
if failed == 0:
    print("🎉 Все сервисы Suomi Master v5.4 работают идеально!")
else:
    print(f"⚠️ Ошибки на {failed} эндпоинтах.")
print("="*60)
