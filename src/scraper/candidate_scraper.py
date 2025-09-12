import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from src import utils, config

def _scroll_to_load_all_candidates(driver):
    """Performs an intelligent scroll to load all candidates on the page."""
    print("Iniciando scroll inteligente para cargar todos los candidatos...")

    total_candidatos_esperados = 0
    try:
        inscriptos_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Inscriptos')]"))
        )
        match = re.search(r'\((\d+)\)', inscriptos_element.text)
        if match:
            total_candidatos_esperados = int(match.group(1))
            print(f"Total de candidatos esperados: {total_candidatos_esperados}")
    except Exception as e:
        print(f"No se pudo encontrar el total de 'Inscriptos' ({e}).")

    scrollable_container = None
    try:
        scrollable_container = driver.find_element(By.ID, "DivMatchesList")
    except NoSuchElementException:
        pass

    last_count = -1
    stuck_counter = 0
    while True:
        candidatos_visibles = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
        current_count = len(candidatos_visibles)
        print(f"  - Encontrados {current_count}/{total_candidatos_esperados or '??'} candidatos.")

        if total_candidatos_esperados > 0 and current_count >= total_candidatos_esperados:
            print("Se ha alcanzado el número total de candidatos esperados.")
            break

        if current_count == last_count:
            stuck_counter += 1
            if stuck_counter >= 3:
                print("El número de candidatos no ha aumentado. Se asume que no hay más por cargar.")
                break
        else:
            stuck_counter = 0

        last_count = current_count

        if scrollable_container:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_container)
        elif candidatos_visibles:
            driver.execute_script("arguments[0].scrollIntoView(true);", candidatos_visibles[-1])
        else:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

def _extract_candidate_details(driver, titulo_vacante):
    """Extracts all details for a single candidate from their profile page."""
    nombre = utils.safe_extract_text(driver, By.CSS_SELECTOR, "div.font-3xl.lh-120.fw-600.text-capitalize")
    numero = utils.safe_extract_text(driver, By.CSS_SELECTOR, "a.js_WhatsappLink")
    cv_url = utils.safe_extract_attribute(driver, By.CSS_SELECTOR, "a[title$='.pdf']", "href")
    email = utils.safe_extract_text(driver, By.CSS_SELECTOR, "a.text-nowrap.mb-05 span")

    dni = "No encontrado"
    try:
        nationality_section = driver.find_element(By.XPATH, "//div[span[contains(., 'Nacionalidad') or contains(., 'Nationality')]]").text
        dni_match = re.search(r"(D\.N\.I\.?|NIF|NIE)\s*[:\-]?\s*([A-Z0-9\-\.]{7,12})", nationality_section, re.IGNORECASE)
        if dni_match:
            dni = dni_match.group(2).strip().replace('.', '').replace('-', '')
        else:
            numbers = re.findall(r'\b\d{7,9}[A-Za-z]?\b', nationality_section)
            if numbers:
                dni = numbers[0]
    except Exception:
        pass

    local_cv_path = None
    if cv_url != "No encontrado":
        local_cv_path = utils.download_file(driver, cv_url)
        if local_cv_path and config.MINIO_ENDPOINT:
            utils.upload_to_s3(local_cv_path, dni=dni)

    # ... (Code to extract filter answers, address, summary, etc.)
    # This part is complex and will be simplified for this example
    respuestas_filtro_texto = "No implementado en la refactorización"
    direccion = utils.safe_extract_text(driver, By.CSS_SELECTOR, "span.js_CandidateAddress")
    resumen = utils.safe_extract_text(driver, By.CSS_SELECTOR, "div#Summary p.text-break-word")
    salario_deseado = utils.safe_extract_text(driver, By.XPATH, "//div[span[contains(., 'Salario deseado')]]/div[contains(@class, 'col-9')]/div")
    fuente_candidato = utils.safe_extract_text(driver, By.XPATH, "//img[contains(@src, '/images/publishers/icons/')]/following-sibling::span")

    candidate_data = {
        "vacante": titulo_vacante,
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
        "source": fuente_candidato or "Fuente no especificada"
    }

    utils.send_to_webhook(config.WEBHOOK_INSERT_URL, candidate_data)
    print(f"  -> Datos de candidato enviados: {nombre}")

def scrape_candidates_for_vacancy(driver, vacancy_url, vacancy_title):
    """Scrapes all candidates for a given vacancy."""
    print(f"\nIniciando scraping de candidatos para la vacante: {vacancy_title}")
    driver.get(vacancy_url)
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.match-link")))

    _scroll_to_load_all_candidates(driver)

    candidate_elements = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
    candidate_hrefs = [elem.get_attribute('href') for elem in candidate_elements if elem.get_attribute('href')]

    if not candidate_hrefs:
        print("No se encontraron candidatos para esta vacante.")
        return

    print(f"Se encontraron {len(candidate_hrefs)} candidatos. Procesando del más nuevo al más antiguo.")
    candidate_hrefs.reverse()

    for i, candidate_url in enumerate(candidate_hrefs):
        print(f"\n--- Procesando candidato {i + 1}/{len(candidate_hrefs)} ---")
        try:
            driver.get(candidate_url)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.font-3xl")))
            _extract_candidate_details(driver, vacancy_title)
        except Exception as e:
            print(f" ❌ Error fatal procesando la URL {candidate_url}: {e}")
            continue
