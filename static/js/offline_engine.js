
// Suomi Master Offline Engine (IndexedDB & Local Cache)

const DB_NAME = 'SuomiMasterOfflineDB';
const DB_VERSION = 1;

// Инициализация базы данных в телефоне
function initOfflineDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);
        request.onupgradeneeded = (e) => {
            const db = e.target.result;
                db.createObjectStore('user_markers', { keyPath: 'id', autoIncrement: true });
            }
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
