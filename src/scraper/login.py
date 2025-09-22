import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from src import config

def login(driver):
    """Logs into the platform using credentials from config."""
    print("Iniciando sesión...")
    driver.get(config.LOGIN_URL)
    time.sleep(5)

    driver.find_element(By.ID, "Username").send_keys(config.USUARIO)
    driver.find_element(By.ID, "Password").send_keys(config.CLAVE)
    driver.find_element(By.ID, "btLogin").click()
    time.sleep(10)  # Wait for login and potential redirection

    try:
        # Handle cookie banner
        driver.find_element(By.ID, "AllowCookiesButton").click()
        time.sleep(2)
        print("Banner de cookies aceptado.")
    except NoSuchElementException:
        print("No se encontró el banner de cookies o no fue necesario.")

    print("Inicio de sesión completado.")
