# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

# Cargar variables del entorno
load_dotenv()

# Credenciales
USUARIO = os.environ.get("USUARIO")
CLAVE = os.environ.get("CLAVE")

# MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

# Chrome
CHROME_BIN = os.getenv("CHROME_BIN")

# Webhook
WEBHOOK_VACANT = "http://10.20.62.94:5678/webhook/vacant"
WEBHOOK_INSERT = "http://10.20.62.94:5678/webhook/insert"
