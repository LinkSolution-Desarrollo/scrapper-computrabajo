import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

from .. import config


class CVCacheManager:
    """Gestor de caché inteligente para CVs descargados."""

    def __init__(self):
        self.cache_file = config.CACHE_CONFIG["CACHE_FILE"]
        self.cache_enabled = config.CACHE_CONFIG["CACHE_ENABLED"]
        self.max_cache_size = config.CACHE_CONFIG["MAX_CACHE_SIZE"]
        self.cache_expiry_days = config.CACHE_CONFIG["CACHE_EXPIRY_DAYS"]
        self.auto_clean = config.CACHE_CONFIG.get("AUTO_CLEAN_CACHE", True)

        if self.cache_enabled:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            # Inicializar caché
            self._cache = self._load_cache()
        else:
            self._cache = {}

    def _load_cache(self):
        """Carga el caché desde el archivo JSON."""
        if not self.cache_enabled:
            return {}

        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                # Limpiar entradas expiradas
                self._clean_expired_entries(cache_data)

                return cache_data
            else:
                return {}
        except Exception as e:
            print(f" [CACHE] Error al cargar caché: {e}")
            return {}

    def _save_cache(self):
        """Guarda el caché en el archivo JSON."""
        if not self.cache_enabled:
            return

        try:
            # Limitar tamaño del caché
            self._limit_cache_size()

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f" [CACHE] Error al guardar caché: {e}")

    def _clean_expired_entries(self, cache_data):
        """Limpia las entradas expiradas del caché."""
        current_time = time.time()
        expired_keys = []

        for url_hash, entry in cache_data.items():
            # Verificar expiración por tiempo
            cache_time = entry.get('timestamp', 0)
            days_diff = (current_time - cache_time) / (24 * 3600)

            if days_diff > self.cache_expiry_days:
                expired_keys.append(url_hash)

                # También eliminar el archivo físico si existe
                file_path = entry.get('local_path')
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f" [CACHE] Archivo expirado eliminado: {file_path}")
                    except Exception as e:
                        print(f" [CACHE] Error al eliminar archivo expirado {file_path}: {e}")

        # Remover entradas expiradas del caché
        for key in expired_keys:
            del cache_data[key]

        if expired_keys:
            print(f" [CACHE] {len(expired_keys)} entradas expiradas eliminadas")

    def _limit_cache_size(self):
        """Limita el tamaño del caché al máximo configurado."""
        if len(self._cache) <= self.max_cache_size:
            return

        # Ordenar por tiempo de acceso (más antiguos primero)
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].get('last_access', 0)
        )

        # Eliminar entradas más antiguas
        entries_to_remove = len(self._cache) - self.max_cache_size
        for i in range(entries_to_remove):
            url_hash, entry = sorted_entries[i]

            # Eliminar archivo físico
            file_path = entry.get('local_path')
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f" [CACHE] Error al eliminar archivo {file_path}: {e}")

            # Remover de caché
            del self._cache[url_hash]

        print(f" [CACHE] {entries_to_remove} entradas antiguas eliminadas (límite de tamaño)")

    def _get_url_hash(self, url):
        """Genera un hash único para una URL."""
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def is_cv_cached(self, url):
        """Verifica si un CV ya está en caché y es válido."""
        if not self.cache_enabled:
            return False

        url_hash = self._get_url_hash(url)
        entry = self._cache.get(url_hash)

        if not entry:
            return False

        # Verificar si el archivo físico existe
        file_path = entry.get('local_path')
        if not file_path or not os.path.exists(file_path):
            # Archivo físico no existe, remover de caché
            del self._cache[url_hash]
            return False

        # Verificar expiración
        cache_time = entry.get('timestamp', 0)
        current_time = time.time()
        days_diff = (current_time - cache_time) / (24 * 3600)

        if days_diff > self.cache_expiry_days:
            # Entrada expirada
            del self._cache[url_hash]
            try:
                os.remove(file_path)
                print(f" [CACHE] Archivo expirado eliminado: {file_path}")
            except Exception as e:
                print(f" [CACHE] Error al eliminar archivo expirado {file_path}: {e}")
            return False

        # Actualizar tiempo de último acceso
        entry['last_access'] = current_time
        self._save_cache()

        return True

    def add_cv_to_cache(self, url, local_path, file_size=None):
        """Agrega un CV al caché."""
        if not self.cache_enabled:
            return

        url_hash = self._get_url_hash(url)
        current_time = time.time()

        # Obtener tamaño del archivo si no se proporcionó
        if file_size is None:
            try:
                file_size = os.path.getsize(local_path)
            except Exception:
                file_size = 0

        self._cache[url_hash] = {
            'url': url,
            'local_path': local_path,
            'filename': os.path.basename(local_path),
            'file_size': file_size,
            'timestamp': current_time,
            'last_access': current_time
        }

        print(f" [CACHE] CV agregado al caché: {os.path.basename(local_path)}")
        self._save_cache()

    def get_cached_cv_path(self, url):
        """Obtiene la ruta local de un CV cacheado."""
        if not self.cache_enabled:
            return None

        url_hash = self._get_url_hash(url)
        entry = self._cache.get(url_hash)

        if entry and os.path.exists(entry['local_path']):
            entry['last_access'] = time.time()
            self._save_cache()
            return entry['local_path']

        return None

    def get_cache_stats(self):
        """Obtiene estadísticas del caché."""
        if not self.cache_enabled:
            return {"enabled": False}

        total_size = 0
        for entry in self._cache.values():
            total_size += entry.get('file_size', 0)

        return {
            "enabled": True,
            "total_entries": len(self._cache),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_size": self.max_cache_size,
            "expiry_days": self.cache_expiry_days
        }

    def clear_cache(self):
        """Limpia todo el caché."""
        if not self.cache_enabled:
            return

        # Eliminar archivos físicos
        for entry in self._cache.values():
            file_path = entry.get('local_path')
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f" [CACHE] Error al eliminar archivo {file_path}: {e}")

        # Limpiar caché en memoria
        self._cache.clear()
        print(" [CACHE] Caché limpiado completamente")

        # Guardar caché vacío
        self._save_cache()


# Instancia global del gestor de caché
cv_cache_manager = CVCacheManager()