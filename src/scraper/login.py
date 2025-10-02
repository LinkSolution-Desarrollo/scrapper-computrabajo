import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src import config

def login(driver):
    """Logs into the platform using credentials from config with improved error handling."""
    print(" [LOGIN] Iniciando sesión...")

    try:
        driver.get(config.LOGIN_URL)
        time.sleep(config.SCRAPING_CONFIG["DEFAULT_WAIT_TIME"])

        # Wait for login form and fill credentials
        WebDriverWait(driver, config.SCRAPING_CONFIG["LONG_WAIT_TIME"]).until(
            EC.presence_of_element_located((By.ID, "Username"))
        ).send_keys(config.USUARIO)

        driver.find_element(By.ID, "Password").send_keys(config.CLAVE)
        driver.find_element(By.ID, "btLogin").click()

        # Wait for login completion
        time.sleep(config.SCRAPING_CONFIG["LONG_WAIT_TIME"])

        # Handle cookie banner if present
        try:
            cookie_button = WebDriverWait(driver, config.SCRAPING_CONFIG["DEFAULT_WAIT_TIME"]).until(
                EC.element_to_be_clickable((By.ID, "AllowCookiesButton"))
            )
            cookie_button.click()
            time.sleep(config.SCRAPING_CONFIG["DEFAULT_WAIT_TIME"])
            print(" [LOGIN] Banner de cookies aceptado.")
        except (NoSuchElementException, TimeoutException):
            print(" [LOGIN] No se encontró el banner de cookies o no fue necesario.")

        print(" [LOGIN] Inicio de sesión completado exitosamente.")
        return True

    except Exception as e:
        print(f" [ERROR] Error durante el inicio de sesión: {e}")
        return False
