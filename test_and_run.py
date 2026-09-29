import sys
from fastapi.testclient import TestClient

try:
    from main import app
    print("[CHECK 1/2] main.py загружен без синтаксических ошибок.")
except Exception as e:
    print(f"[FAIL 1/2] Ошибка при загрузке main.py: {e}")
    sys.exit(1)

client = TestClient(app)
endpoints = ["/", "/manifest.json", "/api/auto/partners", "/api/auto/deals", "/api/auto/insurance"]
all_ok = True

print("\n--- 🚀 ТЕСТИРОВАНИЕ ЭНДПОИНТОВ ЯДРА ---")
for ep in endpoints:
    res = client.get(ep)
    if res.status_code == 200:
        print(f"  [PASS] {ep:<25} -> Status 200 OK")
    else:
        print(f"  [FAIL] {ep:<25} -> Status {res.status_code}")
        all_ok = False

if all_ok:
    print("--- 🎉 ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ! ЗАПУСКАЕМ СЕРВЕР ---")
