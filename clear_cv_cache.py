#!/usr/bin/env python3
"""
Script para limpiar el caché de CVs si es necesario.
Útil para mantenimiento y limpieza de archivos antiguos.
"""

import os
import sys
import shutil

# Agregar el directorio src al path para poder importar
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src import config
from src.scraper.cv_cache_manager import cv_cache_manager

def clear_downloads_folder():
    """Limpia la carpeta de downloads."""
    downloads_folder = config.DOWNLOADS_FOLDER

    if os.path.exists(downloads_folder):
        confirm = input(f"¿Estás seguro de que quieres eliminar toda la carpeta '{downloads_folder}'? (s/n): ")
        if confirm.lower() == 's':
            try:
                shutil.rmtree(downloads_folder)
                print(f" [CLEANUP] Carpeta '{downloads_folder}' eliminada completamente")
            except Exception as e:
                print(f" [ERROR] Error al eliminar carpeta: {e}")
        else:
            print(" [CLEANUP] Operación cancelada")
    else:
        print(f" [CLEANUP] La carpeta '{downloads_folder}' no existe")

def clear_cv_cache():
    """Limpia el caché de CVs."""
    confirm = input("¿Estás seguro de que quieres limpiar el caché de CVs? (s/n): ")
    if confirm.lower() == 's':
        cv_cache_manager.clear_cache()
        print(" [CLEANUP] Caché de CVs limpiado")
    else:
        print(" [CLEANUP] Operación cancelada")

def show_cache_stats():
    """Muestra estadísticas del caché."""
    stats = cv_cache_manager.get_cache_stats()
    print("=== ESTADÍSTICAS DEL CACHÉ ===")
    if stats["enabled"]:
        print(f"Estado: Habilitado")
        print(f"Entradas totales: {stats['total_entries']}")
        print(f"Tamaño total: {stats['total_size_mb']} MB")
        print(f"Límite máximo: {stats['max_size']} entradas")
        print(f"Días de expiración: {stats['expiry_days']}")
    else:
        print("Estado: Deshabilitado")

def main():
    print("=== GESTIÓN DE CACHÉ DE CVs ===")

    while True:
        print("\nOpciones:")
        print("1. Ver estadísticas del caché")
        print("2. Limpiar caché de CVs")
        print("3. Limpiar carpeta de downloads")
        print("4. Salir")

        opcion = input("\nSelecciona una opción (1-4): ")

        if opcion == "1":
            show_cache_stats()
        elif opcion == "2":
            clear_cv_cache()
        elif opcion == "3":
            clear_downloads_folder()
        elif opcion == "4":
            print(" [CLEANUP] Saliendo...")
            sys.exit(0)
        else:
            print(" [ERROR] Opción no válida")

if __name__ == "__main__":
    main()