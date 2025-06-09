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

# Helper functions
from selenium.common.exceptions import NoSuchElementException

def safe_extract_text(driver, by, value, default="No encontrado"):
    try:
        return driver.find_element(by, value).text.strip() # Added strip()
    except NoSuchElementException:
        # print(f"Element not found for text: {by} {value}") # Optional: for debugging
        return default
    except Exception as e: # Catch any other unexpected error during .text or .strip()
        # print(f"Other error extracting text for {by} {value}: {e}") # Optional: for debugging
        return default

def safe_extract_attribute(driver, by, value, attribute, default="No encontrado"):
    try:
        return driver.find_element(by, value).get_attribute(attribute)
    except NoSuchElementException:
        # print(f"Element not found for attribute: {by} {value}") # Optional: for debugging
        return default
    except Exception as e: # Catch any other unexpected error during .get_attribute()
        # print(f"Other error extracting attribute for {by} {value}: {e}") # Optional: for debugging
        return default

# Cargar variables del entorno
load_dotenv()
usuario = os.environ.get("USUARIO")
clave = os.environ.get("CLAVE")

# Configuración de Chrome
options = Options()
options.add_argument("--start-maximized")  # abre el navegador maximizado
# options.add_argument("--headless")  # Descomentá si querés que se ejecute sin abrir ventana

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # 1. Ir al sitio de login
    driver.get("https://ats.pandape.com/Company/Vacancy")
    time.sleep(2)

    # 2. Completar usuario y contraseña
    driver.find_element(By.ID, "Username").send_keys("Flor.leyva@linksolution.com.ar")
    driver.find_element(By.ID, "Password").send_keys("Febrero2023")

    # 3. Hacer clic en "Entrar"
    driver.find_element(By.ID, "btLogin").click()
    time.sleep(5)

    # 4. Aceptar cookies si aparece el botón
    try:
        driver.find_element(By.ID, "AllowCookiesButton").click()
        time.sleep(2)
    except NoSuchElementException:
        pass

    # 5. Buscar todos los links de vacantes
    links = driver.find_elements(By.CSS_SELECTOR, "a.font-xl.fw-900.lh-120")
    hrefs = [link.get_attribute("href") for link in links]

    # 6. Recorrer cada vacante
    for href in hrefs:
        print(f"Entrando a vacante: {href}")
        driver.get(href)
        time.sleep(3)

        # Extraer nombre de la vacante
        vacante = safe_extract_text(driver, By.CSS_SELECTOR, "div.secondary-bar-title span.lh-140")

        # Buscar candidatos (match-link)
        candidatos = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
        total = min(100, len(candidatos))  # Máximo 5 por vacante

        for i in range(total):
            candidatos_actualizados = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
            try:
                candidato = candidatos_actualizados[i]
                candidato.click()
                time.sleep(3)

                nombre = safe_extract_text(driver, By.CSS_SELECTOR, "div.font-3xl.lh-120.fw-600.text-capitalize")
                numero = safe_extract_text(driver, By.CSS_SELECTOR, "a.js_WhatsappLink")
                cv = safe_extract_attribute(driver, By.CSS_SELECTOR, "a[title$='.pdf']", "href")
                email = safe_extract_text(driver, By.CSS_SELECTOR, "a.text-nowrap.mb-05 span")

                dni = "No encontrado" # Default value
                try:
                    div_element = driver.find_element(By.XPATH, "//div[span[text()='Nacionalidad']]")
                    driver.execute_script("arguments[0].scrollIntoView(true);", div_element)
                    time.sleep(1)  # para asegurar que el scroll y renderizado se completen
                    div_text = div_element.text
                    dni_match = re.search(r"D\.N\.I\s*(\d+)", div_text)
                    if dni_match:
                        dni = dni_match.group(1)
                    else:
                        print(f"D.N.I. no encontrado en el texto: '{div_text}'")
                        # dni sigue siendo "No encontrado"
                except NoSuchElementException:
                    print("No se encontró el campo/div de Nacionalidad para extraer DNI.")
                    # dni sigue siendo "No encontrado"
                except Exception as e:
                    print(f"Error inesperado al obtener DNI: {e}")
                    # dni sigue siendo "No encontrado"

                direccion = safe_extract_text(driver, By.CSS_SELECTOR, "span.ml-20")
                resumen = safe_extract_text(driver, By.CSS_SELECTOR, "div#Summary p.text-break-word")
                salario_deseado = safe_extract_text(driver, By.CSS_SELECTOR, "div#Salary div.col-9 > div")

                print(f"Vacante: {vacante}")
                print(f"Nombre: {nombre}")
                print(f"Número: {numero}")
                print(f"CV: {cv}")
                print(f"Email: {email}")
                print(f"DNI: {dni}")
                print(f"Dirección: {direccion}")
                print(f"Resumen: {resumen}")
                print(f"Salario Deseado: {salario_deseado}")

                data = {
                    "vacante": vacante,
                    "nombre": nombre,
                    "numero": numero,
                    "curriculum": cv,
                    "email": email,
                    "dni": dni,
                    "direccion": direccion,
                    "resumen": resumen,
                    "salario_deseado": salario_deseado, # New field
                    "source":"computrabajo",
                }

                try:
                    # It's good practice to add a timeout to network requests
                    response = requests.post("http://10.20.62.94:5678/webhook/insert", json=data, timeout=10)

                    if response.status_code == 200:
                        print("Datos enviados correctamente.")
                    else:
                        # The server responded with an HTTP error code
                        print(f"Error del servidor al enviar datos: Código {response.status_code} - Respuesta: {response.text}")

                except requests.exceptions.Timeout:
                    print("Error en la petición HTTP: Timeout - El servidor (10.20.62.94:5678) tardó demasiado en responder.")
                except requests.exceptions.ConnectionError:
                    print("Error en la petición HTTP: Error de conexión - No se pudo conectar al servidor (10.20.62.94:5678). Verifica la red y que el servidor esté activo.")
                except requests.exceptions.RequestException as re:
                    # For other requests-related issues (e.g., invalid URL, too many redirects)
                    print(f"Error en la petición HTTP: {re}")
                except Exception as e:
                    # For any other unexpected error not caught above
                    print(f"Error inesperado durante el envío de datos HTTP: {e}")

                time.sleep(2)

            except Exception as e:
                print(f"Error al hacer clic en el candidato #{i}: {e}")
                continue

        print("-" * 60)
        driver.back()
        time.sleep(3)

finally:
    driver.quit()
