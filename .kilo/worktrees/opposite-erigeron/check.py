import urllib.request, json, time, sys
urls = [
    'http://127.0.0.1:8000/api/system/health/full',
    'http://127.0.0.1:8000/api/system/medicine',
    'http://127.0.0.1:8000/api/ice/thickness?lat=63.8333&lng=23.1333'
]
print("=== 💊 v6.3 AI MEDICINE ПРОВЕРКА ===")
for i in range(6):
    try:
        r = urllib.request.urlopen('http://127.0.0.1:8000/api/system/health/full', timeout=3)
        d = json.loads(r.read())
        print(f"💊 Версия: {d.get('version')}")
        print(f"🚀 Воскрешений: {d.get('resurrection_count')}")
        cb = d.get('circuit_breaker',{})
        print(f"🛡️ Circuit Breaker: {cb.get('state')} ({cb.get('failures')} fails)")
        print(f"✅ Статус ядра: {d.get('engine_status')}")
        print(f"💾 Hit rate: {d.get('hit_rate_percent')}% | Cache keys: {d.get('active_cache_keys')}")
        print(f"⚡ Heals: {d.get('metrics',{}).get('auto_heals')} | Medicines: {d.get('metrics',{}).get('medicines_applied')}")
        break
    except Exception as e:
        print(f"⏳ Попытка {i+1}/6: {e}")
        time.sleep(2)
else:
    print("❌ Сервер не ответил, смотри server.log")
    sys.exit(1)

# Доп тест medicine
try:
    r = urllib.request.urlopen('http://127.0.0.1:8000/api/system/medicine', timeout=3)
    m = json.loads(r.read())
    print(f"\n💊 Лекарств: {list(m.get('medicines',{}).keys())}")
except Exception as e:
    print(f"Medicine error: {e}")
