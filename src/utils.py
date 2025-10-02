import os
import time
import requests
import boto3
from urllib.parse import urlparse
from boto3.session import Config
from functools import wraps

from . import config

def safe_extract_text(driver, by, value, default="No encontrado"):
    """Safely extracts text from a web element, scrolling it into view first."""
    try:
        element = driver.find_element(by, value)
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(config.SCRAPING_CONFIG["DEFAULT_WAIT_TIME"] * 0.3)  # Optimized wait time
        return element.text.strip()
    except Exception:
        return default

def safe_extract_attribute(driver, by, value, attribute, default="No encontrado"):
    """Safely extracts an attribute from a web element, scrolling it into view first."""
    try:
        element = driver.find_element(by, value)
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(config.SCRAPING_CONFIG["DEFAULT_WAIT_TIME"] * 0.3)  # Optimized wait time
        return element.get_attribute(attribute)
    except Exception:
        return default

def safe_extract_inner_html(driver, by, value, default="No encontrado"):
    """Safely extracts the innerHTML from a web element, scrolling it into view first."""
    try:
        element = driver.find_element(by, value)
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(config.SCRAPING_CONFIG["DEFAULT_WAIT_TIME"] * 0.3)  # Optimized wait time
        return driver.execute_script("return arguments[0].innerHTML;", element)
    except Exception:
        return default

def download_file(driver, url, local_folder=config.DOWNLOADS_FOLDER):
    """Downloads a file from a URL using the browser's session with rate limiting."""
    os.makedirs(local_folder, exist_ok=True)
    filename = os.path.basename(urlparse(url).path) or f"cv_{int(time.time())}.pdf"
    local_path = os.path.join(local_folder, filename)

    for attempt in range(config.SCRAPING_CONFIG["MAX_RETRIES"]):
        try:
            # Rate limiting
            time.sleep(config.SCRAPING_CONFIG["RATE_LIMIT_DELAY"])

            s = requests.Session()
            for cookie in driver.get_cookies():
                s.cookies.set(cookie['name'], cookie['value'])

            headers = {
                "User-Agent": driver.execute_script("return navigator.userAgent;"),
                "Referer": driver.current_url
            }

            response = s.get(url, headers=headers, timeout=config.SCRAPING_CONFIG["DOWNLOAD_TIMEOUT"])
            response.raise_for_status()

            with open(local_path, "wb") as f:
                f.write(response.content)

            print(f" [DOWNLOAD] Archivo descargado: {filename}")
            return local_path

        except Exception as e:
            if attempt < config.SCRAPING_CONFIG["MAX_RETRIES"] - 1:
                wait_time = (attempt + 1) * 2
                print(f" [RETRY] Error al descargar {filename}, reintento {attempt + 1}/{config.SCRAPING_CONFIG['MAX_RETRIES']} en {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                print(f" [ERROR] Error definitivo al descargar {url}: {e}")
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
    """Sends data to a specified webhook URL with retry logic."""
    for attempt in range(config.SCRAPING_CONFIG["MAX_RETRIES"]):
        try:
            # Rate limiting
            time.sleep(config.SCRAPING_CONFIG["RATE_LIMIT_DELAY"])

            response = requests.post(
                url,
                json=data,
                timeout=config.SCRAPING_CONFIG["WEBHOOK_TIMEOUT"]
            )

            if response.status_code == 200:
                print(f" [WEBHOOK] Datos enviados exitosamente")
                return True
            else:
                print(f" [WEBHOOK] Error HTTP {response.status_code}: {response.text}")

        except Exception as e:
            if attempt < config.SCRAPING_CONFIG["MAX_RETRIES"] - 1:
                wait_time = (attempt + 1) * 2
                print(f" [RETRY] Error enviando webhook, reintento {attempt + 1}/{config.SCRAPING_CONFIG['MAX_RETRIES']} en {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                print(f" [ERROR] Error definitivo enviando webhook: {e}")
                return False

    return False

# Performance monitoring utilities
_performance_metrics = {
    "start_time": None,
    "operations": [],
    "current_operation": None
}

def start_performance_monitoring():
    """Initialize performance monitoring."""
    _performance_metrics["start_time"] = time.time()
    _performance_metrics["operations"] = []
    print(" [PERF] Iniciando monitoreo de rendimiento...")

def measure_time(operation_name):
    """Decorator to measure execution time of functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            _performance_metrics["current_operation"] = operation_name
            print(f" [PERF] Iniciando operación: {operation_name}")

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                _performance_metrics["operations"].append({
                    "operation": operation_name,
                    "duration": execution_time,
                    "success": True
                })
                print(f" [PERF] Operación '{operation_name}' completada en {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                _performance_metrics["operations"].append({
                    "operation": operation_name,
                    "duration": execution_time,
                    "success": False,
                    "error": str(e)
                })
                print(f" [PERF] Operación '{operation_name}' falló en {execution_time:.2f}s: {e}")
                raise

        return wrapper
    return decorator

def get_performance_summary():
    """Get a summary of performance metrics."""
    if not _performance_metrics["operations"]:
        return "No hay métricas de rendimiento disponibles."

    total_time = time.time() - _performance_metrics["start_time"]
    successful_ops = [op for op in _performance_metrics["operations"] if op["success"]]
    failed_ops = [op for op in _performance_metrics["operations"] if not op["success"]]

    summary = f"""
=== RESUMEN DE RENDIMIENTO ===
Tiempo total: {total_time:.2f} segundos
Operaciones exitosas: {len(successful_ops)}
Operaciones fallidas: {len(failed_ops)}
Tasa de éxito: {(len(successful_ops) / len(_performance_metrics['operations']) * 100):.1f}%

Operaciones por tipo:
"""
    operation_times = {}
    for op in _performance_metrics["operations"]:
        op_name = op["operation"]
        if op_name not in operation_times:
            operation_times[op_name] = []
        operation_times[op_name].append(op["duration"])

    for op_name, times in operation_times.items():
        avg_time = sum(times) / len(times)
        max_time = max(times)
        summary += f"  {op_name}: {len(times)} ejecuciones, promedio {avg_time:.2f}s, máximo {max_time:.2f}s\n"

    return summary
