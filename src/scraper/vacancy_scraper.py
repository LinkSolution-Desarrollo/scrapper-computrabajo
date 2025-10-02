import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src import utils, config

def get_all_vacancy_links(driver):
    """Finds and returns all vacancy links from the main page with improved error handling."""
    print(" [VACANCIES] Buscando todas las vacantes...")
    try:
        driver.get(config.LOGIN_URL) # Ensure we are on the correct page
        time.sleep(config.SCRAPING_CONFIG["DEFAULT_WAIT_TIME"])

        # Wait for vacancy links to load
        WebDriverWait(driver, config.SCRAPING_CONFIG["LONG_WAIT_TIME"]).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.font-xl.fw-900.lh-120"))
        )

        links = driver.find_elements(By.CSS_SELECTOR, "a.font-xl.fw-900.lh-120")
        hrefs = [link.get_attribute("href") for link in links if link.get_attribute("href")]

        print(f" [VACANCIES] Se encontraron {len(hrefs)} vacantes.")
        return hrefs

    except Exception as e:
        print(f" [ERROR] Error buscando vacantes: {e}")
        return []

def scrape_vacancy_details(driver, vacancy_url):
    """Scrapes the details of a single vacancy with improved error handling."""
    print(f" [VACANCY] Procesando detalles de la vacante: {vacancy_url}")

    titulo_vacante_actual = "No encontrado"

    try:
        driver.get(vacancy_url)
        time.sleep(config.SCRAPING_CONFIG["DEFAULT_WAIT_TIME"])

        try:
            edit_btn = WebDriverWait(driver, config.SCRAPING_CONFIG["LONG_WAIT_TIME"]).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='btnEditVacancy']"))
            )
            edit_btn.click()

            wait_edit = WebDriverWait(driver, config.SCRAPING_CONFIG["LONG_WAIT_TIME"])
            job_input_element = wait_edit.until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='Job']"))
            )

            titulo_base = job_input_element.get_attribute('value').strip()
            complemento = driver.find_element(By.XPATH, "//*[@id='JobComplement']").get_attribute('value').strip()

            if titulo_base and complemento:
                titulo_vacante_actual = f"{titulo_base} - {complemento}"
            else:
                titulo_vacante_actual = titulo_base or "No encontrado"

            # --- Scrape Detailed Fields ---

            # 1. Scrape Description
            descripcion_xpath = "//div[@class='ql-editor' and @contenteditable='true']"
            descripcion = utils.safe_extract_text(driver, By.XPATH, descripcion_xpath)

            # 2. Scrape Structured Requisitos
            try:
                age_min = utils.safe_extract_attribute(driver, By.ID, "AgeMin", "value", default="")
                age_max = utils.safe_extract_attribute(driver, By.ID, "AgeMax", "value", default="")

                # For dropdowns, we get the text of the selected option in the button
                gender_xpath = "//button[@id='idSex']/span[not(@class)]"
                experience_xpath = "//button[@id='idExperienceRange']/span[not(@class)]"
                education_xpath = "//button[@id='idStudy1Min']/span[not(@class)]"

                gender = utils.safe_extract_text(driver, By.XPATH, gender_xpath, default="No especificado")
                experience = utils.safe_extract_text(driver, By.XPATH, experience_xpath, default="No especificado")
                education = utils.safe_extract_text(driver, By.XPATH, education_xpath, default="No especificado")

                requisitos_parts = []
                if age_min and age_max:
                    requisitos_parts.append(f"Rango de edad: {age_min}-{age_max}")
                if gender and gender != "No especificado":
                    requisitos_parts.append(f"Género: {gender}")
                if experience and experience != "No especificado":
                    requisitos_parts.append(f"Experiencia: {experience}")
                if education and education != "No especificado":
                    requisitos_parts.append(f"Nivel de educación: {education}")

                requisitos = " | ".join(requisitos_parts) if requisitos_parts else "No encontrado"

            except Exception as e:
                print(f"  -> Error extrayendo requisitos estructurados: {e}")
                requisitos = "Error al extraer"

            # 3. Valorado field (not implemented as per user feedback)
            valorado = "No encontrado"

            print("\n--- VACANTE ---")
            print(f"Título: {titulo_vacante_actual}")
            print(f"Descripción: {'Encontrada' if descripcion != 'No encontrado' else 'No encontrada'}")
            print(f"Requisitos: {requisitos}")

            data_vacante = {
                "titulo": titulo_vacante_actual,
                "descripcion": descripcion,
                "requisitos": requisitos,
                "valorado": valorado,
                "source": "pandape"
            }
            utils.send_to_webhook(config.WEBHOOK_VACANCY_URL, data_vacante)

            # Go back to the candidate list for this vacancy
            driver.get(vacancy_url)
            WebDriverWait(driver, config.SCRAPING_CONFIG["DEFAULT_WAIT_TIME"]).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.match-link"))
            )

        except Exception as e:
            print(f" [ERROR] No se pudo procesar la edición de la vacante: {e}.")
            try:
                # Fallback to get title from the candidate page
                wait_fallback = WebDriverWait(driver, config.SCRAPING_CONFIG["DEFAULT_WAIT_TIME"])
                fallback_selector = (By.CSS_SELECTOR, "div.secondary-bar-title span.lh-140")
                fallback_element = wait_fallback.until(EC.presence_of_element_located(fallback_selector))
                titulo_vacante_actual = fallback_element.text.strip() or "No encontrado"
                print(f"  Título encontrado con fallback: {titulo_vacante_actual}")
            except Exception as e_fallback:
                print(f"  Fallback para obtener el título también falló: {e_fallback}")

    except Exception as e:
        print(f" [ERROR] Error crítico procesando la vacante: {e}")

    return titulo_vacante_actual
