# Script de Scrapeo de Candidatos

## Propósito
Este script está diseñado para extraer (scrapear) datos de candidatos desde el sitio web `ats.pandape.com` para LinkSolution. Automatiza el proceso de inicio de sesión, navegación a través de las vacantes, y recolección de información relevante de los perfiles de los candidatos.

## Configuración

### Variables de Entorno (`.env`)
Para el correcto funcionamiento del script, es necesario configurar las credenciales de acceso al sitio `ats.pandape.com`. Esto se realiza a través de un archivo `.env` ubicado en el directorio raíz del proyecto.

El archivo `.env` debe contener las siguientes variables:
*   `USUARIO`: El correo electrónico utilizado para el inicio de sesión.
*   `CLAVE`: La contraseña para el inicio de sesión.

**Ejemplo de contenido para el archivo `.env`:**
```
USUARIO="tu_email@example.com"
CLAVE="tu_contraseña"
```

### Dependencias
Las bibliotecas de Python necesarias para ejecutar este script se listan en el archivo `requirements.txt`. Para instalarlas, ejecuta el siguiente comando en tu terminal:
```bash
pip install -r requirements.txt
```

## Ejecución
Una vez configuradas las variables de entorno y las dependencias, el script se puede ejecutar con el siguiente comando:
```bash
python scrap.py
```

## Funcionamiento
El script realiza las siguientes acciones de forma automatizada:
1.  Inicia sesión en `ats.pandape.com` utilizando las credenciales proporcionadas en el archivo `.env`.
2.  Navega a la sección de vacantes de la empresa.
3.  Recorre cada vacante listada.
4.  Para cada vacante, accede a los perfiles de los candidatos.
5.  Extrae la siguiente información de cada candidato:
    *   Nombre completo
    *   Número de teléfono (si está disponible)
    *   Enlace al CV (generalmente en formato PDF)
    *   Correo electrónico
    *   D.N.I. (Documento Nacional de Identidad, si está disponible)
    *   Dirección (si está disponible)
6.  Envía los datos recolectados a un webhook predefinido para su procesamiento o almacenamiento.

## Constantes Configurables
Algunos parámetros clave del script están definidos como constantes al inicio del archivo `scrap.py` para facilitar su modificación sin necesidad de alterar la lógica principal del código. Estas incluyen:
*   `WEBHOOK_URL`: La URL del servicio webhook al cual se envían los datos de los candidatos.
*   `MAX_CANDIDATES_PER_VACANCY`: El número máximo de candidatos a procesar por cada vacante.
*   `DATA_SOURCE`: Un identificador para la fuente de los datos (ej. "computrabajo").

Si necesitas cambiar alguno de estos parámetros, puedes hacerlo directamente editando sus valores en `scrap.py`.
