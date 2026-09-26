
# Configuration & Core Settings for Suomi Master Engine
import os

class Settings:
    PROJECT_NAME: str = 'Suomi Master Core'
    VERSION: str = '2.5.0'
    EMERGENCY_NUMBER: str = '112'
    MYRKYTYSTIETOKESKUS: str = '0800 147 111'
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379')

settings = Settings()
