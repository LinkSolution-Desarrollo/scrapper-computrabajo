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

def download_file(url, local_folder="downloads"):
    os.makedirs(local_folder, exist_ok=True)
    filename = os.path.basename(urlparse(url).path) or f"cv_{int(time.time())}.pdf"
    local_path = os.path.join(local_folder, filename)

    try:
        s = requests.Session()
        # Pasar cookies de Selenium a requests
        for cookie in driver.get_cookies():
            s.cookies.set(cookie['name'], cookie['value'])

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": driver.current_url
        }

        response = s.get(url, headers=headers)
        response.raise_for_status()

        with open(local_path, "wb") as f:
            f.write(response.content)

        print(f"📥 Descargado: {filename}")
        return local_path
    except Exception as e:
        print(f"❌ Error al descargar {url}: {e}")
        return None

def upload_to_s3(local_path, nombre="sin_nombre", dni="sin_dni"):
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
        filename = f"{dni}{extension}"
        with open(local_path, "rb") as f:
            s3.upload_fileobj(f, bucket, filename)

        print(f"📤 Subido a MinIO: {filename}")
    except Exception as e:
        print(f"❌ Error al subir a MinIO: {e}")



# Cargar variables del entorno
load_dotenv()
usuario = os.environ.get("USUARIO")
clave = os.environ.get("CLAVE")

# Configuración de Chrome para Docker
# Configuración de Chrome
options = Options()
# Solo descomentá estas si lo necesitás
# options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/google-chrome-stable")
# options.add_argument("--headless")
# options.add_argument("--no-sandbox")
# options.add_argument("--disable-dev-shm-usage")
# options.add_argument("--disable-gpu")
# options.add_argument("--disable-extensions")
# options.add_argument("--remote-debugging-port=9222")
# options.add_argument("window-size=1920,1080")
# options.add_argument("user-agent=Mozilla/5.0")

# Usar el ChromeDriver descargado manualmente
service = Service(r"C:\tools\chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

try:
    driver.get("https://ats.pandape.com/Company/Vacancy?Pagination[PageNumber]=1&Pagination[PageSize]=1000&Order=1&IdsFilter=0&RecruitmentType=0")
    time.sleep(5)

    driver.find_element(By.ID, "Username").send_keys(usuario)
    driver.find_element(By.ID, "Password").send_keys(clave)
    driver.find_element(By.ID, "btLogin").click()
    time.sleep(10)

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

        # ---------- DATOS DE LA VACANTE DESDE VISTA PREVIA ----------
        try:
            preview_btn = driver.find_element(By.CSS_SELECTOR, "a[title='Vista previa']")
            preview_href = preview_btn.get_attribute("href")
            driver.execute_script("window.open(arguments[0]);", preview_href)
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(3)

            titulo = safe_extract_text(driver, By.CSS_SELECTOR, "h1.fw-600.color-title")
            descripcion = safe_extract_text(driver, By.CSS_SELECTOR, "div.order-1 > div.mb-20")
            requisitos = safe_extract_text(driver, By.CSS_SELECTOR, "div#Requirements")
            valorado = safe_extract_text(driver, By.CSS_SELECTOR, "div#Valued")

            print("\n--- VACANTE ---")
            print("Título:", titulo)
            print("Requisitos:", requisitos.replace("\n", " ")[:100])
            print("Valorado:", valorado.replace("\n", " ")[:100])

            data_vacante = {
                "titulo": titulo,
                "descripcion": descripcion,
                "requisitos": requisitos,
                "valorado": valorado,
                "source": "pandape"
            }

            try:
                r = requests.post("http://10.20.62.94:5678/webhook/vacant", json=data_vacante, timeout=10)
                print("✅ Vacante enviada" if r.status_code == 200 else f"❌ Error vacante {r.status_code}: {r.text}")
            except Exception as e:
                print(f"❌ Error al enviar vacante: {e}")

            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except Exception as e:
            print(f"⚠️ No se pudo abrir la vista previa: {e}")

        # ---------- CANDIDATOS ----------
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

                if cv != "No encontrado":
                    local_cv_path = download_file(cv)
                    if local_cv_path:
                        upload_to_s3(local_cv_path, nombre=nombre, dni=dni)


                dni = "No encontrado"
                try:
                    div = driver.find_element(By.XPATH, "//div[span[text()='Nacionalidad']]")
                    driver.execute_script("arguments[0].scrollIntoView(true);", div)
                    time.sleep(1)
                    dni_match = re.search(r"D\.N\.I\s*(\d+)", div.text)
                    if dni_match:
                        dni = dni_match.group(1)
                except:
                    pass

                # Aquí extraemos las respuestas del filtro
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

                print("\n--- CANDIDATO ---")
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
                    "source": "computrabajo"
                }

                try:
                    r = requests.post("http://10.20.62.94:5678/webhook/insert", json=data, timeout=10)
                    print("✅ Candidato enviado" if r.status_code == 200 else f"❌ Error candidato {r.status_code}: {r.text}")
                except Exception as e:
                    print(f"❌ Error HTTP candidato: {e}")

                time.sleep(2)
            except Exception as e:
                print(f"⚠️ Error candidato #{i}: {e}")
                continue

        print("-" * 60)
        driver.back()
        time.sleep(3)

finally:
    driver.quit()
