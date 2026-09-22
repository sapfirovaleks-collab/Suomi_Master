import urllib.request

def check_endpoint(url, name):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'HealthCheck/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.getcode() == 200:
                print(f"✅ [{name}] {url} -> HTTP 200 OK")
                return True
            return False
    except Exception as e:
        print(f"❌ [{name}] {url} -> Ошибка: {e}")
        return False

print("="*60)
print("🔍 Диагностика Suomi Master v5.6 ULTRA MERGED...")
print("="*60)

endpoints = [
    ("http://127.0.0.1:8000/api/system/self-check", "Самопроверка & Geo coverage"),
    ("http://127.0.0.1:8000/api/weather/live", "Weather & Ice AI"),
    ("http://127.0.0.1:8000/api/system/tyre-compliance", "SOS & Tyres"),
    ("http://127.0.0.1:8000/api/map/tiles-config", "Топо-карты Retkikartta"),
    ("http://127.0.0.1:8000/api/fishing/norway-rules", "Норвежская рыбалка & Лицензии"),
    ("http://127.0.0.1:8000/api/fuel/prices", "Мониторинг цен на топливо"),
    ("http://127.0.0.1:8000/api/map/wildlife", "Avtodor Wildlife"),
    ("http://127.0.0.1:8000/api/map/harvest", "Грибы & Ягоды"),
    ("http://127.0.0.1:8000/api/map/ev", "EV Зарядки"),
    ("http://127.0.0.1:8000/api/map/free-shelters", "Избушки Autiotupa"),
    ("http://127.0.0.1:8000/api/auto/maintenance-guide", "База Авто-ремонта"),
    ("http://127.0.0.1:8000/manifest.json", "PWA Manifest"),
    ("http://127.0.0.1:8000/map", "Веб-интерфейс Карты")
]

failed = sum(1 for url, name in endpoints if not check_endpoint(url, name))
print("-" * 60)
if failed == 0:
    print("🎉 ВСЕ МОДУЛИ Suomi Master v5.6 ULTRA MERGED РАБОТАЮТ ИДЕАЛЬНО!")
else:
    print(f"⚠️ Ошибки на {failed} эндпоинтах.")
print("="*60)
