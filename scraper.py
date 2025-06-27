# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import requests
import re
import os
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager # Importado
import time
import boto3
from urllib.parse import urlparse
from boto3.session import Config

def safe_extract_text(driver, by, value, default="No encontrado"):
    try:
        return driver.find_element(by, value).text.strip()
    except Exception:
        return default

def safe_extract_attribute(driver, by, value, attribute, default="No encontrado"):
    try:
        return driver.find_element(by, value).get_attribute(attribute)
    except Exception:
        return default

def download_file(driver, url, local_folder="downloads"): # Pasamos driver como argumento
    os.makedirs(local_folder, exist_ok=True)
    filename = os.path.basename(urlparse(url).path) or f"cv_{int(time.time())}.pdf"
    local_path = os.path.join(local_folder, filename)

    try:
        s = requests.Session()
        # Pasar cookies de Selenium a requests
        for cookie in driver.get_cookies(): # driver debe estar definido y ser accesible aquí
            s.cookies.set(cookie['name'], cookie['value'])

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36", # Podríamos usar el mismo user-agent de las options de Chrome
            "Referer": driver.current_url
        }

        response = s.get(url, headers=headers)
        response.raise_for_status()

        with open(local_path, "wb") as f:
            f.write(response.content)

        print(f" Descargado: {filename}")
        return local_path
    except Exception as e:
        print(f" Error al descargar {url}: {e}")
        return None

# driver global para que download_file pueda acceder a él si no se pasa como argumento.
# Sin embargo, es mejor práctica pasarlo como argumento. Modifiqué download_file para aceptarlo.
driver = None

def upload_to_s3(local_path, nombre="sin_nombre", dni="sin_dni"):
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=os.getenv("MINIO_ENDPOINT"),
            aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
            region_name='us-east-1', # Ajusta según tu región de MinIO si es diferente
            config=Config(signature_version='s3v4', s3={'addressing_style': 'path'})
        )

        bucket = os.getenv("MINIO_BUCKET")
        extension = os.path.splitext(local_path)[1] or ".pdf"
        # Asegurarse que DNI no tenga caracteres inválidos para nombres de archivo S3 si es necesario
        # Por ahora, asumimos que el DNI es un identificador simple.
        filename = f"{dni.replace('.', '').replace(' ', '_')}{extension}" # Limpieza básica del DNI para nombre de archivo

        with open(local_path, "rb") as f:
            s3.upload_fileobj(f, bucket, filename)

        print(f" Subido a MinIO: {filename}")
    except Exception as e:
        print(f" Error al subir a MinIO: {e}")

# Cargar variables del entorno
load_dotenv()
usuario = os.environ.get("USUARIO")
clave = os.environ.get("CLAVE")

# Configuración de Chrome
options = Options()
chrome_bin_path = os.getenv("CHROME_BIN")
if chrome_bin_path:
    options.binary_location = chrome_bin_path
else:
    # Intentar una ruta común en Windows si CHROME_BIN no está seteado, aunque el Dockerfile lo setea.
    # Esto es más para ejecución local fuera de Docker si es necesario.
    default_chrome_paths = [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files\\Google\\Chrome_CFT\\chrome-win64\\chrome.exe" # Para Chrome for Testing
    ]
    for path in default_chrome_paths:
        if os.path.exists(path):
            options.binary_location = path
            break
    if not (hasattr(options, 'binary_location') and options.binary_location): # Comprobar si se estableció
        # Si CHROME_BIN no está seteado, intentar una ruta común de Linux si estamos en un entorno tipo Linux
        # (esto es más para ejecuciones locales fuera de Docker, ya que Dockerfile lo setea)
        if os.name == 'posix': # 'posix' para Linux/macOS
            default_linux_chrome_path = "/usr/bin/google-chrome-stable"
            if os.path.exists(default_linux_chrome_path):
                options.binary_location = default_linux_chrome_path
                print(f" CHROME_BIN no configurado, usando ruta por defecto de Linux: {default_linux_chrome_path}")
            else:
                print(" CHROME_BIN no está configurado y no se encontró Chrome en rutas predeterminadas (Windows/Linux).")
        else:
            print(" CHROME_BIN no está configurado y no se encontró Chrome en rutas predeterminadas de Windows.")


options.add_argument("--headless")
options.add_argument("--no-sandbox") # Necesario para ejecutar como root en contenedores Docker Linux
options.add_argument("--disable-dev-shm-usage") # Necesario para evitar problemas de recursos en Docker
options.add_argument("--disable-gpu") # Recomendado para entornos headless/contenedores
options.add_argument("--disable-extensions")
# options.add_argument("--remote-debugging-port=9222") # Descomentar solo si se necesita para depuración
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36") # User agent genérico para Linux

# Usar webdriver-manager para gestionar ChromeDriver
# Esto descargará automáticamente el chromedriver correcto si no está presente o si el del PATH no es compatible.
# Si el Dockerfile ya ha puesto un chromedriver compatible en el PATH (C:\tools),
# webdriver-manager podría usarlo.
try:
    print(" Configurando ChromeDriver usando webdriver-manager...")
    # Especificar la ruta al ejecutable de Chrome para que webdriver-manager descargue el driver correcto
    # si options.binary_location está configurado.
    chrome_driver_manager_path_arg = None
    if hasattr(options, 'binary_location') and options.binary_location and os.path.exists(options.binary_location):
        chrome_driver_manager_path_arg = options.binary_location

    # Determinar chrome_type basado en la ruta del binario si existe
    chrome_type_param = None # Default to None, letting ChromeDriverManager infer
    if chrome_driver_manager_path_arg:
        if "chrome-for-testing" in chrome_driver_manager_path_arg.lower() or \
           "cft" in chrome_driver_manager_path_arg.lower() :
             chrome_type_param = "chromium"
        # else: let it be None or "google-chrome" by default based on webdriver-manager's own logic

    service = Service(ChromeDriverManager(path=chrome_driver_manager_path_arg, chrome_type=chrome_type_param).install())
    print(" ChromeDriver configurado.")
except Exception as e:
    print(f" Error configurando ChromeDriver con webdriver-manager: {e}")
    print("Falling back to default ChromeDriver in PATH (esperado en C:\\tools\\chromedriver.exe)")
    # Fallback a la ruta esperada si webdriver-manager falla (aunque no debería)
    # o si se prefiere usar explícitamente el del Dockerfile.
    # El Dockerfile ya añade C:\tools al PATH, por lo que chromedriver.exe debería ser encontrado.
    service = Service() # Selenium buscará en el PATH

driver = webdriver.Chrome(service=service, options=options)

try:
    driver.get("https://ats.pandape.com/Company/Vacancy?Pagination[PageNumber]=1&Pagination[PageSize]=1000&Order=1&IdsFilter=0&RecruitmentType=0")
    time.sleep(5)

    driver.find_element(By.ID, "Username").send_keys(usuario)
    driver.find_element(By.ID, "Password").send_keys(clave)
    driver.find_element(By.ID, "btLogin").click()
    time.sleep(10) # Espera para login y redirección

    try:
        # Intentar hacer clic en el botón de cookies si aparece
        driver.find_element(By.ID, "AllowCookiesButton").click()
        time.sleep(2)
    except NoSuchElementException:
        print(" No se encontró el botón de cookies o no fue necesario.")
        pass # Continuar si no hay botón de cookies

    links = driver.find_elements(By.CSS_SELECTOR, "a.font-xl.fw-900.lh-120")
    hrefs = [link.get_attribute("href") for link in links]
    print(f" Encontradas {len(hrefs)} vacantes.")

    for href_idx, href in enumerate(hrefs):
        print(f"\nProcessing vacancy {href_idx + 1}/{len(hrefs)}: {href}")
        driver.get(href)
        time.sleep(3) # Espera para que cargue la página de la vacante

        # ---------- DATOS DE LA VACANTE DESDE VISTA PREVIA ----------
        try:
            preview_btn = driver.find_element(By.CSS_SELECTOR, "a[title='Vista previa']")
            preview_href = preview_btn.get_attribute("href")
            driver.execute_script("window.open(arguments[0]);", preview_href)
            driver.switch_to.window(driver.window_handles[1]) # Cambiar a la nueva pestaña
            time.sleep(3) # Espera para que cargue la vista previa

            titulo = safe_extract_text(driver, By.CSS_SELECTOR, "h1.fw-600.color-title")
            # Ajustar selectores si la estructura de la vista previa es diferente
            descripcion_elements = driver.find_elements(By.CSS_SELECTOR, "div.order-1 > div.mb-20")
            descripcion = "\n".join([elem.text for elem in descripcion_elements if elem.text.strip()]) if descripcion_elements else "No encontrado"

            requisitos_div = driver.find_elements(By.XPATH, "//h3[contains(text(), 'Requisitos')]/following-sibling::div[1]")
            requisitos = requisitos_div[0].text.strip() if requisitos_div else safe_extract_text(driver, By.CSS_SELECTOR, "div#Requirements") # Fallback

            valorado_div = driver.find_elements(By.XPATH, "//h3[contains(text(), 'Valorado')]/following-sibling::div[1]")
            valorado = valorado_div[0].text.strip() if valorado_div else safe_extract_text(driver, By.CSS_SELECTOR, "div#Valued") # Fallback


            print("\n--- VACANTE ---")
            print(f"Título: {titulo}")
            requisitos_preview = (requisitos.replace('\n', ' ')[:100]) if requisitos != "No encontrado" else "No encontrado"
            valorado_preview = (valorado.replace('\n', ' ')[:100]) if valorado != "No encontrado" else "No encontrado"
            print(f"Requisitos (primeros 100 chars): {requisitos_preview}")
            print(f"Valorado (primeros 100 chars): {valorado_preview}")

            data_vacante = {
                "titulo": titulo,
                "descripcion": descripcion,
                "requisitos": requisitos,
                "valorado": valorado,
                "source": "pandape" # Fuente de la vacante
            }

            try:
                # Asegúrate que esta URL es accesible desde el contenedor
                r = requests.post("http://10.20.62.94:5678/webhook/vacant", json=data_vacante, timeout=10)
                print(f"API Vacante: {' Enviada' if r.status_code == 200 else f' Error {r.status_code}: {r.text}'}")
            except Exception as e:
                print(f" Error al enviar vacante a API: {e}")

            driver.close() # Cerrar la pestaña de vista previa
            driver.switch_to.window(driver.window_handles[0]) # Volver a la pestaña principal
        except Exception as e:
            print(f" No se pudo procesar la vista previa de la vacante: {e}")
            # Si la vista previa falla, asegurarse de estar en la ventana correcta si se abrió una nueva
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])


        # ---------- CANDIDATOS ----------
        vacante_nombre_pagina = safe_extract_text(driver, By.CSS_SELECTOR, "div.secondary-bar-title span.lh-140") # Nombre de la vacante en la página de candidatos
        candidatos_links = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
        total_candidatos_en_pagina = len(candidatos_links)
        print(f" Encontrados {total_candidatos_en_pagina} candidatos para la vacante '{vacante_nombre_pagina}'.")

        # Limitar el número de candidatos a procesar si es necesario (ej. MAX_CANDIDATOS_POR_VACANTE)
        # total_a_procesar = min(100, total_candidatos_en_pagina)
        total_a_procesar = total_candidatos_en_pagina # Procesar todos los encontrados

        for i in range(total_a_procesar):
            # Volver a encontrar los elementos para evitar StaleElementReferenceException
            candidatos_actualizados = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
            if i >= len(candidatos_actualizados):
                print(f" No se pudo encontrar el candidato #{i+1}, posiblemente la página cambió.")
                break

            try:
                candidato_link_element = candidatos_actualizados[i]
                # Guardar el texto del link (nombre del candidato) antes de hacer clic
                nombre_candidato_link = candidato_link_element.text.strip()
                print(f"\nProcesando candidato {i + 1}/{total_a_procesar}: {nombre_candidato_link}")

                candidato_link_element.click()
                time.sleep(3) # Espera para que cargue el detalle del candidato

                # Extracción de datos del candidato
                nombre = safe_extract_text(driver, By.CSS_SELECTOR, "div.font-3xl.lh-120.fw-600.text-capitalize")
                numero = safe_extract_text(driver, By.CSS_SELECTOR, "a.js_WhatsappLink")
                cv_url = safe_extract_attribute(driver, By.CSS_SELECTOR, "a[title$='.pdf']", "href") # Asumimos que siempre es .pdf
                email = safe_extract_text(driver, By.CSS_SELECTOR, "a.text-nowrap.mb-05 span")

                dni = "No encontrado"
                try:
                    # Buscar DNI de forma más robusta
                    nationality_section_elements = driver.find_elements(By.XPATH, "//div[span[contains(., 'Nacionalidad') or contains(., 'Nationality')]]")
                    if nationality_section_elements:
                        nationality_section_text = nationality_section_elements[0].text
                        # Patrones comunes para DNI en España (puede necesitar ajustes para otros formatos/países)
                        dni_match = re.search(r"(D\.N\.I\.?|NIF|NIE)\s*[:\-]?\s*([A-Z0-9\-\.]{7,12})", nationality_section_text, re.IGNORECASE)
                        if dni_match:
                            dni = dni_match.group(2).strip().replace('.', '').replace('-', '')
                        else: # Fallback si no encuentra DNI específico, buscar un número largo
                            numbers_in_section = re.findall(r'\b\d{7,9}[A-Za-z]?\b', nationality_section_text)
                            if numbers_in_section:
                                dni = numbers_in_section[0]
                except Exception as e_dni:
                    print(f" No se pudo extraer DNI automáticamente: {e_dni}")
                    pass

                local_cv_path = None
                if cv_url != "No encontrado":
                    print(f" Intentando descargar CV desde: {cv_url}")
                    local_cv_path = download_file(driver, cv_url) # Pasar driver a download_file
                    if local_cv_path and os.getenv("MINIO_ENDPOINT"): # Solo subir si hay endpoint de MinIO
                        upload_to_s3(local_cv_path, nombre=nombre, dni=dni if dni != "No encontrado" else f"sindni_{int(time.time())}")
                else:
                    print(" CV no disponible para este candidato.")


                respuestas_filtro_texto = "No disponibles"
                try:
                    resultados_tab_elements = driver.find_elements(By.ID, "ResultsTabAjax")
                    if not resultados_tab_elements: # Si no se encuentra por ID (a veces pasa con elementos AJAX)
                        resultados_tab_elements = driver.find_elements(By.XPATH, "//a[contains(@href,'#ResultsTabAjax')]")


                    if resultados_tab_elements:
                        resultados_tab = resultados_tab_elements[0]
                        # Hacer clic solo si no está activo
                        parent_li = resultados_tab.find_element(By.XPATH, "./parent::li")
                        if "active" not in parent_li.get_attribute("class"):
                            driver.execute_script("arguments[0].click();", resultados_tab)
                            time.sleep(2) # Espera a que cargue el contenido AJAX

                        ver_respuestas_links = driver.find_elements(By.CSS_SELECTOR, "a.js_lnkQuestionnaireWeightedDetail")
                        if ver_respuestas_links:
                            driver.execute_script("arguments[0].click();", ver_respuestas_links[0])
                            time.sleep(2) # Esperar modal

                            modal_content = driver.find_element(By.ID, "divResult") # Contenedor del modal
                            preguntas_respuestas_items = modal_content.find_elements(By.CSS_SELECTOR, "ol.pl-50 > li")

                            respuestas_list = []
                            for item_idx, item in enumerate(preguntas_respuestas_items):
                                try:
                                    pregunta = item.find_element(By.XPATH, "./span").text.strip()
                                    respuesta_elements = item.find_elements(By.XPATH, "./div/span")
                                    respuesta = respuesta_elements[0].text.strip() if respuesta_elements else "Respuesta no visible"
                                    respuestas_list.append(f"{pregunta}: {respuesta}")
                                except Exception as e_qa:
                                    print(f"Error extrayendo pregunta/respuesta #{item_idx}: {e_qa}")
                                    respuestas_list.append("Error al extraer Q&A")

                            respuestas_filtro_texto = " | ".join(respuestas_list)

                            # Cerrar modal
                            try:
                                close_button = modal_content.find_element(By.CSS_SELECTOR, "button.close")
                                driver.execute_script("arguments[0].click();", close_button)
                                time.sleep(1)
                            except Exception as e_close_modal:
                                print(f" No se pudo cerrar el modal de respuestas: {e_close_modal}")
                        else:
                            print(" No se encontró el enlace 'Ver respuestas del cuestionario'.")
                    else:
                        print(" No se encontró la pestaña de Resultados (ResultsTabAjax).")

                except NoSuchElementException:
                    print(" Pestaña de resultados o enlace de cuestionario no encontrado (NoSuchElement).")
                except Exception as e_filtro:
                    print(f" Error al obtener respuestas de filtro: {e_filtro}")
                    respuestas_filtro_texto = "Error al extraer"

                direccion_elements = driver.find_elements(By.XPATH, "//span[contains(@class, 'icon-location')]/following-sibling::span")
                direccion = direccion_elements[0].text.strip() if direccion_elements else safe_extract_text(driver, By.CSS_SELECTOR, "span.ml-20") # Fallback

                resumen = safe_extract_text(driver, By.CSS_SELECTOR, "div#Summary p.text-break-word")

                salario_deseado_elements = driver.find_elements(By.XPATH, "//div[span[contains(., 'Salario deseado') or contains(., 'Desired salary')]]/div[contains(@class, 'col-9')]/div")
                salario_deseado = salario_deseado_elements[0].text.strip() if salario_deseado_elements else "No encontrado"


                print("\n--- CANDIDATO DETALLE ---")
                print(f"Vacante en página: {vacante_nombre_pagina}")
                print(f"Nombre: {nombre}")
                print(f"Teléfono: {numero}")
                print(f"CV URL: {cv_url}")
                print(f"Email: {email}")
                print(f"DNI: {dni}")
                print(f"Dirección: {direccion}")
                resumen_preview = (resumen.replace('\n', ' ')[:100]) if resumen != "No encontrado" else "No encontrado"
                print(f"Resumen (primeros 100 chars): {resumen_preview}")
                print(f"Salario Deseado: {salario_deseado}")
                print(f"Respuestas filtro: {respuestas_filtro_texto[:200]}...") # Imprimir solo una parte

                data_candidato = {
                    "vacante": vacante_nombre_pagina, # Usar el nombre de la vacante de la página de candidatos
                    "nombre": nombre,
                    "numero": numero,
                    "curriculum_url": cv_url, # Enviar la URL del CV
                    "curriculum_descargado": os.path.basename(local_cv_path) if local_cv_path else "No descargado",
                    "email": email,
                    "dni": dni,
                    "direccion": direccion,
                    "resumen": resumen,
                    "salario_deseado": salario_deseado,
                    "respuestas_filtro": respuestas_filtro_texto,
                    "source": "pandape" # Fuente del candidato (antes decía computrabajo)
                }

                try:
                    # Asegúrate que esta URL es accesible desde el contenedor
                    r_cand = requests.post("http://10.20.62.94:5678/webhook/insert", json=data_candidato, timeout=10)
                    print(f"API Candidato: {' Enviado' if r_cand.status_code == 200 else f' Error {r_cand.status_code}: {r_cand.text}'}")
                except Exception as e_http_cand:
                    print(f" Error HTTP al enviar candidato: {e_http_cand}")

                # Volver a la lista de candidatos
                driver.back()
                time.sleep(3) # Espera para que cargue la lista de nuevo

            except Exception as e_cand_loop:
                print(f" Error procesando candidato #{i + 1} ({nombre_candidato_link if 'nombre_candidato_link' in locals() else 'Nombre desconocido'}): {e_cand_loop}")
                print("Intentando volver a la lista de candidatos...")
                try:
                    driver.back() # Intenta volver atrás en caso de error grave en el candidato
                    time.sleep(3)
                except Exception as e_back:
                    print(f" No se pudo volver atrás, intentando recargar página de vacantes: {e_back}")
                    # Es importante volver a la URL de la lista de candidatos de la vacante actual
                    current_vac_url = driver.current_url # Podría ser la URL del candidato o la lista
                    if "Candidate" in current_vac_url or "Match" in current_vac_url: # Si está en detalle de candidato
                        driver.get(href) # 'href' es la URL de la vacante (lista de sus candidatos)
                    else: # Ya está en la lista o en una URL inesperada, intentar recargar href
                         driver.get(href)
                    time.sleep(5)
                continue # Continuar con el siguiente candidato

        print("-" * 60)
        # Volver a la lista de vacantes (ya se hace al inicio del loop de vacantes con driver.get(href))
        # No es necesario driver.back() aquí, el loop externo de vacantes se encarga con driver.get(href_vacante)

finally:
    if driver:
        print(" Cerrando el navegador...")
        driver.quit()
