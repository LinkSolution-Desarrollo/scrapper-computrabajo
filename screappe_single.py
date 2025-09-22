# -*- coding: utf-8 -*-
# --- SCRIPT PARA PROCESAR UNA ÚNICA VACANTE ---
# INSTRUCCIONES:
# 1.  Asegúrese de que su archivo .env está configurado con las credenciales de USUARIO y CLAVE.
# 2.  Modifique la variable `SINGLE_VACANCY_URL` a continuación con el enlace de la vacante que desea scrapear.
# 3.  Ejecute el script.

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
from webdriver_manager.chrome import ChromeDriverManager
import time
import boto3
from urllib.parse import urlparse
from boto3.session import Config

# --- CONFIGURACIÓN ---
# ▼▼▼ PEGUE LA URL DE LA VACANTE AQUÍ ▼▼▼
SINGLE_VACANCY_URL = "https://ats.pandape.com/Company/Match/Matches/10488465?idvacancyfolder=69652247&matchesfilter.idvacancy=10488465&matchesfilter.idvacancyfolder=69652247&matchesfilter.vacancylatitude=0&matchesfilter.vacancylongitude=0&matchesfilter.searchinlastexperience_experiencecategories1=false&matchesfilter.searchinlastexperience_experiencecompany=false&matchesfilter.searchinlastexperience_experiencejob=false&matchesfilter.searchinlastexperience_experiencemanageriallevel=false&matchesfilter.searchinlastexperience_experiencerange=false&matchesfilter.latitude=-34.545178&matchesfilter.longitude=-58.449936&matchesfilter.postalcodevalue=c1424+-+belgrano+-+belgrano&matchesfilter.experiencectinprogress=0&matchesfilter.testlanguageoperatortype=0&matchesfilter.negotiablesalary=false&matchesfilter.readcvstatus=3&matchesfilter.studyingstatus=0&matchesfilter.hascommentsct=3&matchesfilter.photofilterct=3&matchesfilter.testcustomoperatortype=0&matchesfilter.aiscoretype=0&matchesfilter.typesearchexperience=0&matchesfilter.typesearchstudystatus=0&matchesfilter.testexternaloperatortype=0&matchesfilter.hasevaluationcomments=3&matchesfilter.candidateassignmenttype=3&matchesfilter.isoutoflimit=3&matchesfilter.lastidcandidate=0&matchesfilter.disabilityvalidation=0&matchesfilter.hasdisability=0&matchesfilter.pagenumber=2&matchesfilter.pagesize=40&matchesfilter.loadall=false&matchesfilter.order=0" # URL de ejemplo
# ▲▲▲ PEGUE LA URL DE LA VACANTE AQUÍ ▲▲▲


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

def download_file(driver, url, local_folder="downloads"):
    os.makedirs(local_folder, exist_ok=True)
    filename = os.path.basename(urlparse(url).path) or f"cv_{int(time.time())}.pdf"
    local_path = os.path.join(local_folder, filename)
    try:
        s = requests.Session()
        for cookie in driver.get_cookies():
            s.cookies.set(cookie['name'], cookie['value'])
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
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

load_dotenv()
usuario = os.environ.get("USUARIO")
clave = os.environ.get("CLAVE")

options = Options()
# options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")

try:
    print(" Configurando ChromeDriver usando webdriver-manager...")
    service = Service(ChromeDriverManager().install())
except Exception as e:
    print(f" Error configurando ChromeDriver con webdriver-manager: {e}")
    service = Service()

driver = webdriver.Chrome(service=service, options=options)

try:
    # --- INICIO DEL PROCESO ---
    if not SINGLE_VACANCY_URL or "https://ats.pandape.com" not in SINGLE_VACANCY_URL:
        raise ValueError("Por favor, establezca una URL de vacante de Pandape válida en la variable SINGLE_VACANCY_URL.")

    # 1. Iniciar sesión
    print("Iniciando sesión en Pandape...")
    driver.get("https://ats.pandape.com/Company/Vacancy?Pagination[PageNumber]=1&Pagination[PageSize]=1000&Order=1&IdsFilter=2&RecruitmentType=0")
    time.sleep(5)
    driver.find_element(By.ID, "Username").send_keys(usuario)
    driver.find_element(By.ID, "Password").send_keys(clave)
    driver.find_element(By.ID, "btLogin").click()
    time.sleep(10)

    try:
        driver.find_element(By.ID, "AllowCookiesButton").click()
        time.sleep(2)
    except NoSuchElementException:
        print(" No se encontró el botón de cookies o no fue necesario.")

    # 2. Navegar a la vacante especificada
    href = SINGLE_VACANCY_URL
    print(f"\nProcesando vacante: {href}")
    driver.get(href)
    time.sleep(3)

    # 3. Extraer título de la vacante
    titulo_vacante_actual = "No encontrado"
    try:
        wait_fallback = WebDriverWait(driver, 5)
        fallback_selector = (By.CSS_SELECTOR, "div.secondary-bar-title span.lh-140")
        fallback_element = wait_fallback.until(EC.presence_of_element_located(fallback_selector))
        titulo_fallback = fallback_element.text.strip()
        if titulo_fallback:
            titulo_vacante_actual = titulo_fallback
            print(f" ✅ Título de la vacante encontrado: {titulo_vacante_actual}")
        else:
            print(" ❌ El título de la vacante estaba vacío.")
    except Exception as e_fallback:
        print(f" ❌ No se pudo obtener el título de la vacante: {e_fallback}")

    # 4. Scroll inteligente para cargar todos los candidatos
    print(" Iniciando scroll para cargar todos los candidatos...")
    total_candidatos_esperados = 0
    try:
        inscriptos_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Inscriptos')]")))
        match = re.search(r'\((\d+)\)', inscriptos_element.text)
        if match:
            total_candidatos_esperados = int(match.group(1))
            print(f" Total de candidatos esperados: {total_candidatos_esperados}")
    except Exception as e:
        print(f" No se pudo encontrar el total de 'Inscriptos'. Se usará el método de scroll de fallback.")

    scrollable_container = None
    try:
        scrollable_container = driver.find_element(By.ID, "DivMatchesList")
        print(" Contenedor de scroll específico encontrado.")
    except NoSuchElementException:
        print(" ⚠️ No se encontró el contenedor de scroll específico.")

    last_count = -1
    stuck_counter = 0
    while True:
        candidatos_visibles = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
        current_count = len(candidatos_visibles)
        print(f"  - Encontrados {current_count}/{total_candidatos_esperados if total_candidatos_esperados > 0 else '??'} candidatos.")
        if total_candidatos_esperados > 0 and current_count >= total_candidatos_esperados:
            print(" Se ha alcanzado el número total de candidatos. Scroll finalizado.")
            break
        if current_count == last_count:
            if current_count > 0 and total_candidatos_esperados > 0 and current_count < total_candidatos_esperados:
                print(f"  - Alerta: El scroll se detuvo en {current_count}. Continuando con los encontrados.")
                break
            stuck_counter += 1
            if stuck_counter >= 3:
                print(" El número de candidatos no ha aumentado en 3 intentos. Scroll finalizado.")
                break
        else:
            stuck_counter = 0
        last_count = current_count
        if scrollable_container:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_container)
        else: # Fallback a scroll de toda la página
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    # 5. Recopilar URLs y procesar candidatos
    print("\nRecopilando todas las URLs de los candidatos...")
    candidate_elements = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
    candidate_hrefs = [elem.get_attribute('href') for elem in candidate_elements if elem.get_attribute('href')]
    
    if not candidate_hrefs:
        print("No se encontraron URLs de candidatos para procesar.")
    else:
        print(f"Se encontraron {len(candidate_hrefs)} URLs. Invirtiendo para procesar los más nuevos primero.")
        candidate_hrefs.reverse()

        for i, candidate_url in enumerate(candidate_hrefs):
            print(f"\n--- Procesando candidato {i + 1}/{len(candidate_hrefs)} ---")
            try:
                print(f"Navegando a: {candidate_url}")
                driver.get(candidate_url)
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.font-3xl.lh-120.fw-600.text-capitalize")))
                
                # --- LÓGICA DE EXTRACCIÓN ---
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
                data_candidato = { "vacante": titulo_vacante_actual, "nombre": nombre, "numero": numero, "curriculum_url": cv_url, "curriculum_descargado": os.path.basename(local_cv_path) if local_cv_path else "No descargado", "email": email, "dni": dni, "direccion": direccion, "resumen": resumen, "salario_deseado": salario_deseado, "respuestas_filtro": respuestas_filtro_texto, "source": fuente_candidato }
                try:
                    r_cand = requests.post("http://10.20.62.101:5678/webhook/insert", json=data_candidato, timeout=10)
                    print(f"API Candidato: {' Enviado' if r_cand.status_code == 200 else f' Error {r_cand.status_code}: {r_cand.text}'}")
                except Exception as e_http_cand:
                    print(f" Error HTTP al enviar candidato: {e_http_cand}")

            except Exception as e_cand_loop:
                print(f" ❌ Error fatal procesando la URL {candidate_url}: {e_cand_loop}")
                continue
    
    print(f"\n--- Fin del procesamiento para la vacante: {href} ---")

finally:
    if driver:
        print(" Cerrando el navegador...")
        driver.quit()
