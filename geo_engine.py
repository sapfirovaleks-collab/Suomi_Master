# -*- coding: utf-8 -*-
"""
Suomi Master - Geo-Engine & Ecosystem Core Data (Full 9 Outdoor & Service Layers)
"""

ECOSYSTEM_LAYERS = {
    "fishing": "🎣 Kalastus & Syvyydet",
    "sauna": "🧖‍♂️ Rantasaunat & Avanto",
    "shelter": "🪵 Laavut & Autiotuvat",
    "santa": "🎅 Joulupukki & Napapiiri",
    "safari": "🐕 Husky- & Porosafarit",
    "rental_living": "🏡 Majoitus & Mökit",
    "auto": "🚗 Auto & Caravan & Huolto",
    "forest": "🌲 Metsät, Marjat & Sienet",
    "tools": "🛠️ Työkalut, Laitteet & Varustevuokraus"
}

ALL_LOCATIONS = [
    # --- 1. FISHING & DEPTHS ---
    {
        "id": 1,
        "name": "Grovfjord / Elvegård Trolling Zone",
        "category": "fishing",
        "lat": 68.6833, "lng": 17.5333,
        "depth_max": 120,
        "species": ["Turska", "Seiti", "Pallas"],
        "icon": "🎣",
        "description": "Syvänveden kalastuspaikka ja isot turskat."
    },
    {
        "id": 2,
        "name": "Öjanjärvi Syvänne",
        "category": "fishing",
        "lat": 63.8000, "lng": 23.0800,
        "depth_max": 14,
        "species": ["Kuha", "Ahven", "Hauki"],
        "icon": "🐟",
        "description": "Suosittu kuhan uistelu- ja heittokalastusalue."
    },

    # --- 2. SAUNAS ---
    {
        "id": 101,
        "name": "Kokkola Rantasauna & Uimapaikka",
        "category": "sauna",
        "lat": 63.8385, "lng": 23.1305,
        "price": "Free / Public",
        "icon": "🧖‍♂️",
        "description": "Puusauna ja talviuintipaikka (avanto) meren rannalla."
    },

    # --- 3. SHELTERS & LAAVUT ---
    {
        "id": 102,
        "name": "Ounasvaaran Aurora-laavu",
        "category": "shelter",
        "lat": 66.5042, "lng": 25.7601,
        "price": "Ilmainen",
        "icon": "🪵",
        "description": "Metsähallituksen laavu, puut valmiina, erinomainen revontulipaikka."
    },

    # --- 4. SANTA & LAPLAND ---
    {
        "id": 201,
        "name": "Joulupukin Kylä (Santa Claus Village)",
        "category": "santa",
        "lat": 66.5435, "lng": 25.8472,
        "price": "Vapaa pääsy",
        "icon": "🎅",
        "description": "Napapiiri, Joulupukin pääposti ja satumainen elämys perheille."
    },

    # --- 5. SAFARIS ---
    {
        "id": 202,
        "name": "Husky Park Rovaniemi",
        "category": "safari",
        "lat": 66.5450, "lng": 25.8510,
        "price": "45€ / hlö",
        "icon": "🐕",
        "description": "Aitoja elämyksiä ja ajeluita siperianhuskyilla tunturissa."
    },

    # --- 6. ACCOMMODATION ---
    {
        "id": 301,
        "name": "Santa Claus Holiday Village Cottages",
        "category": "rental_living",
        "lat": 66.5438, "lng": 25.8480,
        "price": "180€ / yö",
        "icon": "🏡",
        "description": "Tasokkaat mökit ja huoneistot Napapiirillä."
    },

    # --- 7. AUTO & CARAVAN ---
    {
        "id": 401,
        "name": "Kokkola Caravan & Matkailuautoparkki",
        "category": "auto",
        "lat": 63.8400, "lng": 23.1200,
        "price": "15€ / vrk",
        "icon": "🚐",
        "description": "Sähköpisteet, vedentäyttö ja matkailuauton huoltopiste meren lähellä."
    },

    # --- 8. FORESTS & BERRIES ---
    {
        "id": 501,
        "name": "Perhonjokilaakson Sienimetsät & Marjamaat",
        "category": "forest",
        "lat": 63.7900, "lng": 23.2500,
        "price": "Jokamiehenoikeus",
        "icon": "🍄",
        "description": "Erinomaiset mohoviki- ja kantarelli-maastot sekä mustikka."
    },

    # --- 9. TOOLS & EQUIPMENT RENTAL (TYÖKALUVUOKRAUS) ---
    {
        "id": 601,
        "name": "Kokkola Outdoor & Tool Rental Hub",
        "category": "tools",
        "lat": 63.8350, "lng": 23.1300,
        "price": "Vuokraus 15-40€ / vrk",
        "icon": "🛠️",
        "description": "Akkukoneet, kaira/moottorikairat, kaikuluotaimet, generaattorit, lumikengät ja venetrailerit."
    }
]

def get_all_locations():
    return ALL_LOCATIONS
