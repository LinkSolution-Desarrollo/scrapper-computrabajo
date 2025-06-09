# Web Scraper de Candidatos - ats.pandape.com

Este script es un web scraper diseñado para extraer automáticamente datos de candidatos del sitio web ats.pandape.com. Inicia sesión en la plataforma, navega a través de las vacantes de empleo y recopila información relevante de los perfiles de los candidatos.

## Prerrequisitos

Antes de ejecutar el script, asegúrate de tener instalado lo siguiente:

- Python 3.x
- Las siguientes bibliotecas de Python:
  - `selenium`
  - `requests`
  - `python-dotenv`
  - `webdriver-manager`

Puedes instalar estas dependencias usando pip:
```bash
pip install selenium requests python-dotenv webdriver-manager
```
O, si existe un archivo `requirements.txt` (como en este repositorio), puedes instalar todas las dependencias de una vez:
```bash
pip install -r requirements.txt
```
- Google Chrome (ya que el script utiliza ChromeDriver).

## Configuración

1.  **Clona el repositorio (si aún no lo has hecho):**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd <NOMBRE_DEL_DIRECTORIO_DEL_REPOSITORIO>
    ```
    *Reemplaza `<URL_DEL_REPOSITORIO>` con la URL real del repositorio y `<NOMBRE_DEL_DIRECTORIO_DEL_REPOSITORIO>` con el nombre del directorio que se crea al clonarlo.*

2.  **Instala las dependencias:**
    Como se mencionó en los prerrequisitos, puedes instalar las dependencias usando el archivo `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configura las variables de entorno:**
    El script necesita credenciales para iniciar sesión en `ats.pandape.com`. Estas se configuran mediante variables de entorno.
    Crea un archivo llamado `.env` en la raíz del proyecto con el siguiente contenido:
    ```
    USUARIO="tu_usuario_de_pandape"
    CLAVE="tu_clave_de_pandape"
    ```
    Reemplaza `"tu_usuario_de_pandape"` y `"tu_clave_de_pandape"` con tus credenciales reales. El script utiliza `Flor.leyva@linksolution.com.ar` y `Febrero2023` como ejemplo en el código, pero es una **mejor práctica** gestionarlos a través de variables de entorno para evitar exponerlos directamente en el código.

## Ejecución

Una vez que hayas configurado el entorno y las variables de entorno, puedes ejecutar el script con el siguiente comando:

```bash
python scrap.py
```

El script comenzará el proceso de scraping, abriendo una ventana del navegador (a menos que se configure en modo headless) y mostrando en la consola la información que va extrayendo.

## Funcionamiento del Script

El script realiza las siguientes acciones:

1.  **Inicio de Sesión:** Abre el navegador y navega a `https://ats.pandape.com/Company/Vacancy`. Luego, utiliza las credenciales (obtenidas del archivo `.env` o directamente del código si no se configura el `.env`) para iniciar sesión.
2.  **Aceptación de Cookies:** Si aparece un banner de cookies, el script intentará hacer clic en el botón para aceptarlas.
3.  **Búsqueda de Vacantes:** Una vez dentro, busca todos los enlaces que corresponden a las diferentes vacantes de empleo publicadas.
4.  **Iteración por Vacante:** Recorre cada uno de los enlaces de vacantes encontrados.
5.  **Extracción de Datos del Candidato:** Dentro de cada vacante:
    *   Identifica y hace clic en los perfiles de los candidatos (hasta un máximo de 100 candidatos por vacante o el total disponible si es menor).
    *   Para cada candidato, intenta extraer la siguiente información:
        *   Nombre completo.
        *   Número de teléfono (generalmente un enlace de WhatsApp).
        *   Enlace al CV (generalmente un archivo PDF).
        *   Dirección de correo electrónico.
        *   D.N.I. (Documento Nacional de Identidad).
        *   Dirección física.
    *   La información extraída se imprime en la consola.
6.  **Envío de Datos a Webhook:** Después de extraer los datos de un candidato, el script los formatea en un objeto JSON y los envía mediante una solicitud POST al siguiente endpoint: `http://10.20.62.94:5678/webhook/insert`. Se incluye un campo `source` con el valor `computrabajo` en los datos enviados.
7.  **Navegación y Repetición:** El script vuelve a la página de la vacante para procesar al siguiente candidato y, una vez que termina con todos los candidatos de una vacante, pasa a la siguiente vacante.
8.  **Finalización:** Una vez que se han procesado todas las vacantes y sus candidatos, el script cierra el navegador.

**Nota sobre el Webhook:** El script está configurado para enviar datos a una dirección IP local (`http://10.20.62.94:5678/webhook/insert`). Asegúrate de que este servicio esté disponible y accesible desde la máquina donde se ejecuta el script si deseas que esta funcionalidad opere correctamente.

## Uso con Docker (Opcional)

Este repositorio incluye un `Dockerfile` que permite construir una imagen de Docker y ejecutar el script en un entorno containerizado. Esto puede simplificar la gestión de dependencias y asegurar la portabilidad del script.

**Construir la imagen:**

```bash
docker build -t nombre-de-tu-imagen .
```

**Ejecutar el contenedor:**

Para ejecutar el contenedor, necesitarás pasarle las variables de entorno. Puedes hacerlo de varias maneras, por ejemplo, usando la opción `-e` o un archivo de entorno.

Usando la opción `-e`:
```bash
docker run --rm \
  -e USUARIO="tu_usuario_de_pandape" \
  -e CLAVE="tu_clave_de_pandape" \
  nombre-de-tu-imagen
```

O creando un archivo `docker.env` con el contenido:
```
USUARIO=tu_usuario_de_pandape
CLAVE=tu_clave_de_pandape
```
Y luego ejecutando:
```bash
docker run --rm --env-file docker.env nombre-de-tu-imagen
```

**Nota:** El `Dockerfile` proporcionado está configurado para instalar Google Chrome y ChromeDriver, que son necesarios para que Selenium funcione. Asegúrate de que la red del contenedor pueda acceder al endpoint del webhook (`http://10.20.62.94:5678`) si es necesario. Si el webhook es un servicio local en tu máquina anfitriona, podrías necesitar configurar la red de Docker (por ejemplo, usando `host.docker.internal` en lugar de la IP directa en el script, o configuraciones de red específicas).
