FROM python:3.10-slim

# Variables de entorno para configuración
ENV CHROME_VERSION "stable" # O puedes fijar una versión específica si es necesario
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema para Chrome y Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    # Dependencias de Chrome y Selenium
    fonts-liberation \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libexpat1 \
    libgbm1 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    # Limpiar
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-${CHROME_VERSION}_current_amd64.deb -O /tmp/chrome.deb && \
    apt-get update && apt-get install -y /tmp/chrome.deb --no-install-recommends && \
    rm /tmp/chrome.deb && \
    rm -rf /var/lib/apt/lists/*

# Establecer la variable de entorno para la ubicación del binario de Chrome
ENV CHROME_BIN=/usr/bin/google-chrome-stable

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero para aprovechar el cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
# (webdriver-manager descargará chromedriver en tiempo de ejecución si no se instala globalmente)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

# Exponer puerto si fuera necesario para alguna depuración remota (opcional)
# EXPOSE 9222

# Comando por defecto para ejecutar el scraper
CMD ["python", "scraper.py"]
