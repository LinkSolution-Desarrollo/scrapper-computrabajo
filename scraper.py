import os
import requests
from ftplib import FTP
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

# Datos del FTP desde .env
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
FTP_DIR = os.getenv("FTP_DIR", "/")  # Carpeta destino en FTP

def download_file(url, local_folder="downloads"):
    os.makedirs(local_folder, exist_ok=True)
    filename = os.path.basename(urlparse(url).path)
    local_path = os.path.join(local_folder, filename)

    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(response.content)
        print(f"Descargado: {filename}")
        return local_path
    except Exception as e:
        print(f"Error descargando {url}: {e}")
        return None

def upload_to_ftp(local_path):
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.cwd(FTP_DIR)
        with open(local_path, 'rb') as f:
            ftp.storbinary(f"STOR {os.path.basename(local_path)}", f)
        ftp.quit()
        print(f"Subido a FTP: {os.path.basename(local_path)}")
    except Exception as e:
        print(f"Error subiendo a FTP: {e}")

# 🎯 Ejemplo de uso:
cv_urls = [
    "https://example.com/uploads/cv1.pdf",
    "https://example.com/uploads/cv2.pdf"
]

for url in cv_urls:
    file_path = download_file(url)
    if file_path:
        upload_to_ftp(file_path)
