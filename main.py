cd /workspaces/Suomi_Master

# Сохрани свой main.py отдельно (у тебя 9+ изменений)
cp main.py main_my_backup.py

# Сохрани все изменения в stash
git stash push -m "save my changes" --include-untracked

# Теперь pull сработает
git pull

# Верни свой main.py обратно (он точнее чем на гитхабе)
cp main_my_backup.py main.py
git status# Убей все старое (у тебя 7 bash висело)
docker compose down
docker compose -f docker-compose.prod.yml down 2>/dev/null; true
pkill -f uvicorn; true

# Запусти ТОЛЬКО простой файл
docker compose -f docker-compose.yml up -d --build

# Подожди 15 сек
sleep 15
docker compose -f docker-compose.yml logs app --tail 30
docker compose -f docker-compose.yml psload_test.pyfix_git_and_docker.shimport os
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import create_engine, Column, Integer, String, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "suomi_master_ultimate_key_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Suomi-Master Ultimate Map & Geo Edition", version="4.6.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./suomi_master.db")
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    city = Column(String, nullable=True)

class RentalDB(Base):
    __tablename__ = "rentals"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    price = Column(Integer)
    city = Column(String, index=True)
    owner_email = Column(String)
    phone = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

class CarLogDB(Base):
    __tablename__ = "car_logs"
    id = Column(Integer, primary_key=True, index=True)
    owner_email = Column(String, index=True)
    car_model = Column(String)
    service_name = Column(String)
    mileage = Column(String)
    notes = Column(Text)
    date = Column(String)

class CommentDB(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    rental_id = Column(Integer, index=True)
    user_email = Column(String)
    text = Column(Text)
    date = Column(String)

class NotificationDB(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    text = Column(String)
    date = Column(String)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    db = SessionLocal()
    if db.query(RentalDB).count() == 0:
        initial_items = [
            RentalDB(title="Momenttiavain (Динамо-ключ)", price=5, city="Kokkola", owner_email="admin@suomimaster.fi", phone="+358401234567", image_url=None),
            RentalDB(title="Painepesuri (Мойка высокого давления)", price=15, city="Vaasa", owner_email="admin@suomimaster.fi", phone="+358407654321", image_url=None),
            RentalDB(title="Akkuporakone (Шуруповерт Makita)", price=8, city="Kronoby", owner_email="admin@suomimaster.fi", phone="+358409998888", image_url=None)
        ]
        db.add_all(initial_items)
        db.commit()
    db.close()

init_db()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, min_length=6)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class DiagnosisRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    language: str = Field(..., pattern="^(ru|en|fi)$")

class RentalItem(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    price: int = Field(..., ge=1, le=500)
    city: str = Field(..., min_length=2, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    image_url: Optional[str] = None

class CarLogItem(BaseModel):
    car_model: str = Field(..., min_length=2, max_length=100)
    service_name: str = Field(..., min_length=2, max_length=100)
    mileage: str = Field(..., min_length=2, max_length=50)
    notes: Optional[str] = Field(None, max_length=300)

class CommentItem(BaseModel):
    text: str = Field(..., min_length=1, max_length=300)

AI_CLIENT = None
try:
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        AI_CLIENT = OpenAI(api_key=api_key)
except ImportError:
    pass

HTML_CLIENT = """
<!DOCTYPE html>
<html lang="fi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Suomi-Master Ultimate</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body class="bg-gray-50 text-gray-900 font-sans min-h-screen flex flex-col" onload="initApp()">

    <header class="bg-white border-b border-gray-200 p-4 flex justify-between items-center sticky top-0 z-50 shadow-xs">
        <h1 class="text-base font-bold text-teal-600 flex items-center">
            <i class="fa-solid fa-screwdriver-wrench mr-2"></i>Suomi-Master
        </h1>
        <div class="flex items-center gap-2">
            <button onclick="detectGeolocation()" class="bg-teal-50 hover:bg-teal-100 text-teal-700 text-xs px-2.5 py-1.5 rounded-lg border border-teal-200 font-medium flex items-center gap-1">
                <i class="fa-solid fa-location-crosshairs"></i> <span id="gpsBtnText">GPS</span>
            </button>
            <select id="langSelect" onchange="changeLanguage()" class="bg-gray-100 text-gray-800 text-xs px-2 py-1.5 rounded-lg border border-gray-300 outline-none font-medium">
                <option value="ru">RU</option>
                <option value="en">EN</option>
                <option value="fi">FI</option>
            </select>
        </div>
    </header>

    <main class="flex-1 p-4 pb-24 max-w-md mx-auto w-full space-y-4">
        <div id="tabWorkshop" class="space-y-4">
            <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                <h2 id="txtWorkshopTitle" class="font-semibold text-sm mb-2 text-gray-800">ИИ-диагностика авто и ошибок (OBD2)</h2>
                <textarea id="issueInput" rows="3" maxlength="500" class="w-full bg-gray-50 border border-gray-300 rounded-lg p-3 text-xs focus:border-teal-600 focus:bg-white outline-none resize-none text-gray-900" placeholder="Введите код ошибки (например, P0300) или опишите проблему..."></textarea>
                <button onclick="runDiagnosis()" id="submitBtn" class="mt-3 w-full bg-teal-600 hover:bg-teal-700 text-white font-medium py-2.5 rounded-lg text-xs transition flex items-center justify-center gap-2 shadow-xs">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> <span id="btnRunAi">Анализировать ошибку</span>
                </button>
            </div>
            <div id="resultContainer" class="hidden bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-3">
                <h3 class="font-bold text-teal-700 text-xs flex items-center">
                    <i class="fa-solid fa-circle-check mr-1.5"></i> Результат диагностики и коды:
                </h3>
                <div id="aiSteps" class="text-xs text-gray-700 space-y-1.5 bg-gray-50 p-3 rounded-lg border border-gray-100"></div>
                <div class="pt-2 border-t border-gray-100">
                    <p class="text-[11px] text-gray-500 mb-2 font-medium">Запчасти в Финляндии:</p>
                    <div class="flex gap-2">
                        <a href="https://www.motonet.fi" target="_blank" class="flex-1 bg-gray-100 hover:bg-gray-200 text-center py-2 rounded-lg text-[11px] font-semibold text-teal-700 border border-gray-200 transition">Motonet</a>
                        <a href="https://www.biltema.fi" target="_blank" class="flex-1 bg-gray-100 hover:bg-gray-200 text-center py-2 rounded-lg text-[11px] font-semibold text-teal-700 border border-gray-200 transition">Biltema</a>
                        <a href="https://www.trodo.fi" target="_blank" class="flex-1 bg-gray-100 hover:bg-gray-200 text-center py-2 rounded-lg text-[11px] font-semibold text-teal-700 border border-gray-200 transition">Trodo</a>
                    </div>
                </div>
            </div>
        </div>
        <div id="tabGarage" class="hidden space-y-4">
            <div class="bg-amber-50 border border-amber-200 p-3.5 rounded-xl shadow-xs space-y-2">
                <h3 class="text-xs font-bold text-amber-900 flex items-center"><i class="fa-solid fa-clipboard-check mr-1.5"></i> Чек-лист Katsastus (Техосмотр)</h3>
                <ul class="text-[11px] text-amber-800 space-y-1 list-disc list-inside">
                    <li>Тормозные усилия и стояночный тормоз (Käsijarru)</li>
                    <li>Глубина протектора шин (мин. 1.6 мм летом)</li>
                    <li>Работа фар, поворотников и омывателей</li>
                    <li>Отсутствие критических ошибок OBD2 в блоке двигателя</li>
                </ul>
            </div>
            <div class="bg-emerald-50 border border-emerald-200 p-3.5 rounded-xl shadow-xs space-y-1.5">
                <h3 class="text-xs font-bold text-emerald-900 flex items-center"><i class="fa-solid fa-recycle mr-1.5"></i> Утилизация масел и деталей (Ekorosk)</h3>
                <p class="text-[11px] text-emerald-800">Отработанное масло, фильтры и аккумуляторы нельзя выбрасывать. Сдавайте их бесплатно на сортировочные станции Ekorosk (Kokkola/Kronoby/Pietarsaari).</p>
                <a href="https://ekorosk.fi" target="_blank" class="inline-block text-[11px] font-bold text-emerald-700 underline pt-0.5">Открыть сайт Ekorosk &rarr;</a>
            </div>
            <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-3">
                <h2 id="txtGarageTitle" class="font-semibold text-sm text-gray-800">Журнал обслуживания авто</h2>
                <div id="carLogList" class="space-y-2"></div>
            </div>
            <div id="addCarLogBox" class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-2.5 hidden">
                <h3 class="text-xs font-bold text-gray-800">Добавить запись о замене / ремонте</h3>
                <input type="text" id="carModel" placeholder="Авто / Техника (Renault Scenic 2)" class="w-full bg-gray-50 border border-gray-300 rounded-lg p-2.5 text-xs outline-none text-gray-900">
                <input type="text" id="serviceName" placeholder="Что сделано (Замена салонного и масляного фильтра)" class="w-full bg-gray-50 border border-gray-300 rounded-lg p-2.5 text-xs outline-none text-gray-900">
                <input type="text" id="carMileage" placeholder="Пробег (например, 245 000 км)" class="w-full bg-gray-50 border border-gray-300 rounded-lg p-2.5 text-xs outline-none text-gray-900">
                <textarea id="carNotes" rows="2" placeholder="Заметки, артикулы деталей..." class="w-full bg-gray-50 border border-gray-300 rounded-lg p-2.5 text-xs outline-none resize-none text-gray-900"></textarea>
                <button onclick="postCarLog()" class="w-full bg-teal-600 hover:bg-teal-700 text-white font-medium py-2 rounded-lg text-xs transition">Сохранить в журнал</button>
            </div>
            <div id="garageLoginPrompt" class="bg-teal-50 border border-teal-200 p-3 rounded-xl text-center">
                <p class="text-xs text-teal-800 mb-2">Войдите в аккаунт, чтобы вести историю авто</p>
                <button onclick="switchTab('profile')" class="bg-teal-600 text-white px-4 py-1.5 rounded-lg text-xs font-semibold">Войти</button>
            </div>
        </div>
        <div id="tabRent" class="hidden space-y-4">
            <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-3">
                <div class="flex justify-between items-center">
                    <h2 id="txtRentTitle" class="font-semibold text-sm text-gray-800">Соседский прокат (P2P)</h2>
                    <div class="flex gap-1">
                        <button onclick="setRentView('list')" id="btnViewList" class="bg-teal-600 text-white text-[11px] px-2.5 py-1 rounded-lg font-medium">Список</button>
                        <button onclick="setRentView('map')" id="btnViewMap" class="bg-gray-200 text-gray-700 text-[11px] px-2.5 py-1 rounded-lg font-medium">Карта</button>
                    </div>
                </div>
                <div id="rentSearchBlock" class="flex gap-2">
                    <input type="text" id="searchFilter" oninput="loadRentals()" placeholder="Поиск по названию..." class="w-2/3 bg-gray-50 border border-gray-300 rounded-lg p-2 text-xs outline-none text-gray-900">
                    <input type="text" id="cityFilter" oninput="loadRentals()" placeholder="Город..." class="w-1/3 bg-gray-50 border border-gray-300 rounded-lg p-2 text-xs outline-none text-gray-900">
                </div>
                <div id="rentalList" class="space-y-3 pt-1"></div>
                <div id="rentalMapContainer" class="hidden space-y-2">
                    <div id="map" class="w-full h-72 rounded-lg border border-gray-300 z-10"></div>
                    <p class="text-[10px] text-gray-500 text-center">Интерактивная карта инструментов</p>
                </div>
            </div>
            <div id="addRentalBox" class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-2.5 hidden">
                <h3 id="txtAddTitle" class="text-xs font-bold text-gray-800">Сдать инструмент в аренду</h3>
                <input type="text" id="newTitle" placeholder="Название" class="w-full bg-gray-50 border border-gray-300 rounded-lg p-2.5 text-xs outline-none text-gray-900">
                <div class="flex gap-2">
                    <input type="number" id="newPrice" placeholder="Цена €/день" class="w-1/2 bg-gray-50 border border-gray-300 rounded-lg p-2.5 text-xs outline-none text-gray-900">
                    <input type="text" id="newCity" placeholder="Город" class="w-1/2 bg-gray-50 border border-gray-300 rounded-lg p-2.5 text-xs outline-none text-gray-900">
                </div>
                <input type="text" id="newPhone" placeholder="Телефон" class="w-full bg-gray-50 border border-gray-300 rounded-lg p-2.5 text-xs outline-none text-gray-900">
                <div class="space-y-1">
                    <label class="text-[11px] text-gray-600 font-medium">Фото инструмента:</label>
                    <input type="file" id="newImage" accept="image/*" class="w-full text-xs text-gray-500 file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100">
                </div>
                <button onclick="postRental()" class="w-full bg-teal-600 hover:bg-teal-700 text-white font-medium py-2 rounded-lg text-xs transition">Опубликовать</button>
            </div>
            <div id="loginPromptBox" class="bg-teal-50 border border-teal-200 p-3 rounded-xl text-center hidden">
                <p class="text-xs text-teal-800 mb-2">Войдите, чтобы добавить инструмент</p>
                <button onclick="switchTab('profile')" class="bg-teal-600 text-white px-4 py-1.5 rounded-lg text-xs font-semibold">Войти</button>
            </div>
        </div>
        <div id="tabOutdoors" class="hidden space-y-4">
            <div class="bg-gradient-to-br from-blue-900 to-indigo-950 p-4 rounded-xl text-white shadow-sm space-y-3">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="text-[10px] text-blue-200 font-semibold uppercase tracking-wider">Ilmatieteen laitos (FMI)</p>
                        <h3 class="text-sm font-bold mt-0.5">Kokkola / Kronoby alue</h3>
                    </div>
                </div>
            </div>
            <a href="https://www.eraluvat.fi" target="_blank" class="block w-full bg-white hover:bg-gray-50 border border-gray-200 p-3 rounded-xl text-center text-xs font-bold text-teal-700 shadow-sm transition">
                <i class="fa-solid fa-file-invoice-dollar mr-1"></i> Оплатить лицензию
            </a>
        </div>
        <div id="tabProfile" class="hidden space-y-4">
            <div id="authContainer" class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-3">
                <h2 id="txtAuthTitle" class="font-semibold text-sm text-gray-800">Вход / Регистрация</h2>
                <input type="email" id="authEmail" placeholder="Email" class="w-full bg-gray-50 border border-gray-300 rounded-lg p-2.5 text-xs outline-none text-gray-900">
                <input type="password" id="authPassword" placeholder="Пароль" class="w-full bg-gray-50 border border-gray-300 rounded-lg p-2.5 text-xs outline-none text-gray-900">
                <div class="flex gap-2">
                    <button onclick="loginUser()" class="w-1/2 bg-teal-600 hover:bg-teal-700 text-white font-medium py-2 rounded-lg text-xs transition">Войти</button>
                    <button onclick="registerUser()" class="w-1/2 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 rounded-lg text-xs transition">Регистрация</button>
                </div>
            </div>
            <div id="userProfileBox" class="hidden bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-3">
                <div class="text-center">
                    <i class="fa-solid fa-user-circle text-4xl text-teal-600"></i>
                    <p id="userEmailDisplay" class="text-xs font-bold text-gray-800 mt-1"></p>
                </div>
                <button onclick="logoutUser()" class="w-full bg-red-50 hover:bg-red-100 text-red-600 font-medium py-2 rounded-lg text-xs transition border border-red-200">Выйти</button>
            </div>
        </div>
    </main>

    <nav class="bg-white border-t border-gray-200 fixed bottom-0 left-0 right-0 max-w-md mx-auto flex justify-around py-3 shadow-lg z-50">
        <button onclick="switchTab('workshop')" id="navWorkshop" class="flex flex-col items-center text-teal-600 text-xs font-medium transition"><i class="fa-solid fa-wrench text-base mb-1"></i><span>Мастер</span></button>
        <button onclick="switchTab('garage')" id="navGarage" class="flex flex-col items-center text-gray-400 text-xs font-medium transition"><i class="fa-solid fa-car text-base mb-1"></i><span>Гараж</span></button>
        <button onclick="switchTab('rent')" id="navRent" class="flex flex-col items-center text-gray-400 text-xs font-medium transition"><i class="fa-solid fa-handshake text-base mb-1"></i><span>Прокат</span></button>
        <button onclick="switchTab('outdoors')" id="navOutdoors" class="flex flex-col items-center text-gray-400 text-xs font-medium transition"><i class="fa-solid fa-fish text-base mb-1"></i><span>Природа</span></button>
        <button onclick="switchTab('profile')" id="navProfile" class="flex flex-col items-center text-gray-400 text-xs font-medium transition"><i class="fa-solid fa-user text-base mb-1"></i><span>Профиль</span></button>
    </nav>

    <script>
        // (Сокращено для примера, убедитесь что вставили полный скрипт из предыдущих сообщений!)
        function initApp() { detectGeolocation(true); }
        // ... остальной JavaScript ...
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    return HTML_CLIENT

@app.post("/api/v1/register")
async def register(user: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Этот email уже зарегистрирован!")
    new_user = UserDB(email=user.email, hashed_password=get_password_hash(user.password))
    db.add(new_user)
    db.commit()
    return {"status": "success"}

@app.post("/api/v1/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    token = create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    try:
        payload = jwt.decode(auth_header.split(" ")[1], SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")

@app.get("/api/v1/profile")
async def get_profile(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.email == current_user).first()
    return {"email": db_user.email, "name": db_user.name, "phone": db_user.phone, "city": db_user.city}

@app.put("/api/v1/profile")
async def update_profile(data: UserUpdate, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.email == current_user).first()
    if data.name: db_user.name = data.name
    if data.phone: db_user.phone = data.phone
    if data.city: db_user.city = data.city
    db.commit()
    return {"status": "success"}

@app.post("/api/v1/upload")
async def upload_image(request: Request, file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
    ext = file.filename.split(".")[-1]
    filename = f"{datetime.now().timestamp()}_{os.urandom(4).hex()}.{ext}"
    file_path = os.path.join("uploads", filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    return {"url": f"/uploads/{filename}"}

@app.get("/api/v1/rentals")
async def get_rentals(db: Session = Depends(get_db)):
    items = db.query(RentalDB).all()
    return [{"id": i.id, "title": i.title, "price": i.price, "city": i.city, "owner": i.owner_email, "phone": i.phone, "image_url": i.image_url} for i in items]

@app.post("/api/v1/rentals")
async def add_rental(item: RentalItem, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    db_item = RentalDB(title=item.title, price=item.price, city=item.city, phone=item.phone, owner_email=current_user, image_url=item.image_url)
    db.add(db_item)
    db.commit()
    return {"status": "success"}

@app.get("/api/v1/garage")
async def get_garage(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    logs = db.query(CarLogDB).filter(CarLogDB.owner_email == current_user).all()
    return [{"id": l.id, "car_model": l.car_model, "service_name": l.service_name, "mileage": l.mileage, "notes": l.notes, "date": l.date} for l in logs]

@app.post("/api/v1/garage")
async def add_garage(item: CarLogItem, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    today = datetime.now().strftime("%d.%m.%Y")
    log = CarLogDB(owner_email=current_user, car_model=item.car_model, service_name=item.service_name, mileage=item.mileage, notes=item.notes, date=today)
    db.add(log)
    db.commit()
    return {"status": "success"}
