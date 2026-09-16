import urllib.request
import urllib.error

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
print("🔍 Полная диагностика Suomi Master v5.6 Complete App...")
print("="*60)

endpoints = [
    ("http://127.0.0.1:8000/api/system/self-check", "Самопроверка БД и модулей"),
    ("http://127.0.0.1:8000/api/weather/live", "Live Погода, Лед & Аврора"),
    ("http://127.0.0.1:8000/api/system/tyre-compliance", "SOS 112 & Закон о резине"),
    ("http://127.0.0.1:8000/api/map/wildlife", "Avtodor: Тропы лосей/медведей"),
    ("http://127.0.0.1:8000/api/map/harvest", "Грибы & Ягоды"),
    ("http://127.0.0.1:8000/api/map/ev", "EV Зарядки"),
    ("http://127.0.0.1:8000/api/map/free-shelters", "Избушки Autiotupa/Laavu"),
    ("http://127.0.0.1:8000/api/auto/maintenance-guide", "Авто-диагностика & Ремонт"),
    ("http://127.0.0.1:8000/manifest.json", "PWA Manifest App"),
    ("http://127.0.0.1:8000/map", "Веб-интерфейс Карты")
]

failed = 0
for url, name in endpoints:
    if not check_endpoint(url, name):
        failed += 1

print("-" * 60)
if failed == 0:
    print("🎉 ВСЕ 10 СЕРВИСОВ И PWA APP Suomi Master v5.6 РАБОТАЮТ ИДЕАЛЬНО!")
else:
    print(f"⚠️ Ошибки на {failed} эндпоинтах.")
print("="*60)
