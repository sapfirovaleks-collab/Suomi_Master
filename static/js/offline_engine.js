
// Suomi Master Offline Engine (IndexedDB & Local Cache)

const DB_NAME = 'SuomiMasterOfflineDB';
const DB_VERSION = 1;

// Инициализация базы данных в телефоне
function initOfflineDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);
        request.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains('user_markers')) {
                db.createObjectStore('user_markers', { keyPath: 'id', autoIncrement: true });
            }
            if (!db.objectStoreNames.contains('cached_layers')) {
                db.createObjectStore('cached_layers', { keyPath: 'layer_id' });
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = (e) => reject(e);
    });
}

// Сохранение метки/фото в офлайн-очередь
async function saveMarkerOffline(markerData) {
    const db = await initOfflineDB();
    const tx = db.transaction('user_markers', 'readwrite');
    const store = tx.objectStore('user_markers');
    store.add({ ...markerData, created_at: new Date().toISOString(), synced: false });
    console.log('📱 [Offline] Метка сохранена локально на телефоне');
}

// Локальный ИИ-справочник безопасности при отсутствии сети
const OFFLINE_RULES = {
    karhu: 'Встреча с медведем: Не бежать! Медленно отходите назад, говорите спокойным голосом, не смотрите в глаза.',
    susi: 'Встреча с волком: Не поворачивайтесь спиной, поднимите руки/куртку выше, издавайте громкие звуки.',
    onginta: 'Обычная маховая удочка (onginta) и подледный лов (pilkkiminen) бесплатны по Jokamiehenoikeus.',
    kuha_size: 'Минимальный размер судака (kuha) в Финляндии — 42 см.'
};

function getOfflineSafetyAdvice(topic) {
    return OFFLINE_RULES[topic] || 'Режим Офлайн: Информационная база доступна локально. Данные обновятся при подключении к сети.';
}

// Отслеживание статуса сети
window.addEventListener('online', () => {
    console.log('🌐 Связь восстановлена! Запуск синхронизации...');
    syncOfflineData();
});

window.addEventListener('offline', () => {
    console.log('🌲 Связь потеряна. Переход в автономный режим (Offline-First)');
});

async function syncOfflineData() {
    // Автоматическая отправка накопленных меток на сервер при появлении сети
    const db = await initOfflineDB();
    const tx = db.transaction('user_markers', 'readonly');
    const store = tx.objectStore('user_markers');
    const request = store.getAll();
    
    request.onsuccess = async () => {
        const markers = request.result;
        if (markers.length > 0) {
            console.log(`🔄 Синхронизация ${markers.length} сохраненных офлайн-меток с сервером...`);
            // Логика отправки на бэкенд
        }
    };
}

initOfflineDB();



// =====================================================================
// SUOMI MASTER PREMIUM OFFLINE & COMPASS ENGINE
// =====================================================================

// --- 1. АППАРАТНЫЙ ИНТЕРАКТИВНЫЙ КОМПАС ---
function initCompass() {
    if (window.DeviceOrientationEvent) {
        window.addEventListener('deviceorientation', (event) => {
            let heading = null;
            
            if (event.webkitCompassHeading) {
                // Поддержка iOS Safari
                heading = event.webkitCompassHeading;
            } else if (event.alpha) {
                // Поддержка Android
                heading = 360 - event.alpha;
            }

            if (heading !== null) {
                const compassArrow = document.getElementById('compass-arrow');
                const compassDegrees = document.getElementById('compass-degrees');
                
                if (compassArrow) {
                    compassArrow.style.transform = `rotate(${heading}deg)`;
                }
                if (compassDegrees) {
                    compassDegrees.innerText = `${Math.round(heading)}°`;
                }
            }
        });
        console.log('🧭 Компас успешно инициализирован');
    } else {
        console.log('⚠️ Датчик ориентации (компас) не поддерживается на этом устройстве');
    }
}

// --- 2. ПРЕМИУМ СКАЧИВАНИЕ ОФЛАЙН-КАРТ С ТОЧКАМИ 9 СЛОЕВ ---
async function downloadPremiumOfflinePack(regionBounds, isPremium = false) {
    if (!isPremium) {
        alert('⭐ Функция скачивания офлайн-карт и глубин доступна только в Premium (3.90 €/мес). Оформите подписку для автономных походов!');
        return;
    }

    console.log('📥 Начинается премиум-скачивание карты и слоя всех точек...');
    
    // Получение всех сохраненных точек 9 слоев для сохранения офлайн
    try {
        const response = await fetch('/api/geo/all-layers');
        const layersData = await response.json();
        
        const db = await initOfflineDB();
        const tx = db.transaction('cached_layers', 'readwrite');
        const store = tx.objectStore('cached_layers');
        
        store.put({ layer_id: 'full_offline_pack', data: layersData, downloaded_at: new Date().toISOString() });
        
        alert('✅ Офлайн-пакет региона и все 9 слоев точек успешно загружены в память устройства!');
    } catch (err) {
        console.error('Ошибка скачивания пакета:', err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initCompass();
});
