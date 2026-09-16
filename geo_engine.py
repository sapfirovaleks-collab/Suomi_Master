"""
Suomi Master - Geo Engine v4.0 - FROM HELSINKI TO NORWEGIAN FJORDS
Покрытие: 19 регионов Финляндии + Норвегия, Швеция, Арктика до Нордкапа
"""
from typing import Dict
import math

SCANDINAVIA_FULL = [
    ("FI-01", "Uusimaa", "Уусимаа", "Helsinki", 59.90, 60.65, 23.20, 26.40, 60.17, 24.94, "FI", "region"),
    ("FI-02", "Varsinais-Suomi", "Варсинайс-Суоми", "Turku", 59.95, 61.10, 21.10, 23.20, 60.45, 22.26, "FI", "region"),
    ("FI-03", "Satakunta", "Сатакунта", "Pori", 61.10, 62.20, 21.30, 23.20, 61.48, 22.00, "FI", "region"),
    ("FI-04", "Kanta-Häme", "Канта-Хяме", "Hämeenlinna", 60.60, 61.15, 23.20, 25.10, 60.99, 24.46, "FI", "region"),
    ("FI-05", "Pirkanmaa", "Пирканмаа", "Tampere", 61.15, 62.30, 22.80, 24.80, 61.49, 23.76, "FI", "region"),
    ("FI-06", "Päijät-Häme", "Пяйят-Хяме", "Lahti", 60.65, 61.60, 24.80, 26.40, 61.05, 25.65, "FI", "region"),
    ("FI-07", "Kymenlaakso", "Кюменлааксо", "Kouvola", 60.30, 61.10, 26.20, 27.80, 60.87, 26.70, "FI", "region"),
    ("FI-08", "Etelä-Karjala", "Южная Карелия", "Lappeenranta", 60.70, 61.80, 27.40, 29.20, 61.05, 28.18, "FI", "region"),
    ("FI-09", "Etelä-Savo", "Южное Саво", "Mikkeli", 61.20, 62.50, 26.40, 29.00, 61.68, 27.27, "FI", "region"),
    ("FI-10", "Pohjois-Savo", "Северное Саво", "Kuopio", 62.50, 63.90, 26.20, 28.80, 62.89, 27.67, "FI", "region"),
    ("FI-11", "Pohjois-Karjala", "Северная Карелия", "Joensuu", 61.80, 63.60, 28.80, 31.00, 62.60, 29.76, "FI", "region"),
    ("FI-12", "Keski-Suomi", "Центральная Финляндия", "Jyväskylä", 61.60, 63.20, 24.50, 26.80, 62.24, 25.74, "FI", "region"),
    ("FI-13", "Etelä-Pohjanmaa", "Южная Остроботния", "Seinäjoki", 62.20, 63.20, 21.80, 24.50, 62.79, 22.84, "FI", "region"),
    ("FI-14", "Pohjanmaa", "Остроботния", "Vaasa", 62.30, 64.10, 20.60, 23.00, 63.09, 21.61, "FI", "region"),
    ("FI-15", "Keski-Pohjanmaa", "Центральная Остроботния", "Kokkola", 63.20, 64.60, 22.00, 24.80, 63.83, 23.13, "FI", "region"),
    ("FI-16", "Pohjois-Pohjanmaa", "Северная Остроботния", "Oulu", 64.10, 66.00, 23.00, 30.00, 65.01, 25.46, "FI", "region"),
    ("FI-17", "Kainuu", "Кайнуу", "Kajaani", 63.60, 65.20, 27.00, 30.00, 64.22, 27.73, "FI", "region"),
    ("FI-18", "Lappi", "Лапландия", "Rovaniemi", 66.00, 70.10, 20.00, 30.00, 66.50, 25.72, "FI", "region"),
    ("FI-19", "Ahvenanmaa", "Аландские острова", "Mariehamn", 59.70, 60.80, 19.20, 21.10, 60.09, 19.93, "FI", "region"),
    ("NO-01", "Finnmark", "Финнмарк - Нордкап", "Alta", 69.00, 71.50, 20.00, 31.50, 70.07, 24.00, "NO", "fjord_arctic"),
    ("NO-02", "Troms", "Тромс - Лофотены", "Tromsø", 68.00, 70.00, 16.00, 23.00, 69.64, 18.95, "NO", "fjord"),
    ("NO-03", "Nordland", "Нурланн - Лофотены", "Bodø", 65.00, 69.00, 11.00, 17.50, 67.28, 14.40, "NO", "fjord"),
    ("NO-04", "Trøndelag", "Трёнделаг - фьорды", "Trondheim", 62.50, 65.50, 9.00, 14.00, 63.43, 10.39, "NO", "fjord"),
    ("NO-05", "Vestland", "Вестланн - Согне-фьорд", "Bergen", 59.50, 62.50, 4.50, 8.50, 60.39, 5.32, "NO", "fjord"),
    ("NO-06", "Møre og Romsdal", "Мёре - Гейрангер-фьорд", "Ålesund", 61.50, 63.50, 5.00, 9.00, 62.47, 6.15, "NO", "fjord"),
    ("NO-07", "Rogaland", "Ругаланн - Люсе-фьорд", "Stavanger", 58.00, 60.00, 5.00, 7.50, 58.97, 5.73, "NO", "fjord"),
    ("SE-01", "Norrbotten", "Норрботтен - Шведская Лапландия", "Kiruna", 65.50, 69.00, 18.00, 24.00, 67.85, 20.22, "SE", "lapland"),
    ("SE-02", "Västerbotten", "Вестерботтен", "Umeå", 63.50, 66.00, 16.00, 22.00, 63.82, 20.26, "SE", "coast"),
    ("SE-03", "Lapland-SW", "Шведская Лапландия - Абиску", "Abisko", 67.50, 69.50, 17.00, 21.00, 68.35, 18.81, "SE", "fjell"),
    ("AR-01", "Barents Sea", "Баренцево море", "Nordkapp", 70.50, 72.00, 20.00, 32.00, 71.17, 25.78, "AR", "arctic"),
    ("AR-02", "Norwegian Sea - Lofoten", "Норвежское море - Лофотены", "Reine", 67.00, 69.00, 11.50, 14.50, 68.09, 13.09, "NO", "lofoten"),
]

FINLAND_REGIONS_ACCURATE = [r for r in SCANDINAVIA_FULL if r[10] == "FI"]

def haversine(lat1, lng1, lat2, lng2):
    R = 6371.0
    dlat = math.radians(lat2-lat1)
    dlng = math.radians(lng2-lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlng/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def detect_region_accurate(lat: float, lng: float) -> Dict:
    candidates = []
    for r in SCANDINAVIA_FULL:
        code, name_fi, name_ru, hub, lat_min, lat_max, lng_min, lng_max, c_lat, c_lng, country, rtype = r
        if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
            dist = haversine(lat, lng, c_lat, c_lng)
            area = (lat_max - lat_min) * (lng_max - lng_min)
            candidates.append((dist, area, {
                "code": code, "name_fi": name_fi, "name_ru": name_ru, "hub": hub,
                "country": country, "type": rtype, "center": (c_lat, c_lng)
            }))
    if not candidates:
        closest = min(SCANDINAVIA_FULL, key=lambda x: haversine(lat, lng, x[8], x[9]))
        code, name_fi, name_ru, hub, _, _, _, _, c_lat, c_lng, country, rtype = closest
        dist = haversine(lat, lng, c_lat, c_lng)
        return {
            "code": code, "name_fi": name_fi, "name_ru": name_ru, "hub": hub,
            "country": country, "type": rtype, "accuracy": "nearest", "distance_km": round(dist,1)
        }
    candidates.sort(key=lambda x: (x[0], x[1]))
    best = candidates[0][2]
    best["accuracy"] = "high"
    best["distance_km"] = round(candidates[0][0], 1)
    return best

def get_coverage_info():
    return {
        "total_regions": len(SCANDINAVIA_FULL),
        "finland": len([r for r in SCANDINAVIA_FULL if r[10]=="FI"]),
        "norway": len([r for r in SCANDINAVIA_FULL if r[10]=="NO"]),
        "sweden": len([r for r in SCANDINAVIA_FULL if r[10]=="SE"]),
        "arctic": len([r for r in SCANDINAVIA_FULL if r[10]=="AR"]),
        "coverage": "От Балтики до Баренцева моря, от фьордов Бергена до Лофотенов и Нордкапа"
    }
