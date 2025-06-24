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

def safe_extract_text(driver, by, value, default="No encontrado"):
    try:
        return driver.find_element(by, value).text.strip()
    except NoSuchElementException:
        return default
    except Exception:
        return default

def safe_extract_attribute(driver, by, value, attribute, default="No encontrado"):
    try:
        return driver.find_element(by, value).get_attribute(attribute)
    except NoSuchElementException:
        return default
    except Exception:
        return default

# Cargar credenciales desde .env (opcional)
load_dotenv()
usuario = os.environ.get("USUARIO")
clave = os.environ.get("CLAVE")

# Configuración del navegador
options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    driver.get("https://ats.pandape.com/Company/Vacancy")
    time.sleep(2)

    driver.find_element(By.ID, "Username").send_keys("Flor.leyva@linksolution.com.ar")
    driver.find_element(By.ID, "Password").send_keys("Febrero2023")
    driver.find_element(By.ID, "btLogin").click()
    time.sleep(5)

    try:
        driver.find_element(By.ID, "AllowCookiesButton").click()
        time.sleep(2)
    except NoSuchElementException:
        pass

    links = driver.find_elements(By.CSS_SELECTOR, "a.font-xl.fw-900.lh-120")
    hrefs = [link.get_attribute("href") for link in links]

    for href in hrefs:
        print(f"Entrando a vacante: {href}")
        driver.get(href)
        time.sleep(3)

             # Abrir vista previa en nueva pestaña
        try:
            preview_button = driver.find_element(By.CSS_SELECTOR, "a[title='Vista previa']")
            preview_link = preview_button.get_attribute("href")

            driver.execute_script("window.open(arguments[0]);", preview_link)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(3)

            titulo = safe_extract_text(driver, By.CSS_SELECTOR, "h1.fw-600.color-title")

            try:
                descripcion_div = driver.find_element(By.CSS_SELECTOR, "div.order-1")
                descripcion = descripcion_div.text.strip()
            except Exception:
                descripcion = "No disponible"

            try:
                requisitos_div = driver.find_element(By.ID, "Requirements")
                requisitos = requisitos_div.text.strip()
            except Exception:
                requisitos = "No disponible"

            try:
                valorado_div = driver.find_element(By.ID, "Valued")
                valorado = valorado_div.text.strip()
            except Exception:
                valorado = "No disponible"

            vacante_data = {
                "url": preview_link,
                "titulo": titulo,
                "descripcion": descripcion,
                "requisitos": requisitos,
                "valorado": valorado,
                "fuente": "pandape"
            }

            try:
                response = requests.post("http://10.20.62.94:5678/webhook/vacant", json=vacante_data, timeout=10)
                if response.status_code == 200:
                    print("Vista previa enviada correctamente.")
                else:
                    print(f"Error al enviar vista previa: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Error al enviar vista previa: {e}")

            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except Exception as e:
            print(f"No se pudo abrir la vista previa: {e}")


        vacante = safe_extract_text(driver, By.CSS_SELECTOR, "div.secondary-bar-title span.lh-140")
        candidatos = driver.find_elements(By.CSS_SELECTOR, "a.match-link")
        total = min(100, len(candidatos))

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

                dni = "No encontrado"
                try:
                    div_element = driver.find_element(By.XPATH, "//div[span[text()='Nacionalidad']]")
                    driver.execute_script("arguments[0].scrollIntoView(true);", div_element)
                    time.sleep(1)
                    div_text = div_element.text
                    dni_match = re.search(r"D\.N\.I\s*(\d+)", div_text)
                    if dni_match:
                        dni = dni_match.group(1)
                    else:
                        print(f"D.N.I. no encontrado en el texto: '{div_text}'")
                except NoSuchElementException:
                    print("No se encontró el campo/div de Nacionalidad para extraer DNI.")
                except Exception as e:
                    print(f"Error inesperado al obtener DNI: {e}")

                try:
                    resultados_tab = driver.find_element(By.ID, "ResultsTabAjax")
                    driver.execute_script("arguments[0].click();", resultados_tab)
                    time.sleep(2)

                    ver_respuestas = driver.find_element(By.CSS_SELECTOR, "a.js_lnkQuestionnaireWeightedDetail")
                    driver.execute_script("arguments[0].click();", ver_respuestas)
                    time.sleep(2)

                    modal = driver.find_element(By.ID, "divResult")
                    preguntas_respuestas = modal.find_elements(By.CSS_SELECTOR, "ol.pl-50 > li")

                    respuestas_filtro = []
                    for item in preguntas_respuestas:
                        try:
                            pregunta = item.find_element(By.XPATH, "./span").text.strip()
                            respuesta = item.find_element(By.XPATH, "./div/span").text.strip()
                        except Exception:
                            pregunta = "Pregunta no encontrada"
                            respuesta = "Respuesta no encontrada"
                        respuestas_filtro.append(f"{pregunta}: {respuesta}")

                    respuestas_filtro_texto = " | ".join(respuestas_filtro)

                    try:
                        close_button = modal.find_element(By.CSS_SELECTOR, "button.close")
                        driver.execute_script("arguments[0].click();", close_button)
                        time.sleep(1)
                    except Exception as e:
                        print(f"No se pudo cerrar el modal: {e}")

                except NoSuchElementException:
                    print("No se encontraron respuestas de filtro.")
                    respuestas_filtro_texto = "No disponibles"
                except Exception as e:
                    print(f"Error inesperado al obtener respuestas de filtro: {e}")
                    respuestas_filtro_texto = "Error"

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
                print(f"Respuestas filtro: {respuestas_filtro_texto}")

                data = {
                    "vacante": vacante,
                    "nombre": nombre,
                    "numero": numero,
                    "curriculum": cv,
                    "email": email,
                    "dni": dni,
                    "direccion": direccion,
                    "resumen": resumen,
                    "salario_deseado": salario_deseado,
                    "respuestas_filtro": respuestas_filtro_texto,
                    "source": "computrabajo",
                }

                try:
                    response = requests.post("http://10.20.62.94:5678/webhook/insert", json=data, timeout=10)
                    if response.status_code == 200:
                        print("Datos enviados correctamente.")
                    else:
                        print(f"Error del servidor al enviar datos: Código {response.status_code} - Respuesta: {response.text}")
                except requests.exceptions.Timeout:
                    print("Error en la petición HTTP: Timeout")
                except requests.exceptions.ConnectionError:
                    print("Error en la petición HTTP: Conexión fallida")
                except requests.exceptions.RequestException as re:
                    print(f"Error en la petición HTTP: {re}")
                except Exception as e:
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
