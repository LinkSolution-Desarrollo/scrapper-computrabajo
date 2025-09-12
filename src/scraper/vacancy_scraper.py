import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src import utils, config

def get_all_vacancy_links(driver):
    """Finds and returns all vacancy links from the main page."""
    print("Buscando todas las vacantes...")
    driver.get(config.LOGIN_URL) # Ensure we are on the correct page
    time.sleep(5)

    links = driver.find_elements(By.CSS_SELECTOR, "a.font-xl.fw-900.lh-120")
    hrefs = [link.get_attribute("href") for link in links]
    print(f"Se encontraron {len(hrefs)} vacantes.")
    return hrefs

def scrape_vacancy_details(driver, vacancy_url):
    """Scrapes the details of a single vacancy."""
    print(f"Procesando detalles de la vacante: {vacancy_url}")
    driver.get(vacancy_url)
    time.sleep(3)

    titulo_vacante_actual = "No encontrado"
    try:
        edit_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='btnEditVacancy']"))
        )
        edit_btn.click()

        wait_edit = WebDriverWait(driver, 10)
        job_input_element = wait_edit.until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='Job']"))
        )

        titulo_base = job_input_element.get_attribute('value').strip()
        complemento = driver.find_element(By.XPATH, "//*[@id='JobComplement']").get_attribute('value').strip()

        if titulo_base and complemento:
            titulo_vacante_actual = f"{titulo_base} - {complemento}"
        else:
            titulo_vacante_actual = titulo_base or "No encontrado"

        print("\n--- VACANTE ---")
        print(f"Título: {titulo_vacante_actual}")

        data_vacante = {
            "titulo": titulo_vacante_actual,
            "descripcion": "No encontrado",
            "requisitos": "No encontrado",
            "valorado": "No encontrado",
            "source": "pandape"
        }
        utils.send_to_webhook(config.WEBHOOK_VACANCY_URL, data_vacante)

        # Go back to the candidate list for this vacancy
        driver.get(vacancy_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.match-link"))
        )

    except Exception as e:
        print(f" ⚠️ No se pudo procesar la edición de la vacante: {e}.")
        try:
            # Fallback to get title from the candidate page
            wait_fallback = WebDriverWait(driver, 5)
            fallback_selector = (By.CSS_SELECTOR, "div.secondary-bar-title span.lh-140")
            fallback_element = wait_fallback.until(EC.presence_of_element_located(fallback_selector))
            titulo_vacante_actual = fallback_element.text.strip() or "No encontrado"
            print(f" ✅ Título encontrado con fallback: {titulo_vacante_actual}")
        except Exception as e_fallback:
            print(f" ❌ Fallback para obtener el título también falló: {e_fallback}")

    return titulo_vacante_actual
