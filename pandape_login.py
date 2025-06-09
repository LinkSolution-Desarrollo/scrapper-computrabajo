import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def login_to_pandape():
    # Initialize WebDriver
    print("Initializing Chrome WebDriver...")
    try:
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--remote-debugging-port=9222")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        print("WebDriver initialized successfully.")
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        return

    # Navigate to the URL
    url = "https://ats.pandape.com/Company/Vacancy"
    print(f"Navigating to {url}...")
    driver.get(url)

    try:
        # --- Get Credentials ---
        username = os.environ.get("PANDAPE_USERNAME")
        password = os.environ.get("PANDAPE_PASSWORD")

        if not username or not password:
            print("Error: PANDAPE_USERNAME and PANDAPE_PASSWORD environment variables must be set.")
            driver.quit()
            return

        # --- Wait for elements and login ---
        # Replace 'USERNAME_FIELD_ID', 'PASSWORD_FIELD_ID', and 'LOGIN_BUTTON_ID'
        # with the actual locators from the website.
        # It's highly recommended to use more robust selectors like ID, Name, or specific CSS selectors.

        # Example using explicit waits:
        wait = WebDriverWait(driver, 20) # Wait up to 20 seconds

        print("Looking for username field by NAME 'username'...")
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        print("Username field found. Entering username...")
        username_field.send_keys(username)

        print("Looking for password field by NAME 'password'...")
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        print("Password field found. Entering password...")
        password_field.send_keys(password)

        print("Looking for login button by XPATH '//button[contains(text(), \"Accept\")]'...")
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]")))
        print("Login button found. Clicking login button...")
        login_button.click()

        # --- Wait to observe result ---
        print("Login attempt submitted. Pausing for 10 seconds to observe...")
        time.sleep(10) # Keep browser open for 10 seconds

        # TODO: Add verification logic here (e.g., check URL, look for a logout button)
        print(f"Current URL after login attempt: {driver.current_url}")
        print("Login process complete (or attempted). Please check the browser.")

    except Exception as e:
        print(f"An error occurred during the login process: {e}")
        driver.save_screenshot("pandape_login_error.png")
        with open("pandape_login_error_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Saved screenshot and page source of the error.")

    finally:
        print("Closing the browser.")
        driver.quit()

if __name__ == "__main__":
    login_to_pandape()
