FROM python:3.10-slim

# Instalar dependencias del sistema para Chrome y Selenium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    wget \
    curl \
    unzip \
    gnupg \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Variables de entorno para Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Crear carpeta de trabajo
WORKDIR /app

# Copiar los archivos del proyecto (menos el .env si lo ignorás)
COPY . /app

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando por defecto
CMD ["python", "scraper.py"]
