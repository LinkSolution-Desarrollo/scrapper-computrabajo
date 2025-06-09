from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import requests
import re
import os
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Cargar variables del entorno
load_dotenv()
usuario = os.environ.get("USUARIO")
clave = os.environ.get("CLAVE")

# --- Global Constants ---
WEBHOOK_URL = "http://10.20.62.94:5678/webhook/insert"
MAX_CANDIDATES_PER_VACANCY = 100
DATA_SOURCE = "computrabajo"
# --- End Global Constants ---

# Configuración de Chrome
options = Options()
options.add_argument("--start-maximized")  # abre el navegador maximizado
# options.add_argument("--headless")  # Descomentá si querés que se ejecute sin abrir ventana

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # 1. Ir al sitio de login
    driver.get("https://ats.pandape.com/Company/Vacancy")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "Username")))

    # 2. Completar usuario y contraseña
    driver.find_element(By.ID, "Username").send_keys(usuario)
    driver.find_element(By.ID, "Password").send_keys(clave)

    # 3. Hacer clic en "Entrar"
    driver.find_element(By.ID, "btLogin").click()
    # Wait for either vacancy links or the cookie button to be clickable
    WebDriverWait(driver, 10).until(
        EC.or_(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.font-xl.fw-900.lh-120")),
            EC.element_to_be_clickable((By.ID, "AllowCookiesButton"))
        )
    )

    # 4. Aceptar cookies si aparece el botón
    try:
        cookie_button = driver.find_element(By.ID, "AllowCookiesButton")
        if cookie_button.is_displayed() and cookie_button.is_enabled():
            cookie_button.click()
            WebDriverWait(driver, 10).until(EC.staleness_of(cookie_button))
    except NoSuchElementException:
        pass

    # 5. Buscar todos los links de vacantes
    links = driver.find_elements(By.CSS_SELECTOR, "a.font-xl.fw-900.lh-120")
    hrefs = [link.get_attribute("href") for link in links]

    # 6. Recorrer cada vacante
    for href in hrefs:
        print(f"Entrando a vacante: {href}")
        driver.get(href)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.secondary-bar-title span.lh-140")))

        # Extraer nombre de la vacante
        try:
            vacante = driver.find_element(By.CSS_SELECTOR, "div.secondary-bar-title span.lh-140").text
        except:
            vacante = "No encontrada"

        # Buscar candidatos (match-link)
        candidatos = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
        total = min(MAX_CANDIDATES_PER_VACANCY, len(candidatos))  # Process up to MAX_CANDIDATES_PER_VACANCY candidates per vacancy

        for i in range(total):
            # Re-fetch candidate links in each iteration because navigating to a candidate's profile
            # and then back to the vacancy page invalidates the previous list of DOM elements.
            # This is necessary to avoid StaleElementReferenceException.
            candidatos_actualizados = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
            try:
                candidato = candidatos_actualizados[i]
                candidato.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.font-3xl.lh-120.fw-600.text-capitalize")))

                try:
                    nombre = driver.find_element(By.CSS_SELECTOR, "div.font-3xl.lh-120.fw-600.text-capitalize").text
                except NoSuchElementException:
                    nombre = "No encontrado"
                    print("Warning: Nombre no encontrado para el candidato actual.")
                except Exception as e:
                    nombre = "No encontrado"
                    print(f"Error extrayendo nombre: {e}")

                try:
                    numero = driver.find_element(By.CSS_SELECTOR, "a.js_WhatsappLink").text
                except NoSuchElementException:
                    numero = "No encontrado"
                    print("Warning: Número no encontrado para el candidato actual.")
                except Exception as e:
                    numero = "No encontrado"
                    print(f"Error extrayendo número: {e}")

                try:
                    cv = driver.find_element(By.CSS_SELECTOR, "a[title$='.pdf']").get_attribute("href")
                except NoSuchElementException:
                    cv = "No encontrado"
                    print("Warning: CV no encontrado para el candidato actual.")
                except Exception as e:
                    cv = "No encontrado"
                    print(f"Error extrayendo CV: {e}")

                try:
                    email = driver.find_element(By.CSS_SELECTOR, "a.text-nowrap.mb-05 span").text
                except NoSuchElementException:
                    email = "No encontrado"
                    print("Warning: Email no encontrado para el candidato actual.")
                except Exception as e:
                    email = "No encontrado"
                    print(f"Error extrayendo email: {e}")

                try:
                    # Wait for the DNI section to be present before trying to find it
                    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[span[text()='Nacionalidad']]")))
                    div_element = driver.find_element(By.XPATH, "//div[span[text()='Nacionalidad']]")
                    # Scroll and wait for visibility (already improved in previous step)
                    driver.execute_script("arguments[0].scrollIntoView(true);", div_element)
                    WebDriverWait(driver, 5).until(EC.visibility_of(div_element))

                    div_text = div_element.text
                    dni_match = re.search(r"D\.N\.I\s*(\d+)", div_text)
                    dni = dni_match.group(1) if dni_match else "No encontrado"
                    if dni == "No encontrado":
                        print(f"Warning: DNI no encontrado en el texto: {div_text}")
                except NoSuchElementException:
                    dni = "No encontrado"
                    print("Warning: Sección de Nacionalidad/DNI no encontrada.")
                except Exception as e:
                    dni = "No encontrado"
                    print(f"Error al obtener DNI: {e}")

                try:
                    # Assuming "span.ml-20" is the best available selector for direccion for now
                    direccion = driver.find_element(By.CSS_SELECTOR, "span.ml-20").text.strip()
                except NoSuchElementException:
                    direccion = "No encontrado"
                    print("Warning: Dirección no encontrada para el candidato actual.")
                except Exception as e:
                    direccion = "No encontrado"
                    print(f"Error extrayendo dirección: {e}")

                print(f"Vacante: {vacante}")
                print(f"Nombre: {nombre}")
                print(f"Número: {numero}")
                print(f"CV: {cv}")
                print(f"Email: {email}")
                print(f"DNI: {dni}")
                print(f"Dirección: {direccion}")

                data = {
                    "vacante": vacante,
                    "nombre": nombre,
                    "numero": numero,
                    "curriculum": cv,
                    "email": email,
                    "dni": dni,
                    "direccion": direccion,
                    "source": DATA_SOURCE,
                }

                try:
                    response = requests.post(WEBHOOK_URL, json=data)
                    if response.status_code == 200:
                        print("Datos enviados correctamente.")
                    else:
                        print(f"Error al enviar datos: {response.status_code} - {response.text}")
                except Exception as e:
                    print(f"Error en la petición HTTP: {e}")

                time.sleep(2)

            except Exception as e:
                print(f"Error al hacer clic en el candidato #{i}: {e}")
                continue

        print("-" * 60)
        driver.back()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.font-xl.fw-900.lh-120")))

finally:
    driver.quit()
