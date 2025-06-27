# Usar una imagen base de Windows Server Core LTSC 2019
FROM mcr.microsoft.com/windows/servercore:ltsc2019

# Usar PowerShell como shell predeterminado
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

# Variables de entorno para las versiones
# NOTA: Es crucial mantener CHROME_VERSION y CHROMEDRIVER_VERSION sincronizados.
# Consultar https://googlechromelabs.github.io/chrome-for-testing/ para las versiones disponibles de Chrome y ChromeDriver.
ENV PYTHON_VERSION="3.10.11"
ENV PYTHON_HOME="C:\\Python"
# Ejemplo de una versión reciente, ajusta según sea necesario.
ENV CHROME_VERSION="126.0.6478.127" # Reemplazar con la versión de Chrome que quieres instalar
ENV CHROMEDRIVER_VERSION="126.0.6478.127" # Reemplazar con la versión de ChromeDriver correspondiente a CHROME_VERSION

# Crear directorio de herramientas
RUN New-Item -ItemType Directory -Path 'C:\tools' | Out-Null

# Instalar Python
RUN Write-Host 'Instalando Python...'; \
    $pythonInstallerUrl = ('https://www.python.org/ftp/python/{0}/python-{0}-amd64.exe' -f $env:PYTHON_VERSION); \
    Write-Host ('Descargando Python desde {0}' -f $pythonInstallerUrl); \
    Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile 'C:\tools\python_installer.exe'; \
    Write-Host 'Ejecutando instalador de Python...'; \
    Start-Process 'C:\tools\python_installer.exe' -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1 TargetDir="{0}"' -Wait; \
    Remove-Item 'C:\tools\python_installer.exe' -Force; \
    # Refrescar variables de entorno para la sesión actual
    $env:Path = [System.Environment]::GetEnvironmentVariable('PATH', [System.EnvironmentVariableTarget]::Machine); \
    Write-Host 'Python instalado.'

# Instalar Google Chrome
# Usaremos el nuevo "Chrome for Testing" que facilita la obtención de versiones específicas junto con ChromeDriver
RUN Write-Host 'Instalando Google Chrome for Testing...'; \
    $chromeZipUrl = ('https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{0}/win64/chrome-win64.zip' -f $env:CHROME_VERSION); \
    Write-Host ('Descargando Chrome for Testing desde {0}' -f $chromeZipUrl); \
    Invoke-WebRequest -Uri $chromeZipUrl -OutFile 'C:\tools\chrome-win64.zip'; \
    Write-Host 'Extrayendo Chrome for Testing...'; \
    Expand-Archive -Path 'C:\tools\chrome-win64.zip' -DestinationPath 'C:\Program Files\Google\Chrome_CFT' -Force; \
    Remove-Item 'C:\tools\chrome-win64.zip' -Force; \
    # La ruta al ejecutable será algo como C:\Program Files\Google\Chrome_CFT\chrome-win64\chrome.exe
    $env:CHROME_BIN = 'C:\Program Files\Google\Chrome_CFT\chrome-win64\chrome.exe'; \
    [Environment]::SetEnvironmentVariable('CHROME_BIN', $env:CHROME_BIN, [System.EnvironmentVariableTarget]::Machine); \
    Write-Host ('Google Chrome for Testing instalado en {0}' -f $env:CHROME_BIN)

# Instalar ChromeDriver
RUN Write-Host 'Instalando ChromeDriver...'; \
    $chromeDriverZipUrl = ('https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{0}/win64/chromedriver-win64.zip' -f $env:CHROMEDRIVER_VERSION); \
    Write-Host ('Descargando ChromeDriver desde {0}' -f $chromeDriverZipUrl); \
    Invoke-WebRequest -Uri $chromeDriverZipUrl -OutFile 'C:\tools\chromedriver-win64.zip'; \
    Write-Host 'Extrayendo ChromeDriver...'; \
    Expand-Archive -Path 'C:\tools\chromedriver-win64.zip' -DestinationPath 'C:\tools' -Force; \
    # Mover chromedriver.exe de la subcarpeta (e.g., chromedriver-win64) a C:\tools
    Move-Item -Path 'C:\tools\chromedriver-win64\chromedriver.exe' -Destination 'C:\tools\chromedriver.exe' -Force; \
    Remove-Item 'C:\tools\chromedriver-win64.zip' -Force; \
    Remove-Item -Path 'C:\tools\chromedriver-win64' -Recurse -Force; \
    # Añadir C:\tools al PATH de la máquina para que chromedriver.exe sea encontrado
    $newPath = ('C:\tools;{0}' -f [System.Environment]::GetEnvironmentVariable('PATH', [System.EnvironmentVariableTarget]::Machine)); \
    [Environment]::SetEnvironmentVariable('PATH', $newPath, [System.EnvironmentVariableTarget]::Machine); \
    # Refrescar $env:Path para la sesión actual
    $env:Path = $newPath; \
    Write-Host 'ChromeDriver instalado en C:\tools\chromedriver.exe y C:\tools añadido al PATH.'

# Establecer directorio de trabajo
WORKDIR C:\app

# Copiar requirements.txt primero para aprovechar el cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
# Asegurarse de que pip está usando el Python correcto y que el PATH está actualizado
RUN Write-Host 'Instalando dependencias de Python...'; \
    python -m pip install --no-cache-dir -r requirements.txt; \
    Write-Host 'Dependencias de Python instaladas.'

# Copiar el resto de la aplicación
COPY . .

# Comando por defecto para ejecutar el scraper
# Se usa powershell para asegurar que las variables de entorno de máquina (como PATH) se lean correctamente
CMD ["powershell", "-Command", "python scraper.py"]
