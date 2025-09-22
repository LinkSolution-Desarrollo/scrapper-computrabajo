import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def get_webdriver():
    """Configures and returns a Selenium WebDriver instance."""
    options = Options()
    chrome_bin_path = os.getenv("CHROME_BIN")

    if chrome_bin_path:
        options.binary_location = chrome_bin_path
    else:
        # Fallback for local execution if CHROME_BIN is not set
        default_chrome_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files\\Google\\Chrome_CFT\\chrome-win64\\chrome.exe"
        ]
        for path in default_chrome_paths:
            if os.path.exists(path):
                options.binary_location = path
                break
        if not getattr(options, 'binary_location', None) and os.name == 'posix':
            default_linux_path = "/usr/bin/google-chrome-stable"
            if os.path.exists(default_linux_path):
                options.binary_location = default_linux_path

    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")

    try:
        print(" Configurando ChromeDriver usando webdriver-manager...")
        service = Service(ChromeDriverManager().install())
    except Exception as e:
        print(f" Error configurando ChromeDriver con webdriver-manager: {e}")
        print("Volviendo a la configuración por defecto de ChromeDriver en el PATH.")
        service = Service()

    driver = webdriver.Chrome(service=service, options=options)
    return driver
