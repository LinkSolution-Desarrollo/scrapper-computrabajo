# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

def upload_to_s3(local_path, dni=None):
    if not dni or dni == "No encontrado":
        print(" ⚠️ CV sin DNI, no se sube a MinIO")
        return

    try:
        s3 = boto3.client(
            's3',
            endpoint_url=os.getenv("MINIO_ENDPOINT"),
            aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
            region_name='us-east-1',
            config=Config(signature_version='s3v4', s3={'addressing_style': 'path'})
        )

        bucket = os.getenv("MINIO_BUCKET")
        extension = os.path.splitext(local_path)[1] or ".pdf"

        safe_dni = dni.replace('.', '').replace(' ', '_')
        filename = f"{safe_dni}{extension}"

        with open(local_path, "rb") as f:
            s3.upload_fileobj(f, bucket, filename)

        print(f" ✅ Subido a MinIO: {filename}")
    except Exception as e:
        print(f" ❌ Error al subir a MinIO: {e}")

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
#options.add_argument("--remote-debugging-port=9222") # Descomentar solo si se necesita para depuración
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
    driver.get("https://ats.pandape.com/Company/Vacancy?Pagination[PageNumber]=1&Pagination[PageSize]=1000&Order=1&IdsFilter=2&RecruitmentType=0")
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

        titulo_vacante_actual = "No encontrado"  # Inicializar variable para el título

        # ---------- DATOS DE LA VACANTE DESDE EDITAR VACANTE ----------
        try:
            # Hacer clic en el botón de editar vacante
            edit_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='btnEditVacancy']")))
            edit_btn.click()

            # Esperar a que la página de edición cargue, buscando el input del título
            wait_edit = WebDriverWait(driver, 10)
            job_input_element = wait_edit.until(EC.presence_of_element_located((By.XPATH, "//*[@id='Job']")))

            # Extraer título y complemento
            titulo_base = job_input_element.get_attribute('value').strip()
            complemento = driver.find_element(By.XPATH, "//*[@id='JobComplement']").get_attribute('value').strip()

            if titulo_base and complemento:
                titulo = f"{titulo_base} - {complemento}"
            elif titulo_base:
                titulo = titulo_base
            else:
                titulo = "No encontrado"

            titulo_vacante_actual = titulo

            # Los otros campos no se extraen desde esta vista según el requerimiento.
            descripcion = "No encontrado"
            requisitos = "No encontrado"
            valorado = "No encontrado"

            print("\n--- VACANTE ---")
            print(f"Título: {titulo}")

            data_vacante = {
                "titulo": titulo,
                "descripcion": descripcion,
                "requisitos": requisitos,
                "valorado": valorado,
                "source": "pandape" # Fuente de la vacante
            }

            try:
                # Enviar a nuevo webhook
                r = requests.post("http://10.20.62.101:5678/webhook/editar_vacante", json=data_vacante, timeout=10)
                print(f"API Editar Vacante: {' Enviada' if r.status_code == 200 else f' Error {r.status_code}: {r.text}'}")
            except Exception as e:
                print(f" Error al enviar vacante a API: {e}")

            # Volver a la página de la vacante para procesar candidatos
            print(f" Volviendo a la lista de candidatos para la vacante: {href}")
            driver.get(href)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.match-link")))

        except Exception as e:
            print(f" ⚠️ No se pudo procesar la edición de la vacante: {e}.")
            # FALLBACK: Intentar extraer el título desde la página de candidatos
            try:
                print(" ℹ️ Intentando extraer título desde la página de candidatos (fallback)...")
                wait_fallback = WebDriverWait(driver, 5) # Short wait
                fallback_selector = (By.CSS_SELECTOR, "div.secondary-bar-title span.lh-140")
                fallback_element = wait_fallback.until(EC.presence_of_element_located(fallback_selector))
                titulo_fallback = fallback_element.text.strip()
                if titulo_fallback:
                    titulo_vacante_actual = titulo_fallback
                    print(f" ✅ Título encontrado con fallback: {titulo_vacante_actual}")
                else:
                    print(" ❌ El título de fallback estaba vacío.")
            except Exception as e_fallback:
                print(f" ❌ Fallback para obtener el título también falló: {e_fallback}")


        # ---------- CANDIDATOS (CON SCROLL INTELIGENTE) ----------
        # Bucle de scroll mejorado: extrae el número total de candidatos y hace scroll
        # hasta que ese número se alcanza, con mecanismos de seguridad.
        print(" Iniciando scroll inteligente para cargar todos los candidatos...")

        total_candidatos_esperados = 0
        try:
            # El selector apunta a la pestaña que contiene el texto "Inscriptos (X)"
            # Se usa un selector XPath más específico para encontrar el span por su texto.
            inscriptos_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Inscriptos')]"))
            )
            inscriptos_texto = inscriptos_element.text
            match = re.search(r'\((\d+)\)', inscriptos_texto)
            if match:
                total_candidatos_esperados = int(match.group(1))
                print(f" Total de candidatos esperados según la página: {total_candidatos_esperados}")
            else:
                print(" No se pudo extraer el número de la pestaña 'Inscriptos'. Se usará el método de scroll tradicional.")
        except Exception as e:
            print(f" No se pudo encontrar el total de 'Inscriptos' ({e}). Se usará el método de scroll tradicional.")

        last_count = -1
        stuck_counter = 0 # Contador para evitar bucles infinitos
        while True:
            candidatos_visibles = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
            current_count = len(candidatos_visibles)
            print(f"  - Encontrados {current_count}/{total_candidatos_esperados if total_candidatos_esperados > 0 else '??'} candidatos.")

            # Condición de salida principal: se alcanzó el total esperado.
            if total_candidatos_esperados > 0 and current_count >= total_candidatos_esperados:
                print(" Se ha alcanzado el número total de candidatos esperados. Scroll finalizado.")
                break

            # Condición de salida de seguridad: si el número no aumenta, es un fallback.
            if current_count == last_count:
                stuck_counter += 1
                print(f"  - El número de candidatos no aumenta (intento {stuck_counter}/3).")
                if stuck_counter >= 3:
                    print(" El número de candidatos no ha aumentado en 3 intentos. Se asume que no hay más por cargar. Scroll finalizado.")
                    break
            else:
                stuck_counter = 0 # Resetear si hay progreso

            last_count = current_count

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        # Una vez finalizado el scroll, obtenemos la lista final y completa de candidatos.
        candidatos_links = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
        total_candidatos_en_pagina = len(candidatos_links)
        print(f" Encontrados {total_candidatos_en_pagina} candidatos en total para la vacante '{titulo_vacante_actual}'.")

        # Procesar todos los candidatos encontrados.
        total_a_procesar = total_candidatos_en_pagina
        print(f"Se procesarán {total_a_procesar} candidatos para esta vacante.")

        for i in range(total_a_procesar):
            print(f"\nIteración {i + 1} del bucle de candidatos.")
            # Volver a encontrar los elementos para evitar StaleElementReferenceException
            # y esperar a que estén presentes
            try:
                print(" Buscando lista actualizada de candidatos...")
                wait = WebDriverWait(driver, 10)
                candidatos_actualizados = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.match-link")))
                print(f" Encontrados {len(candidatos_actualizados)} candidatos actualizados en la página.")
            except TimeoutException:
                print(" Timeout: No se encontraron enlaces de candidatos después de esperar. Terminando vacante.")
                break
            except Exception as e:
                print(f" Error al buscar candidatos actualizados: {e}. Terminando vacante.")
                break

            if i >= len(candidatos_actualizados):
                print(f" Índice {i} fuera de rango para candidatos_actualizados (longitud: {len(candidatos_actualizados)}). Algo salió mal. Terminando vacante.")
                break

            try:
                candidato_link_element = candidatos_actualizados[i]
                
                # Guardar el texto del link (nombre del candidato) antes de hacer clic
                # Es posible que el elemento no sea visible todavía, así que intentamos obtener el atributo si el texto falla.
                try:
                    nombre_candidato_link = candidato_link_element.text.strip()
                    if not nombre_candidato_link: # Si el texto está vacío, intentar con 'data-username'
                        nombre_candidato_link = candidato_link_element.get_attribute('data-username')
                except Exception as e_text:
                    nombre_candidato_link = f"Nombre no extraíble ({e_text})"
                
                print(f" Procesando candidato {i + 1}/{total_a_procesar}: '{nombre_candidato_link}' (Elemento #{i})")

                # Hacer scroll para asegurar que el elemento esté en la vista
                try:
                    print(f" Haciendo scroll hacia el candidato: {nombre_candidato_link}")
                    driver.execute_script("arguments[0].scrollIntoView(true);", candidato_link_element)
                    time.sleep(0.5) # Pequeña pausa para que el scroll se complete
                except Exception as e_scroll:
                    print(f"  Advertencia: No se pudo hacer scroll hacia el elemento: {e_scroll}")

                # Esperar a que el elemento sea clickeable
                print(f" Esperando a que el candidato '{nombre_candidato_link}' sea clickeable...")
                # Usar el elemento original de la lista `candidatos_actualizados[i]` para la espera y el clic
                candidato_clickable = wait.until(EC.element_to_be_clickable(candidatos_actualizados[i]))
                
                print(f" Haciendo clic en candidato: {nombre_candidato_link}")
                # Usar JavaScript para hacer clic si el clic normal falla a veces
                driver.execute_script("arguments[0].click();", candidato_clickable)
                # candidato_clickable.click()
                
                # time.sleep(3) # Reemplazado por espera explícita si es necesario, o mantener si la página carga mucho JS
                # Esperar a que algún elemento distintivo de la página de detalle del candidato aparezca
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.font-3xl.lh-120.fw-600.text-capitalize")) # Selector del nombre del candidato en detalle
                    )
                    print(" Página de detalle del candidato cargada.")
                except TimeoutException:
                    print(" Timeout esperando que la página de detalle del candidato cargue. Continuando con la extracción...")


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
                        upload_to_s3(local_cv_path, dni=dni)

                else:
                    print(" CV no disponible para este candidato.")


                respuestas_filtro_texto = "No disponibles"
                wait_short = WebDriverWait(driver, 5) # Espera corta para elementos que deberían aparecer rápido
                wait_long = WebDriverWait(driver, 10) # Espera más larga para contenido AJAX o modales

                try:
                    print(" Buscando la pestaña 'Resultados'...")
                    # Intentar localizar la pestaña "Resultados"
                    # Primero por ID, que es más específico
                    resultados_tab_xpath = "//a[@id='ResultsTabAjax' or contains(@href,'#ResultsTabAjax')]" # Combina ID y href
                    
                    resultados_tab_clickable = wait_long.until(EC.element_to_be_clickable((By.XPATH, resultados_tab_xpath)))
                    
                    # Verificar si la pestaña ya está activa directamente en el enlace <a>
                    # El XPath resultados_tab_xpath ya apunta al elemento <a>
                    is_active = "active" in resultados_tab_clickable.get_attribute("class")
                    
                    if not is_active:
                        print(" La pestaña 'Resultados' no está activa. Haciendo clic...")
                        driver.execute_script("arguments[0].click();", resultados_tab_clickable)
                        # Esperar a que la pestaña se marque como activa, verificando la clase en el mismo elemento <a>
                        WebDriverWait(driver, 10).until( # Aumentar ligeramente la espera aquí por si la actualización de clase tarda
                            # Re-localizar el elemento dentro de la lambda para obtener su estado más actual
                            lambda d: "active" in d.find_element(By.XPATH, resultados_tab_xpath).get_attribute("class")
                        )
                        print(" Pestaña 'Resultados' activada.")
                    else:
                        print(" Pestaña 'Resultados' ya está activa.")

                    # Buscar el enlace para "Ver respuestas del cuestionario"
                    print(" Buscando enlace 'Ver respuestas del cuestionario' (a.js_lnkQuestionnaireWeightedDetail)...")
                    ver_respuestas_link_element = wait_long.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.js_lnkQuestionnaireWeightedDetail")))
                    print(" Enlace 'Ver respuestas del cuestionario' encontrado y clickeable. Haciendo clic...")
                    driver.execute_script("arguments[0].click();", ver_respuestas_link_element)

                    # Esperar a que el modal (divResult) sea visible
                    print(" Esperando a que el modal de resultados (divResult) sea visible...")
                    modal_content = wait_long.until(EC.visibility_of_element_located((By.ID, "divResult")))
                    print(" Modal de resultados (divResult) visible.")

                    # Esperar a que los items de preguntas/respuestas estén presentes dentro del modal
                    print(" Buscando items de preguntas/respuestas (ol.pl-50 > li) dentro del modal...")
                    # Usamos presence_of_all_elements_located para obtener una lista
                    preguntas_respuestas_items = wait_long.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#divResult ol.pl-50 > li")))
                    print(f" Encontrados {len(preguntas_respuestas_items)} items de preguntas/respuestas.")

                    if preguntas_respuestas_items:
                        respuestas_list = []
                        for item_idx, item in enumerate(preguntas_respuestas_items):
                            try:
                                pregunta = item.find_element(By.XPATH, "./span").text.strip()
                                # La respuesta está en un span dentro de un div que es hijo del li
                                respuesta_elements = item.find_elements(By.XPATH, "./div/span")
                                respuesta = respuesta_elements[0].text.strip() if respuesta_elements and respuesta_elements[0].text.strip() else "Respuesta no proporcionada"
                                respuestas_list.append(f"{pregunta}: {respuesta}")
                            except TimeoutException:
                                print(f"  Timeout extrayendo pregunta o respuesta para el item #{item_idx}.")
                                respuestas_list.append("Error al extraer Q&A individual (Timeout)")
                            except Exception as e_qa:
                                print(f"  Error extrayendo pregunta/respuesta #{item_idx}: {e_qa}")
                                respuestas_list.append("Error al extraer Q&A individual")
                        
                        if respuestas_list:
                            respuestas_filtro_texto = " | ".join(respuestas_list)
                        else:
                            respuestas_filtro_texto = "No se pudieron extraer preguntas/respuestas individuales."
                    else:
                        respuestas_filtro_texto = "No se encontraron items de preguntas/respuestas en el modal."


                    # Cerrar modal
                    try:
                        print(" Intentando cerrar el modal de resultados...")
                        # Esperar a que el botón de cierre sea clickeable
                        close_button = wait_long.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#divResult button.close")))
                        driver.execute_script("arguments[0].click();", close_button)
                        # Esperar a que el modal desaparezca (opcional pero bueno para la estabilidad)
                        wait_long.until(EC.invisibility_of_element_located((By.ID, "divResult")))
                        print(" Modal de resultados cerrado.")
                    except TimeoutException:
                        print(" Timeout esperando que el botón de cierre del modal sea clickeable o que el modal desaparezca.")
                    except Exception as e_close_modal:
                        print(f" No se pudo cerrar el modal de respuestas de forma controlada: {e_close_modal}")

                except TimeoutException as e_timeout:
                    print(f" Timeout general durante la extracción de respuestas de filtro: {e_timeout}")
                    current_url_on_error = driver.current_url
                    page_title_on_error = driver.title
                    print(f" URL actual: {current_url_on_error}, Título: {page_title_on_error}")
                    if "divResult" in str(e_timeout).lower():
                         respuestas_filtro_texto = "Error: Timeout esperando el modal de resultados."
                    elif "js_lnkQuestionnaireWeightedDetail" in str(e_timeout).lower():
                         respuestas_filtro_texto = "Error: Timeout esperando el enlace para ver respuestas."
                    elif "ResultsTabAjax" in str(e_timeout).lower():
                         respuestas_filtro_texto = "Error: Timeout esperando la pestaña de resultados."
                    else:
                         respuestas_filtro_texto = "Error: Timeout no especificado en la extracción de filtros."
                    print(f"Debug Info: TimeoutException - {str(e_timeout)}")


                except NoSuchElementException as e_no_such:
                    # Imprimir el mensaje de error completo de Selenium
                    full_error_message = f"NoSuchElementException capturada. Mensaje original de Selenium: {str(e_no_such)}"
                    print(full_error_message)
                    
                    # Guardar un mensaje de error más informativo que incluya parte del error original
                    # para el campo respuestas_filtro_texto.
                    # Tomar los primeros N caracteres del mensaje de error para no hacerlo demasiado largo.
                    detalle_error_selenium = str(e_no_such).splitlines()[0] if str(e_no_such).splitlines() else str(e_no_such) # A menudo la primera línea es la más útil
                    respuestas_filtro_texto = f"Error (NoSuchElement): {detalle_error_selenium[:150]}" # Primeros 150 chars del detalle
                    
                    print(f"Debug Info: Asignado '{respuestas_filtro_texto}' debido a NoSuchElementException.")

                except Exception as e_filtro:
                    print(f" Error general (Exception) al obtener respuestas de filtro: {type(e_filtro).__name__} - {e_filtro}")
                    respuestas_filtro_texto = f"Error general al extraer respuestas de filtro ({type(e_filtro).__name__})."
                    print(f"Debug Info: Exception type: {type(e_filtro).__name__} - {str(e_filtro)}")

                direccion_elements = driver.find_elements(By.XPATH, "//span[contains(@class, 'icon-location')]/following-sibling::span")
                direccion = direccion_elements[0].text.strip() if direccion_elements else safe_extract_text(driver, By.CSS_SELECTOR, "span.ml-20") # Fallback

                direccion = safe_extract_text(driver, By.CSS_SELECTOR, "span.js_CandidateAddress")

                resumen = safe_extract_text(driver, By.CSS_SELECTOR, "div#Summary p.text-break-word")

                salario_deseado_elements = driver.find_elements(By.XPATH, "//div[span[contains(., 'Salario deseado') or contains(., 'Desired salary')]]/div[contains(@class, 'col-9')]/div")
                salario_deseado = salario_deseado_elements[0].text.strip() if salario_deseado_elements else "No encontrado"

                # Extracción de la fuente del candidato
                xpath_fuente = "//img[contains(@src, '/images/publishers/icons/')]/following-sibling::span"
                fuente_candidato = "Fuente no especificada" # Valor por defecto
                try:
                    fuente_element = driver.find_element(By.XPATH, xpath_fuente)
                    fuente_candidato = fuente_element.text.strip() if fuente_element and fuente_element.text.strip() else "Fuente no especificada"
                except NoSuchElementException:
                    print(" No se encontró el elemento de la fuente del candidato usando XPath.")
                except Exception as e_fuente:
                    print(f" Error al extraer la fuente del candidato: {e_fuente}")

                print("\n--- CANDIDATO DETALLE ---")
                print(f"Vacante en página: {titulo_vacante_actual}")
                print(f"Nombre: {nombre}")
                print(f"Teléfono: {numero}")
                print(f"CV URL: {cv_url}")
                print(f"Email: {email}")
                print(f"DNI: {dni}")
                print(f"Dirección: {direccion}")
                resumen_preview = (resumen.replace('\n', ' ')[:100]) if resumen != "No encontrado" else "No encontrado"
                print(f"Resumen (primeros 100 chars): {resumen_preview}")
                print(f"Salario Deseado: {salario_deseado}")
                print(f"Fuente del Candidato: {fuente_candidato}") # Imprimir la fuente extraída
                print(f"Respuestas filtro: {respuestas_filtro_texto[:200]}...") # Imprimir solo una parte

                data_candidato = {
                    "vacante": titulo_vacante_actual, # Usar el nombre de la vacante de la página de candidatos
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
                    "source": fuente_candidato # Usar la fuente extraída dinámicamente
                }

                try:
                    # Asegúrate que esta URL es accesible desde el contenedor
                    r_cand = requests.post("http://10.20.62.101:5678/webhook/insert", json=data_candidato, timeout=10)
                    print(f"API Candidato: {' Enviado' if r_cand.status_code == 200 else f' Error {r_cand.status_code}: {r_cand.text}'}")
                except Exception as e_http_cand:
                    print(f" Error HTTP al enviar candidato: {e_http_cand}")

                # Volver a la lista de candidatos (página de la vacante)
                print(f" Volviendo a la página de la vacante: {href}")
                driver.get(href) # Usar href de la vacante actual en lugar de driver.back()
                # Esperar a que la lista de candidatos (o un marcador de ella) vuelva a cargar
                try:
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.match-link")))
                    print(" Página de la vacante (lista de candidatos) cargada después de volver.")
                except TimeoutException:
                    print(" Timeout: La lista de candidatos no pareció recargarse después de volver a la URL de la vacante. Puede haber problemas en la siguiente iteración.")
                
                # time.sleep(3) # Reemplazado por espera explícita

            except Exception as e_cand_loop:
                nombre_ref = nombre_candidato_link if 'nombre_candidato_link' in locals() and nombre_candidato_link else 'Nombre desconocido'
                print(f" Error procesando candidato #{i + 1} ('{nombre_ref}'): {e_cand_loop}")
                print(f" URL actual al momento del error: {driver.current_url}")
                print(" Intentando volver a la página de la vacante para continuar con el siguiente candidato...")
                try:
                    driver.get(href) # 'href' es la URL de la vacante (lista de sus candidatos)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.match-link")))
                    print(" Recuperado en la página de la vacante.")
                except Exception as e_recovery:
                    print(f" Falló el intento de recuperación volviendo a la URL de la vacante: {e_recovery}")
                    print(f" Terminando el procesamiento de candidatos para esta vacante: {href}")
                    break # Salir del bucle de candidatos para esta vacante
                continue # Continuar con el siguiente candidato

        print(f"--- Fin del procesamiento de candidatos para la vacante: {href} ---")
        print("-" * 60)
        # Volver a la lista de vacantes (ya se hace al inicio del loop de vacantes con driver.get(href))
        # No es necesario driver.back() aquí, el loop externo de vacantes se encarga con driver.get(href_vacante)

finally:
    if driver:
        print(" Cerrando el navegador...")
        driver.quit()
