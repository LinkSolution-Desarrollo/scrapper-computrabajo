# -*- coding: utf-8 -*-
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

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

def scrape_vacante(driver):
    titulo = safe_extract_text(driver, By.CSS_SELECTOR, "h1.fw-600.color-title")
    descripcion_elements = driver.find_elements(By.CSS_SELECTOR, "div.order-1 > div.mb-20")
    descripcion = "\n".join([elem.text for elem in descripcion_elements if elem.text.strip()]) if descripcion_elements else "No encontrado"
    requisitos_div = driver.find_elements(By.XPATH, "//h3[contains(text(), 'Requisitos')]/following-sibling::div[1]")
    requisitos = requisitos_div[0].text.strip() if requisitos_div else safe_extract_text(driver, By.CSS_SELECTOR, "div#Requirements")
    valorado_div = driver.find_elements(By.XPATH, "//h3[contains(text(), 'Valorado')]/following-sibling::div[1]")
    valorado = valorado_div[0].text.strip() if valorado_div else safe_extract_text(driver, By.CSS_SELECTOR, "div#Valued")

    return {
        "titulo": titulo,
        "descripcion": descripcion,
        "requisitos": requisitos,
        "valorado": valorado,
        "source": "pandape"
    }

def scrape_candidato(driver):
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
        pass
    direccion = safe_extract_text(driver, By.CSS_SELECTOR, "span.js_CandidateAddress")
    resumen = safe_extract_text(driver, By.CSS_SELECTOR, "div#Summary p.text-break-word")
    salario_deseado_elements = driver.find_elements(By.XPATH, "//div[span[contains(., 'Salario deseado') or contains(., 'Desired salary')]]/div[contains(@class, 'col-9')]/div")
    salario_deseado = salario_deseado_elements[0].text.strip() if salario_deseado_elements else "No encontrado"
    xpath_fuente = "//img[contains(@src, '/images/publishers/icons/')]/following-sibling::span"
    fuente_candidato = "Fuente no especificada"
    try:
        fuente_element = driver.find_element(By.XPATH, xpath_fuente)
        fuente_candidato = fuente_element.text.strip() if fuente_element and fuente_element.text.strip() else "Fuente no especificada"
    except NoSuchElementException:
        print(" No se encontró el elemento de la fuente del candidato usando XPath.")
    except Exception as e_fuente:
        print(f" Error al extraer la fuente del candidato: {e_fuente}")

    return {
        "nombre": nombre,
        "numero": numero,
        "curriculum_url": cv_url,
        "email": email,
        "dni": dni,
        "direccion": direccion,
        "resumen": resumen,
        "salario_deseado": salario_deseado,
        "source": fuente_candidato
    }
