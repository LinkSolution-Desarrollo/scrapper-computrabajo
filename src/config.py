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
WEBHOOK_EDIT_VACANCY_URL = "http://10.20.62.101:5678/webhook/editar_vacante"

# Local download folder
DOWNLOADS_FOLDER = "downloads"
