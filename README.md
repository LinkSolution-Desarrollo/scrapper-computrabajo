# Web Scraper de Candidatos - ats.pandape.com

Este proyecto es un web scraper diseñado para extraer automáticamente datos de candidatos del sitio web ats.pandape.com. Inicia sesión en la plataforma, navega a través de las vacantes de empleo y recopila información relevante de los perfiles de los candidatos.

El código ha sido modularizado para una mejor mantenibilidad y reutilización. La lógica principal se encuentra en el directorio `src`.

## Prerrequisitos

- Python 3.x
- Dependencias listadas en `requirements.txt`.
- Google Chrome.

## Configuración

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/Ezecabrera6/scrapper-computrabajo.git
    cd scrapper-computrabajo
    ```

2.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configura las variables de entorno:**
    Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:
    ```
    USUARIO="tu_usuario_de_pandape"
    CLAVE="tu_clave_de_pandape"
    # Opcional: Configuración de MinIO/S3
    MINIO_ENDPOINT="http://localhost:9000"
    MINIO_ACCESS_KEY="minioadmin"
    MINIO_SECRET_KEY="minioadmin"
    MINIO_BUCKET="curriculums"
    ```

## Ejecución

Una vez configurado el entorno, puedes ejecutar el scraper con:

```bash
python main.py
```

El script comenzará el proceso de scraping, mostrando en la consola la información que va extrayendo.

### Ejecutar para una sola vacante

También puedes ejecutar el scraper para una única vacante modificando la variable `SINGLE_VACANCY_URL` en el archivo `main_single_vacancy.py` y luego ejecutándolo:

```bash
python main_single_vacancy.py
```

## Estructura del Proyecto

- **`main.py`**: Punto de entrada principal para scrapear todas las vacantes.
- **`main_single_vacancy.py`**: Punto de entrada para scrapear una única vacante.
- **`src/`**: Directorio que contiene toda la lógica modularizada.
  - **`config.py`**: Carga y gestiona las variables de entorno y constantes.
  - **`webdriver_setup.py`**: Configura e inicializa el driver de Selenium.
  - **`utils.py`**: Funciones de ayuda (descargas, subidas a S3, etc.).
  - **`scraper/`**: Paquete con la lógica de scraping.
    - **`login.py`**: Maneja el inicio de sesión.
    - **`vacancy_scraper.py`**: Lógica para encontrar y procesar vacantes.
    - **`candidate_scraper.py`**: Lógica para extraer datos de candidatos.
- **`Dockerfile`**: Para construir y ejecutar el proyecto en un contenedor Docker.
- **`requirements.txt`**: Dependencias de Python.

## Uso con Docker

El `Dockerfile` está configurado para ejecutar `main.py`.

**Construir la imagen:**
```bash
docker build -t pandape-scraper .
```

**Ejecutar el contenedor:**
Puedes pasar las variables de entorno usando la opción `--env-file` con tu archivo `.env`.
```bash
docker run --rm --env-file .env pandape-scraper
```
