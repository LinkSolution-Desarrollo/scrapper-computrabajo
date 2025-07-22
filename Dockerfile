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
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Instalar Google Chrome estable
RUN apt-get update && apt-get install -y google-chrome-stable

# Limpiar cache de apt para reducir imagen
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Crear carpeta de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . /app

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Definir variable de entorno para Chrome (Selenium usará este binario)
ENV CHROME_BIN=/usr/bin/google-chrome-stable

# Comando por defecto para ejecutar el scraper
CMD ["python", "-m", "src.main"]
