# Documentación Técnica: Scraper de Pandape (Versión Modular)

Este documento proporciona un análisis técnico detallado del scraper diseñado para extraer datos de la plataforma `ats.pandape.com`. El proyecto ha sido refactorizado a una arquitectura modular para mejorar la mantenibilidad, escalabilidad y claridad del código.

## 1. Descripción General

El proyecto es un scraper de Python que automatiza la extracción de datos de vacantes y candidatos desde Pandape. Utiliza **Selenium** para el control del navegador, **Boto3** para la integración con almacenamiento S3 (MinIO), y **Requests** para enviar datos a webhooks. La versión actual se centra en la robustez, el manejo de errores y la eficiencia.

## 2. Estructura del Proyecto

El repositorio está organizado en una estructura modular y limpia:

- **`main.py`**: Punto de entrada principal que orquesta el proceso completo de scraping para todas las vacantes.
- **`main_single_vacancy.py`**: Un script de utilidad para ejecutar el scraping en una única vacante, ideal para depuración.
- **`src/`**: Directorio que contiene toda la lógica de negocio.
    - **`config.py`**: Centraliza la gestión de variables de entorno (credenciales, URLs, timeouts) y constantes de configuración.
    - **`webdriver_setup.py`**: Configura e inicializa el driver de Selenium, asegurando un entorno de navegador consistente.
    - **`utils.py`**: Contiene funciones de ayuda reutilizables, como descargas de archivos, subidas a S3, envío a webhooks y monitoreo de rendimiento.
    - **`scraper/`**: Paquete con la lógica de scraping.
        - **`login.py`**: Maneja el proceso de inicio de sesión en la plataforma.
        - **`vacancy_scraper.py`**: Lógica para encontrar los enlaces de todas las vacantes y extraer los detalles de cada una.
        - **`candidate_scraper.py`**: Lógica para extraer datos de los candidatos de una vacante, incluyendo la gestión de CVs y la extracción de respuestas de filtros.
- **`Dockerfile`**: Define el entorno para ejecutar la aplicación en un contenedor Docker.
- **`requirements.txt`**: Lista las dependencias de Python.
- **`.env`**: Archivo (no versionado) para almacenar las credenciales y configuraciones sensibles.

## 3. Flujo de Ejecución (`main.py`)

El script principal sigue un flujo orquestado y robusto:
1.  **Limpieza Inicial**: Elimina archivos de descarga antiguos para liberar espacio.
2.  **Inicialización del WebDriver**: Llama a `webdriver_setup.get_webdriver()` para obtener una instancia de Chrome configurada.
3.  **Inicio de Sesión**: Ejecuta `login.login()` para autenticarse en la plataforma.
4.  **Obtención de Vacantes**: Llama a `vacancy_scraper.get_all_vacancy_links()` para recolectar las URLs de todas las vacantes activas.
5.  **Bucle Principal**: Itera sobre cada URL de vacante:
    a.  **Scraping de Detalles de la Vacante**: `vacancy_scraper.scrape_vacancy_details()` extrae el título, descripción y requisitos, y los envía a un webhook.
    b.  **Scraping de Candidatos**: `candidate_scraper.scrape_candidates_for_vacancy()` se encarga de procesar a todos los candidatos de esa vacante.
6.  **Cierre y Limpieza Final**: Cierra el navegador de forma segura y realiza una limpieza final de archivos temporales.

## 4. Análisis de Módulos Clave

### `src/webdriver_setup.py`
- **Gestión Automática del Driver**: Utiliza Selenium 4.6+, que gestiona `ChromeDriver` automáticamente a través de **Selenium Manager**. Esto elimina la necesidad de `webdriver-manager`.
- **Configuración Headless**: Configura Chrome para ejecutarse en modo `headless`, optimizado para servidores y contenedores Docker (`--no-sandbox`, `--disable-dev-shm-usage`).
- **Detección de Binario de Chrome**: Busca automáticamente la ruta del ejecutable de Chrome en sistemas Windows y Linux, proporcionando flexibilidad entre entornos locales y de producción.

### `src/scraper/candidate_scraper.py`
Este es uno de los módulos más complejos y cuenta con varias características avanzadas:
- **Scroll Inteligente (`_scroll_to_load_all_candidates`)**: Para cargar listas dinámicas de candidatos, el script no hace un scroll ciego. Primero, intenta leer el número total de candidatos inscritos y luego hace scroll hasta que el número de elementos visibles coincide, con un mecanismo para detectar si el scroll se ha atascado.
- **Extracción Robusta de DNI**: Utiliza expresiones regulares para buscar el DNI del candidato en la sección de nacionalidad, manejando diferentes formatos (`D.N.I.`, `NIF`, etc.).
- **Manejo de Modales (`_extract_candidate_details`)**: Para extraer las respuestas a las preguntas de filtro, el script:
    1.  Hace clic en la pestaña "Resultados".
    2.  Hace clic en el enlace "Ver respuestas" para abrir un modal.
    3.  Espera a que el contenido del modal sea visible.
    4.  Extrae las preguntas y respuestas.
    5.  Cierra el modal y espera a que desaparezca para continuar.
- **Navegación Segura**: En lugar de depender de `driver.back()` (que a menudo causa errores `StaleElementReferenceException`), el script vuelve a cargar la URL de la vacante o del candidato cuando necesita regresar, asegurando un estado de página predecible.

### `src/utils.py`
- **Funciones Seguras (`safe_extract_*`)**: Extraen texto, atributos o HTML de elementos web, pero devuelven un valor por defecto si el elemento no se encuentra, evitando que el scraper se detenga por cambios menores en la web.
- **Descargas con Sesión (`download_file`)**: Pasa las cookies de la sesión de Selenium a `requests` para descargar archivos (CVs), manteniendo la autenticación sin necesidad de que el navegador gestione la descarga directamente.
- **Subida a S3 (`upload_to_s3`)**: Se conecta a un endpoint compatible con S3 (como MinIO) y sube el CV, usando el DNI del candidato como nombre de archivo para evitar duplicados y facilitar la búsqueda.
- **Manejo de reintentos y timeouts**: Las funciones de red (`download_file`, `upload_to_s3`, `send_to_webhook`) incluyen lógica de reintentos con esperas exponenciales para manejar fallos temporales de red.

## 5. Guía de Configuración y Ejecución

### a. Entorno Local
1.  **Prerrequisitos**: Python 3.8+, Google Chrome.
2.  **Clonar Repositorio**: `git clone https://github.com/Ezecabrera6/scrapper-computrabajo.git`
3.  **Instalar Dependencias**: `pip install -r requirements.txt`.
4.  **Configurar `.env`**: Crea un archivo `.env` en la raíz del proyecto y añade las credenciales y endpoints necesarios (ver `README.md`).
5.  **Ejecutar**:
    - Para todas las vacantes: `python main.py`
    - Para una sola vacante: `python main_single_vacancy.py` (requiere configurar la URL en el propio archivo).

### b. Ejecución con Docker
1.  **Prerrequisitos**: Docker Desktop.
2.  **Configurar `.env`**: Asegúrate de que el archivo `.env` está presente en la raíz.
3.  **Construir Imagen**: `docker build -t pandape-scraper .`
4.  **Ejecutar Contenedor**: `docker run --rm --env-file .env pandape-scraper`

## 6. Integraciones Externas

### a. Endpoints de Webhook
- **URL Base**: Configurable en `src/config.py`.
- **`/webhook/vacant` (POST)**: Envía los detalles de cada vacante.
- **`/webhook/insert` (POST)**: Envía los datos de cada candidato procesado.

### b. Almacenamiento de Objetos (MinIO/S3)
- **Propósito**: Almacenamiento persistente y centralizado de los CVs.
- **Configuración**: A través de variables de entorno (`MINIO_*` en el archivo `.env`).
- **Proceso**: El script descarga el CV, se conecta a MinIO y lo sube. Si la subida es exitosa y `KEEP_LOCAL_FILES` es `False`, el archivo local se elimina para ahorrar espacio.