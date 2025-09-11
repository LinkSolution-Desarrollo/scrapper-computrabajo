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

        scrollable_container = None
        try:
            scrollable_container = driver.find_element(By.ID, "DivMatchesList")
            print(" Contenedor de scroll específico encontrado (DivMatchesList).")
        except NoSuchElementException:
            print(" ⚠️ No se encontró el contenedor de scroll específico. Se usarán métodos de scroll de fallback.")

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
                # Si ya hemos encontrado algunos candidatos y el total esperado es conocido pero no alcanzado,
                # es probable que el scroll haya terminado de verdad.
                if current_count > 0 and total_candidatos_esperados > 0 and current_count < total_candidatos_esperados:
                    print(f"  - Alerta: El scroll se detuvo en {current_count} pero se esperaban {total_candidatos_esperados}. Continuando con los encontrados.")
                    break

                stuck_counter += 1
                print(f"  - El número de candidatos no aumenta (intento {stuck_counter}/3).")
                if stuck_counter >= 3:
                    print(" El número de candidatos no ha aumentado en 3 intentos. Se asume que no hay más por cargar. Scroll finalizado.")
                    break
            else:
                stuck_counter = 0 # Resetear si hay progreso

            last_count = current_count
            
            # --- LÓGICA DE SCROLL FINAL Y MÁS FIABLE ---
            # Hacemos scroll directamente en el contenedor DivMatchesList si se encontró.
            if scrollable_container:
                print("  - Haciendo scroll dentro del contenedor específico...")
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_container)
            else:
                # Fallback si el contenedor no se encontró, usar el método de 'scroll a último elemento'.
                if candidatos_visibles:
                    print("  - (Fallback) Haciendo scroll hacia el último candidato visible...")
                    last_element = candidatos_visibles[-1]
                    driver.execute_script("arguments[0].scrollIntoView(true);", last_element)
                else:
                    # Último recurso: scroll de la página completa.
                    print("  - (Fallback) No se encontraron candidatos, haciendo scroll genérico...")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(3)

        # --- ARQUITECTURA REFACTORIZADA PARA PROCESAR CANDIDATOS ---
        # 1. Recopilar todas las URLs de los candidatos después del scroll.
        print("\nRecopilando todas las URLs de los candidatos...")
        candidate_elements = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
        candidate_hrefs = [elem.get_attribute('href') for elem in candidate_elements if elem.get_attribute('href')]
        
        if not candidate_hrefs:
            print("No se encontraron URLs de candidatos para procesar en esta vacante.")
        else:
            print(f"Se encontraron {len(candidate_hrefs)} URLs de candidatos para procesar.")

            # 2. Invertir la lista para procesar del más nuevo al más antiguo, según solicitado.
            candidate_hrefs.reverse()
            print("La lista de URLs se ha invertido para procesar los candidatos más nuevos primero.")

            # 3. Iterar sobre la lista de URLs (método más robusto y estable).
            for i, candidate_url in enumerate(candidate_hrefs):
                print(f"\n--- Procesando candidato {i + 1}/{len(candidate_hrefs)} ---")
                try:
                    # Navegar directamente a la URL del candidato.
                    print(f"Navegando a: {candidate_url}")
                    driver.get(candidate_url)
                    
                    # Esperar a que la página de detalle del candidato cargue.
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.font-3xl.lh-120.fw-600.text-capitalize"))
                    )
                    print("Página de detalle del candidato cargada.")

                    # --- INICIO DE LÓGICA DE EXTRACCIÓN (Preservada del bucle original) ---
                    nombre = safe_extract_text(driver, By.CSS_SELECTOR, "div.font-3xl.lh-120.fw-600.text-capitalize")
                    numero = safe_extract_text(driver, By.CSS_SELECTOR, "a.js_WhatsappLink")
                    cv_url = safe_extract_attribute(driver, By.CSS_SELECTOR, "a[title$='.pdf']", "href")
                    email = safe_extract_text(driver, By.CSS_SELECTOR, "a.text-nowrap.mb-05 span")

                    dni = "No encontrado"
                    try:
                        nationality_section_elements = driver.find_elements(By.XPATH, "//div[span[contains(., 'Nacionalidad') or contains(., 'Nationality')]]")
                        if nationality_section_elements:
                            nationality_section_text = nationality_section_elements[0].text
                            dni_match = re.search(r"(D\.N\.I\.?|NIF|NIE)\s*[:\-]?\s*([A-Z0-9\-\.]{7,12})", nationality_section_text, re.IGNORECASE)
                            if dni_match:
                                dni = dni_match.group(2).strip().replace('.', '').replace('-', '')
                            else:
                                numbers_in_section = re.findall(r'\b\d{7,9}[A-Za-z]?\b', nationality_section_text)
                                if numbers_in_section:
                                    dni = numbers_in_section[0]
                    except Exception as e_dni:
                        print(f" No se pudo extraer DNI automáticamente: {e_dni}")

                    local_cv_path = None
                    if cv_url != "No encontrado":
                        print(f" Intentando descargar CV desde: {cv_url}")
                        local_cv_path = download_file(driver, cv_url)
                        if local_cv_path and os.getenv("MINIO_ENDPOINT"):
                            upload_to_s3(local_cv_path, dni=dni)
                    else:
                        print(" CV no disponible para este candidato.")

                    respuestas_filtro_texto = "No disponibles"
                    wait_long = WebDriverWait(driver, 10)
                    try:
                        resultados_tab_xpath = "//a[@id='ResultsTabAjax' or contains(@href,'#ResultsTabAjax')]"
                        resultados_tab_clickable = wait_long.until(EC.element_to_be_clickable((By.XPATH, resultados_tab_xpath)))
                        is_active = "active" in resultados_tab_clickable.get_attribute("class")
                        if not is_active:
                            driver.execute_script("arguments[0].click();", resultados_tab_clickable)
                            WebDriverWait(driver, 10).until(lambda d: "active" in d.find_element(By.XPATH, resultados_tab_xpath).get_attribute("class"))
                        
                        ver_respuestas_link_element = wait_long.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.js_lnkQuestionnaireWeightedDetail")))
                        driver.execute_script("arguments[0].click();", ver_respuestas_link_element)
                        
                        wait_long.until(EC.visibility_of_element_located((By.ID, "divResult")))
                        preguntas_respuestas_items = wait_long.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#divResult ol.pl-50 > li")))
                        
                        if preguntas_respuestas_items:
                            respuestas_list = []
                            for item_idx, item in enumerate(preguntas_respuestas_items):
                                try:
                                    pregunta = item.find_element(By.XPATH, "./span").text.strip()
                                    respuesta_elements = item.find_elements(By.XPATH, "./div/span")
                                    respuesta = respuesta_elements[0].text.strip() if respuesta_elements and respuesta_elements[0].text.strip() else "Respuesta no proporcionada"
                                    respuestas_list.append(f"{pregunta}: {respuesta}")
                                except Exception as e_qa:
                                    respuestas_list.append("Error al extraer Q&A individual")
                            respuestas_filtro_texto = " | ".join(respuestas_list) if respuestas_list else "No se pudieron extraer preguntas/respuestas individuales."
                        else:
                            respuestas_filtro_texto = "No se encontraron items de preguntas/respuestas en el modal."
                        
                        close_button = wait_long.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#divResult button.close")))
                        driver.execute_script("arguments[0].click();", close_button)
                        wait_long.until(EC.invisibility_of_element_located((By.ID, "divResult")))

                    except Exception as e_filtro:
                        print(f" No se pudieron obtener las respuestas de filtro: {e_filtro}")
                        respuestas_filtro_texto = "Error al extraer respuestas de filtro."

                    direccion = safe_extract_text(driver, By.CSS_SELECTOR, "span.js_CandidateAddress")
                    resumen = safe_extract_text(driver, By.CSS_SELECTOR, "div#Summary p.text-break-word")
                    salario_deseado_elements = driver.find_elements(By.XPATH, "//div[span[contains(., 'Salario deseado') or contains(., 'Desired salary')]]/div[contains(@class, 'col-9')]/div")
                    salario_deseado = salario_deseado_elements[0].text.strip() if salario_deseado_elements else "No encontrado"
                    
                    fuente_candidato = "Fuente no especificada"
                    try:
                        fuente_element = driver.find_element(By.XPATH, "//img[contains(@src, '/images/publishers/icons/')]/following-sibling::span")
                        fuente_candidato = fuente_element.text.strip() if fuente_element and fuente_element.text.strip() else "Fuente no especificada"
                    except NoSuchElementException:
                        pass

                    print("\n--- CANDIDATO DETALLE ---")
                    print(f"Vacante en página: {titulo_vacante_actual}")
                    print(f"Nombre: {nombre}")
                    # ... (demás prints para depuración)

                    data_candidato = {
                        "vacante": titulo_vacante_actual,
                        "nombre": nombre,
                        "numero": numero,
                        "curriculum_url": cv_url,
                        "curriculum_descargado": os.path.basename(local_cv_path) if local_cv_path else "No descargado",
                        "email": email,
                        "dni": dni,
                        "direccion": direccion,
                        "resumen": resumen,
                        "salario_deseado": salario_deseado,
                        "respuestas_filtro": respuestas_filtro_texto,
                        "source": fuente_candidato
                    }

                    try:
                        r_cand = requests.post("http://10.20.62.101:5678/webhook/insert", json=data_candidato, timeout=10)
                        print(f"API Candidato: {' Enviado' if r_cand.status_code == 200 else f' Error {r_cand.status_code}: {r_cand.text}'}")
                    except Exception as e_http_cand:
                        print(f" Error HTTP al enviar candidato: {e_http_cand}")
                    # --- FIN DE LÓGICA DE EXTRACCIÓN ---

                except Exception as e_cand_loop:
                    print(f" ❌ Error fatal procesando la URL {candidate_url}: {e_cand_loop}")
                    print(" No se puede continuar con este candidato. Pasando al siguiente.")
                    continue # Continuar con la siguiente URL

        print(f"--- Fin del procesamiento de candidatos para la vacante: {href} ---")
        print("-" * 60)
        # Volver a la lista de vacantes (ya se hace al inicio del loop de vacantes con driver.get(href))
        # No es necesario driver.back() aquí, el loop externo de vacantes se encarga con driver.get(href_vacante)

finally:
    if driver:
        print(" Cerrando el navegador...")
        driver.quit()
