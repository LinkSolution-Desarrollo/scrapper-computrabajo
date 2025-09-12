from src import webdriver_setup, config
from src.scraper import login, vacancy_scraper, candidate_scraper

# --- CONFIGURATION ---
# Paste the URL of the vacancy you want to scrape here
SINGLE_VACANCY_URL = "https://ats.pandape.com/Company/Match/Matches/10488465?idvacancyfolder=69652247&matchesfilter.idvacancy=10488465"

def main_single():
    """
    Main function to scrape a single vacancy.
    """
    if not SINGLE_VACANCY_URL or "ats.pandape.com" not in SINGLE_VACANCY_URL:
        print("Error: Please set a valid Pandape vacancy URL in SINGLE_VACANCY_URL.")
        return

    driver = None
    try:
        # 1. Set up WebDriver
        driver = webdriver_setup.get_webdriver()

        # 2. Log in
        login.login(driver)

        # 3. Scrape the single vacancy
        print(f"\n{'='*20} PROCESANDO VACANTE ÚNICA {'='*20}")

        vacancy_title = vacancy_scraper.scrape_vacancy_details(driver, SINGLE_VACANCY_URL)

        if vacancy_title != "No encontrado":
            candidate_scraper.scrape_candidates_for_vacancy(driver, SINGLE_VACANCY_URL, vacancy_title)
        else:
            print(f"No se pudo obtener el título de la vacante {SINGLE_VACANCY_URL}, se omite el scraping de candidatos.")

        print(f"\n{'='*20} FIN DE LA VACANTE ÚNICA {'='*20}")

    except Exception as e:
        print(f"\nOcurrió un error fatal en el proceso: {e}")
    finally:
        if driver:
            print("\nCerrando el navegador...")
            driver.quit()
        print("Proceso finalizado.")

if __name__ == "__main__":
    main_single()
