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

## Pandape Login Scraper (`pandape_login.py`)

This script uses Selenium to log into the Pandape ATS website.

### Prerequisites

- Python 3.x
- Google Chrome browser installed
- The necessary Python packages, as listed in `requirements.txt`. Install them using:
  ```bash
  pip install -r requirements.txt
  ```

### Setup Credentials

The script expects Pandape credentials to be set as environment variables for security. Please set the following variables in your environment:

- `PANDAPE_USERNAME`: Your Pandape username or email.
- `PANDAPE_PASSWORD`: Your Pandape password.

**Example (Linux/macOS):**
```bash
export PANDAPE_USERNAME="your_username"
export PANDAPE_PASSWORD="your_password"
```

**Example (Windows PowerShell):**
```powershell
$env:PANDAPE_USERNAME="your_username"
$env:PANDAPE_PASSWORD="your_password"
```
You might need to add these to your shell's profile file (e.g., `.bashrc`, `.zshrc`, PowerShell Profile) for them to persist across sessions.

### Running the Script

Once the prerequisites are met and credentials are set up, you can run the script:

```bash
python pandape_login.py
```

The script will attempt to log in and will keep the browser open for a few seconds for you to observe the result. It will also print status messages to the console. If errors occur, it may save a screenshot (`pandape_login_error.png`) and the page source (`pandape_login_error_source.html`) for debugging.
