from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import requests
import re

from webdriver_manager.chrome import ChromeDriverManager
import time

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
        try:
            vacante = driver.find_element(By.CSS_SELECTOR, "div.secondary-bar-title span.lh-140").text
        except:
            vacante = "No encontrada"

        # Buscar candidatos (match-link)
        candidatos = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
        total = min(100, len(candidatos))  # Máximo 5 por vacante

        for i in range(total):
            candidatos_actualizados = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
            try:
                candidato = candidatos_actualizados[i]
                candidato.click()
                time.sleep(3)

                try:
                    nombre = driver.find_element(By.CSS_SELECTOR, "div.font-3xl.lh-120.fw-600.text-capitalize").text
                except:
                    nombre = "No encontrado"

                try:
                    numero = driver.find_element(By.CSS_SELECTOR, "a.js_WhatsappLink").text
                except:
                    numero = "No encontrado"

                try:
                    cv = driver.find_element(By.CSS_SELECTOR, "a[title$='.pdf']").get_attribute("href")
                except:
                    cv = "No encontrado"

                try:
                    email = driver.find_element(By.CSS_SELECTOR, "a.text-nowrap.mb-05 span").text
                except:
                    email = "No encontrado"

                try:
                    div_element = driver.find_element(By.XPATH, "//div[span[text()='Nacionalidad']]")
                    driver.execute_script("arguments[0].scrollIntoView(true);", div_element)
                    time.sleep(1)  # para asegurar que el scroll y renderizado se completen
                    div_text = div_element.text
                    dni_match = re.search(r"D\.N\.I\s*(\d+)", div_text)
                    dni = dni_match.group(1) if dni_match else None
                    if dni is None:
                        print("No se encontró DNI en el texto:", div_text)
                except Exception as e:
                    print(f"Error al obtener DNI: {e}")
                    dni = None

                try:
                    direccion = driver.find_element(By.CSS_SELECTOR, "span.ml-20").text.strip()
                except:
                    direccion = "No encontrado"

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
                    "source":"computrabajo",
                }

                try:
                    response = requests.post("http://10.20.62.94:5678/webhook/insert", json=data)
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
        time.sleep(3)

finally:
    driver.quit()
