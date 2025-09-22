import os
import time
import requests
import boto3
from urllib.parse import urlparse
from boto3.session import Config

from . import config

def safe_extract_text(driver, by, value, default="No encontrado"):
    """Safely extracts text from a web element, scrolling it into view first."""
    try:
        element = driver.find_element(by, value)
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)  # Wait for scrolling and potential lazy loading
        return element.text.strip()
    except Exception:
        return default

def safe_extract_attribute(driver, by, value, attribute, default="No encontrado"):
    """Safely extracts an attribute from a web element, scrolling it into view first."""
    try:
        element = driver.find_element(by, value)
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        return element.get_attribute(attribute)
    except Exception:
        return default

def safe_extract_inner_html(driver, by, value, default="No encontrado"):
    """Safely extracts the innerHTML from a web element, scrolling it into view first."""
    try:
        element = driver.find_element(by, value)
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        return driver.execute_script("return arguments[0].innerHTML;", element)
    except Exception:
        return default

def download_file(driver, url, local_folder=config.DOWNLOADS_FOLDER):
    """Downloads a file from a URL using the browser's session."""
    os.makedirs(local_folder, exist_ok=True)
    filename = os.path.basename(urlparse(url).path) or f"cv_{int(time.time())}.pdf"
    local_path = os.path.join(local_folder, filename)

    try:
        s = requests.Session()
        for cookie in driver.get_cookies():
            s.cookies.set(cookie['name'], cookie['value'])

        headers = {
            "User-Agent": driver.execute_script("return navigator.userAgent;"),
            "Referer": driver.current_url
        }

        response = s.get(url, headers=headers)
        response.raise_for_status()

        with open(local_path, "wb") as f:
            f.write(response.content)

        print(f" Descargado: {filename}")
        return local_path
    except Exception as e:
        print(f" Error al descargar {url}: {e}")
        return None

def upload_to_s3(local_path, dni=None):
    """Uploads a file to an S3-compatible storage (MinIO)."""
    if not dni or dni == "No encontrado":
        print("  CV sin DNI, no se sube a MinIO")
        return

    try:
        s3 = boto3.client(
            's3',
            endpoint_url=config.MINIO_ENDPOINT,
            aws_access_key_id=config.MINIO_ACCESS_KEY,
            aws_secret_access_key=config.MINIO_SECRET_KEY,
            region_name='us-east-1',
            config=Config(signature_version='s3v4', s3={'addressing_style': 'path'})
        )

        bucket = config.MINIO_BUCKET
        extension = os.path.splitext(local_path)[1] or ".pdf"
        safe_dni = dni.replace('.', '').replace(' ', '_')
        filename = f"{safe_dni}{extension}"

        with open(local_path, "rb") as f:
            s3.upload_fileobj(f, bucket, filename)

        print(f"  Subido a MinIO: {filename}")
    except Exception as e:
        print(f"  Error al subir a MinIO: {e}")

def send_to_webhook(url, data):
    """Sends data to a specified webhook URL."""
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"API: {' Enviado' if response.status_code == 200 else f' Error {response.status_code}: {response.text}'}")
    except Exception as e:
        print(f" Error al enviar a API: {e}")
