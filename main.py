from src import webdriver_setup, config
from src.scraper import login, vacancy_scraper, candidate_scraper
from src import utils

@utils.measure_time("main_process")
def main():
    """
    Main function to orchestrate the web scraping process with performance monitoring.
    """
    driver = None
    try:
        # Initialize performance monitoring
        utils.start_performance_monitoring()

        print(" [MAIN] Iniciando proceso de scraping optimizado...")

        # Limpiar archivos antiguos antes de comenzar
        print(" [CLEANUP] Limpiando archivos antiguos del directorio de descargas...")
        utils.cleanup_old_downloads(max_age_hours=config.SCRAPING_CONFIG["DOWNLOADS_CLEANUP_MAX_AGE_HOURS"])  # Limpiar archivos de más de 1 hora

        # 1. Set up WebDriver
        driver = webdriver_setup.get_webdriver()

        # 2. Log in
        login_success = login.login(driver)
        if not login_success:
            print(" [ERROR] No se pudo iniciar sesión. Proceso terminado.")
            return

        # 3. Get all vacancy links
        vacancy_links = vacancy_scraper.get_all_vacancy_links(driver)
        if not vacancy_links:
            print(" [ERROR] No se encontraron vacantes. Proceso terminado.")
            return

        print(f" [MAIN] Procesando {len(vacancy_links)} vacantes...")

        # 4. Loop through each vacancy
        for i, vacancy_url in enumerate(vacancy_links):
            print(f"\n{'='*20} [VACANTE {i + 1}/{len(vacancy_links)}] {'='*20}")

            # It's better to scrape vacancy details and then candidates
            # to ensure we have the correct title.
            vacancy_title = vacancy_scraper.scrape_vacancy_details(driver, vacancy_url)

            if vacancy_title != "No encontrado":
                candidate_scraper.scrape_candidates_for_vacancy(driver, vacancy_url, vacancy_title)
            else:
                print(f" [SKIP] No se pudo obtener el título de la vacante {vacancy_url}, se omite el scraping de candidatos.")

            print(f"{'='*20} [FIN VACANTE {i + 1}/{len(vacancy_links)}] {'='*20}")

        # Show performance summary
        print("\n" + "="*50)
        print(utils.get_performance_summary())
        print("="*50)

    except Exception as e:
        print(f" [FATAL] Ocurrió un error fatal en el proceso principal: {e}")
    finally:
        if driver:
            print(" [CLEANUP] Cerrando el navegador...")
            driver.quit()

        # Limpiar archivos antiguos al finalizar
        print(" [CLEANUP] Realizando limpieza final de archivos antiguos...")
        utils.cleanup_old_downloads(max_age_hours=config.SCRAPING_CONFIG["DOWNLOADS_CLEANUP_MAX_AGE_HOURS"])  # Limpiar archivos de más de 1 hora

        print(" [MAIN] Proceso finalizado.")

if __name__ == "__main__":
    main()
