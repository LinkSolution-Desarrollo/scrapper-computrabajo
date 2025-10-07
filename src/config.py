import os
from dotenv import load_dotenv

load_dotenv()

# User credentials
USUARIO = os.environ.get("USUARIO")
CLAVE = os.environ.get("CLAVE")

# MinIO configuration
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET")

# URLs
BASE_URL = "https://ats.pandape.com"
LOGIN_URL = f"{BASE_URL}/Company/Vacancy?Pagination[PageNumber]=1&Pagination[PageSize]=1000&Order=1&IdsFilter=2&RecruitmentType=0"
WEBHOOK_INSERT_URL = "http://10.20.62.101:5678/webhook/insert"
WEBHOOK_VACANCY_URL = "http://10.20.62.101:5678/webhook/vacant"

# Local download folder
DOWNLOADS_FOLDER = "downloads"

# Cache configuration
CACHE_CONFIG = {
    "CACHE_ENABLED": False,  # Deshabilitar caché para reducir espacio en disco
    "CACHE_FILE": "cache/cv_cache.json",
    "MAX_CACHE_SIZE": 20,    # Reducir tamaño máximo del caché
    "CACHE_EXPIRY_DAYS": 1,  # Reducir tiempo de expiración a 1 día
    "AUTO_CLEAN_CACHE": True, # Limpiar automáticamente archivos antiguos
    "KEEP_LOCAL_FILES": False # No mantener archivos locales después de subir a MinIO
}

# Scraping configuration
SCRAPING_CONFIG = {
    "DEFAULT_WAIT_TIME": 3,
    "LONG_WAIT_TIME": 10,
    "MAX_RETRIES": 3,
    "RATE_LIMIT_DELAY": 1,  # seconds between requests
    "SCROLL_PAUSE_TIME": 2,
    "DOWNLOAD_TIMEOUT": 30,
    "WEBHOOK_TIMEOUT": 10
}
