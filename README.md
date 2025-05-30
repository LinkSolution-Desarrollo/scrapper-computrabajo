# Scraper de Empleos de Computrabajo

Este script de Python utiliza Selenium para extraer listados de empleos de una URL específica de Computrabajo (enfocada en roles de "desarrollador" en "Capital Federal, Argentina"). Extrae información como título del puesto, empresa, ubicación y un enlace directo a la publicación del empleo, y luego guarda estos datos en un archivo `job_listings.csv`.

## Características

- Extrae listados de empleos de múltiples páginas.
- Extrae: Título del Puesto, Nombre de la Empresa, Ubicación, Enlace a la Publicación del Empleo.
- Guarda los datos en `job_listings.csv`.
- Utiliza Selenium con ChromeDriver.

## Prerrequisitos

1.  **Python 3.x**: Asegúrate de tener Python 3 instalado. Puedes descargarlo desde [python.org](https://www.python.org/).
2.  **Google Chrome**: El script está configurado para usar Google Chrome. Asegúrate de tenerlo instalado.
3.  **ChromeDriver**: Necesitas descargar el ejecutable de ChromeDriver que coincida con tu versión de Google Chrome.
    *   Verifica tu versión de Chrome: Ve a `chrome://settings/help`.
    *   Descarga ChromeDriver desde el sitio oficial: [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads).
    *   **Importante**: Coloca el ejecutable `chromedriver` en un directorio que forme parte de la variable de entorno PATH de tu sistema (por ejemplo, `/usr/local/bin` en Linux/macOS, o una carpeta específica que agregues al PATH en Windows). Alternativamente, puedes modificar el script `scraper.py` para especificar la ruta a `chromedriver.exe` directamente cuando se inicializa `webdriver.Chrome()` (por ejemplo, `driver = webdriver.Chrome(executable_path='/ruta/a/tu/chromedriver')`).

## Configuración

1.  **Clona el repositorio (si aplica) o descarga los archivos.**

2.  **Crea un entorno virtual (recomendado)**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instala las dependencias**:
    Navega al directorio del proyecto en tu terminal y ejecuta:
    ```bash
    pip install -r requirements.txt
    ```
    Esto instalará `selenium`.

## Uso

1.  **Asegúrate de que ChromeDriver esté configurado correctamente** (ver Prerrequisitos).

2.  **Ejecuta el scraper**:
    Ejecuta el script desde el directorio raíz del proyecto:
    ```bash
    python scraper.py
    ```

3.  **Salida**:
    *   El script imprimirá mensajes de progreso en la consola, incluyendo el número de páginas extraídas y el total de empleos encontrados.
    *   Una vez finalizado, se creará un archivo `job_listings.csv` en el mismo directorio, conteniendo los datos de los empleos extraídos.

## Solución de Problemas

*   **`WebDriverException: 'chromedriver' executable needs to be in PATH`**: Esto significa que ChromeDriver no está instalado correctamente en tu PATH o que el script no puede encontrarlo. Verifica nuevamente las instrucciones de configuración de ChromeDriver.
*   **El scraper se detiene o encuentra errores**: Los sitios web cambian su estructura frecuentemente. Si el scraper falla, es posible que los selectores HTML en `scraper.py` necesiten ser actualizados. Puedes inspeccionar el sitio web manualmente usando las herramientas de desarrollador del navegador para encontrar los nuevos selectores.
*   **Pop-ups de cookies u otros modales**: El script incluye un intento básico para manejar los pop-ups de cookies. Si nuevos modales interfieren, es posible que se necesite agregar sus selectores específicos al script para manejarlos.
