#!/usr/bin/env python3
"""
Script para limpiar manualmente archivos antiguos del directorio de descargas.
Útil para liberar espacio en disco cuando sea necesario.
"""

import os
import sys

# Agregar el directorio src al path para poder importar
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src import config, utils

def main():
    print("LIMPIEZA MANUAL DE ARCHIVOS DE DESCARGAS")
    print("=" * 50)

    # Mostrar estadísticas actuales
    downloads_folder = config.DOWNLOADS_FOLDER
    if os.path.exists(downloads_folder):
        files = [f for f in os.listdir(downloads_folder) if os.path.isfile(os.path.join(downloads_folder, f))]
        total_files = len(files)

        if total_files > 0:
            print(f"Archivos actuales en '{downloads_folder}': {total_files}")

            # Calcular espacio ocupado
            total_size = 0
            for filename in files:
                file_path = os.path.join(downloads_folder, filename)
                total_size += os.path.getsize(file_path)

            total_size_mb = total_size / (1024 * 1024)
            print(f"Espacio ocupado: {total_size_mb:.2f} MB")
        else:
            print(f"El directorio '{downloads_folder}' está vacío")
            return
    else:
        print(f"El directorio '{downloads_folder}' no existe")
        return

    print("\nOPCIONES DE LIMPIEZA:")
    print("1. Limpiar archivos de más de 1 hora (recomendado)")
    print("2. Limpiar archivos de más de 6 horas")
    print("3. Limpiar archivos de más de 24 horas")
    print("4. Limpiar TODOS los archivos (¡CUIDADO!)")

    try:
        choice = input("\nSelecciona una opción (1-4): ").strip()

        if choice == "1":
            max_age_hours = 1
            print("Limpiando archivos de más de 1 hora...")
        elif choice == "2":
            max_age_hours = 6
            print("Limpiando archivos de más de 6 horas...")
        elif choice == "3":
            max_age_hours = 24
            print("Limpiando archivos de más de 24 horas...")
        elif choice == "4":
            confirm = input("¿Estás seguro de que quieres eliminar TODOS los archivos? (si/no): ")
            if confirm.lower() in ("si", "s"):
                max_age_hours = -1  # Todos los archivos
                print("Eliminando TODOS los archivos...")
            else:
                print("Operación cancelada")
                return
        else:
            print("Opción no válida")
            return

        # Ejecutar limpieza
        cleaned_count = utils.cleanup_old_downloads(max_age_hours=max_age_hours)

        if cleaned_count > 0:
            print(f"\nLimpieza completada: {cleaned_count} archivos eliminados")
        else:
            print("\nNo se encontraron archivos para limpiar con los criterios seleccionados")

    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario")
    except Exception as e:
        print(f"\nError durante la limpieza: {e}")

if __name__ == "__main__":
    main()