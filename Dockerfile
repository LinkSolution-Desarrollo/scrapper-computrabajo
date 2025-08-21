FROM python:3.10-slim

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    --no-install-recommends

# Agregar llave y repositorio oficial de Google Chrome
RUN apt-get update && apt-get install -y wget gnupg2 --no-install-recommends && \
    wget -q -O /usr/share/keyrings/google-linux-signing-key.gpg https://dl.google.com/linux/linux_signing_key.pub && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-key.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Instalar Google Chrome estable
RUN apt-get update && apt-get install -y google-chrome-stable

# Limpiar cache de apt
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Crear carpeta de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . /app

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Variables de entorno para Selenium y MinIO
ENV CHROME_BIN=/usr/bin/google-chrome-stable
ENV USUARIO=Flor.leyva@linksolution.com.ar
ENV CLAVE=Febrero2023
ENV MINIO_ENDPOINT=http://10.20.62.101:9000
ENV MINIO_ACCESS_KEY=BWg7DUZUddOsWesTdFTF
ENV MINIO_SECRET_KEY=w8p97JgkpHwpV2vzXtUGUc6tYtB8l6e4QBcfGHIC
ENV MINIO_BUCKET=curriculums

# Comando por defecto para ejecutar el scraper
CMD ["python", "scraper.py"]
