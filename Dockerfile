FROM python:3.10-slim

# 1. Instalar dependencias del sistema y Chromium
RUN apt-get update && apt-get install -y     chromium     chromium-driver     fonts-liberation     libnss3     libatk-bridge2.0-0     libgtk-3-0     libxss1     libasound2     --no-install-recommends &&     apt-get clean &&     rm -rf /var/lib/apt/lists/*

# Crear carpeta de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . /app

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Variables de entorno para Selenium y MinIO
ENV CHROME_BIN=/usr/bin/chromium
ENV USUARIO=Flor.leyva@linksolution.com.ar
ENV CLAVE=Febrero2023
ENV MINIO_ENDPOINT=http://10.20.62.101:9000
ENV MINIO_ACCESS_KEY=BWg7DUZUddOsWesTdFTF
ENV MINIO_SECRET_KEY=w8p97JgkpHwpV2vzXtUGUc6tYtB8l6e4QBcfGHIC
ENV MINIO_BUCKET=curriculums

# Comando por defecto para ejecutar el scraper
CMD ["python", "main.py"]