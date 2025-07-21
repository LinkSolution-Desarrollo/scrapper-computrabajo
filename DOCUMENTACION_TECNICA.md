# Documentación Técnica: Scraper de Pandape

Este documento proporciona un análisis técnico detallado del scraper diseñado para extraer datos de la plataforma `ats.pandape.com`.

## 1. Descripción General

El proyecto consiste en un script de Python que automatiza la navegación y extracción de datos de vacantes y candidatos desde Pandape. Utiliza Selenium para el control del navegador, Boto3 para la integración con almacenamiento S3 (MinIO) y Requests para enviar datos a webhooks.

## 2. Estructura del Proyecto

El repositorio está organizado de la siguiente manera:

- **`scraper.py`**: El corazón del proyecto. Este script de Python contiene toda la lógica para realizar el web scraping.
- **`Dockerfile`**: Define el entorno de contenedor para ejecutar la aplicación de forma aislada y portable.
- **`requirements.txt`**: Lista todas las dependencias de Python necesarias.
- **`.env.example`**: Un archivo de ejemplo que muestra las variables de entorno requeridas para ejecutar el script.
- **`README.md`**: Documentación general para el usuario final sobre cómo configurar y ejecutar el proyecto.
- **`downloads/`**: Directorio temporal creado por el script para almacenar los CVs descargados antes de subirlos a MinIO.

## 3. Análisis del Script Principal (`scraper.py`)

El script se puede dividir en tres componentes principales:

### a. Configuración Inicial
- **Variables de Entorno:** Carga credenciales (`USUARIO`, `CLAVE`) y configuración de MinIO desde un archivo `.env`.
- **Opciones de Selenium/Chrome:** Configura el navegador para ejecutarse en modo `headless` (sin interfaz gráfica), con argumentos optimizados para entornos Docker (`--no-sandbox`, `--disable-dev-shm-usage`).
- **WebDriver:** Utiliza `webdriver-manager` para gestionar automáticamente el `ChromeDriver` necesario, asegurando la compatibilidad con la versión de Google Chrome instalada.

### b. Funciones de Utilidad
- **`safe_extract_text()` y `safe_extract_attribute()`**: Funciones robustas que extraen datos de elementos web, devolviendo un valor por defecto si el elemento no se encuentra para evitar que el script se detenga por errores.
- **`download_file()`**: Descarga archivos (CVs) pasando las cookies de la sesión de Selenium a `requests` para mantener la autenticación.
- **`upload_to_s3()`**: Sube un archivo local a un bucket de MinIO, utilizando el DNI del candidato para generar un nombre de archivo único.

### c. Flujo de Ejecución Principal
El flujo de trabajo principal está encapsulado en un bloque `try...finally` para garantizar que el navegador se cierre correctamente.
1.  **Login:** Accede a `ats.pandape.com` con las credenciales proporcionadas.
2.  **Bucle de Vacantes:** Itera sobre cada vacante encontrada. Para cada una, abre la vista previa en una nueva pestaña, extrae los detalles y los envía a un webhook.
3.  **Bucle de Candidatos:** Dentro de cada vacante, itera sobre cada candidato.
    - **Extracción de Datos:** Navega al perfil del candidato y extrae toda la información relevante (nombre, contacto, DNI, etc.).
    - **Manejo de CVs:** Si existe un CV, lo descarga y lo sube a MinIO.
    - **Extracción de Respuestas (Modal):** Ejecuta una secuencia compleja para abrir un modal que contiene las respuestas a preguntas de filtro, las extrae y cierra el modal.
    - **Navegación Robusta:** Regresa a la lista de candidatos recargando la URL de la vacante en lugar de usar `driver.back()`, lo que previene errores de `StaleElementReferenceException`.
    - **Envío a Webhook:** Envía los datos completos del candidato a un segundo webhook.

## 4. Guía de Configuración y Ejecución

### a. Entorno Local
1.  **Prerrequisitos:** Python 3.8+ y Google Chrome.
2.  **Clonar Repositorio:** `git clone https://github.com/Ezecabrera6/scrapper-computrabajo.git`
3.  **Instalar Dependencias:** `pip install -r requirements.txt` (dentro de un entorno virtual recomendado).
4.  **Configurar `.env`:** Copia `.env.example` a `.env` y rellena tus credenciales.
5.  **Ejecutar:** `python scraper.py`

### b. Ejecución con Docker (Recomendado)
1.  **Prerrequisitos:** Docker Desktop.
2.  **Configurar `.env`:** Crea el archivo `.env` con tus credenciales.
3.  **Construir Imagen:** `docker build -t pandape-scraper .`
4.  **Ejecutar Contenedor:** `docker run --rm --env-file .env pandape-scraper`

## 5. Integraciones Externas

### a. Endpoints de Webhook
El script envía datos JSON a los siguientes endpoints (URL base: `http://10.20.62.94:5678`):

- **`/webhook/vacant` (POST):** Para datos de vacantes.
  ```json
  {"titulo": "...", "descripcion": "...", "requisitos": "...", "valorado": "...", "source": "pandape"}
  ```
- **`/webhook/insert` (POST):** Para datos de candidatos.
  ```json
  {"vacante": "...", "nombre": "...", "email": "...", "dni": "...", "curriculum_url": "...", ...}
  ```

### b. Almacenamiento de Objetos (MinIO)
- **Propósito:** Almacenar los CVs de los candidatos de forma persistente.
- **Configuración:** Se realiza a través de las siguientes variables de entorno:
    - `MINIO_ENDPOINT`: URL del servidor MinIO.
    - `MINIO_ACCESS_KEY`: Clave de acceso.
    - `MINIO_SECRET_KEY`: Clave secreta.
    - `MINIO_BUCKET`: Nombre del bucket (debe existir previamente).
- **Proceso:** El script descarga el CV, se conecta a MinIO con `boto3` y lo sube, nombrando el archivo con el DNI del candidato.
