from src import webdriver_setup, config
from src.scraper import login, vacancy_scraper, candidate_scraper

def main():
    """
    Main function to orchestrate the web scraping process.
    """
    driver = None
    try:
        # 1. Set up WebDriver
        driver = webdriver_setup.get_webdriver()

        # 2. Log in
        login.login(driver)

        # 3. Get all vacancy links
        vacancy_links = vacancy_scraper.get_all_vacancy_links(driver)

        # 4. Loop through each vacancy
        for i, vacancy_url in enumerate(vacancy_links):
            print(f"\n{'='*20} PROCESANDO VACANTE {i + 1}/{len(vacancy_links)} {'='*20}")

            # It's better to scrape vacancy details and then candidates
            # to ensure we have the correct title.
            vacancy_title = vacancy_scraper.scrape_vacancy_details(driver, vacancy_url)

            if vacancy_title != "No encontrado":
                candidate_scraper.scrape_candidates_for_vacancy(driver, vacancy_url, vacancy_title)
            else:
                print(f"No se pudo obtener el título de la vacante {vacancy_url}, se omite el scraping de candidatos.")

            print(f"\n{'='*20} FIN DE LA VACANTE {i + 1}/{len(vacancy_links)} {'='*20}")

    except Exception as e:
        print(f"\nOcurrió un error fatal en el proceso principal: {e}")
    finally:
        if driver:
            print("\nCerrando el navegador...")
            driver.quit()
        print("Proceso finalizado.")

if __name__ == "__main__":
    main()
