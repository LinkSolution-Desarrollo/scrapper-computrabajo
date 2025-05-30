# scraper.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv

def scrape_computrabajo():
    # ChromeDriver should be in your PATH or specify the executable_path
    # Example for specifying path: driver = webdriver.Chrome(executable_path='/path/to/chromedriver')
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    url = "https://ar.computrabajo.com/trabajo-de-desarrollador-en-capital-federal"
    driver.get(url)

    all_jobs_data = []

    # --- Optional: Handle cookie consent pop-up ---
    try:
        cookie_accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")) 
        )
        cookie_accept_button.click()
        print("Cookie consent button clicked.")
        time.sleep(2) 
    except TimeoutException:
        print("Cookie consent button not found or not clickable within timeout.")
    except Exception as e:
        print(f"An error occurred while trying to click cookie button: {e}")
    # --- End optional cookie handling ---


    page_count = 1
    while True:
        print(f"Scraping page {page_count}...")
        try:
            # Wait for job offers to be present on the page
            # Corrected container ID: "offersGridOfferContainer"
            job_offers_container = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "offersGridOfferContainer"))
            )
            # Corrected selector: job offers are article elements with class "box_offer"
            job_offers = job_offers_container.find_elements(By.CSS_SELECTOR, "article.box_offer")
            
            if not job_offers:
                print("No job offers found on this page. Might be the end.")
                break

            for offer_element in job_offers:
                job_data = {}
                try:
                    # Title and Link
                    title_element = offer_element.find_element(By.CSS_SELECTOR, "h2 a.js-o-link")
                    job_data['title'] = title_element.text.strip()
                    job_data['link'] = title_element.get_attribute('href')

                    # Company
                    try:
                        company_element = offer_element.find_element(By.CSS_SELECTOR, "a[offer-grid-article-company-url]")
                        job_data['company'] = company_element.text.strip() if company_element.text.strip() else 'N/A (Empresa Confidencial)'
                    except NoSuchElementException:
                        try:
                            # Fallback for companies like SOLUTIX S.A. that are not a link with the specific attribute
                            company_p_element = offer_element.find_element(By.XPATH, "./p[contains(@class, 'fs16')][1]") # First p tag with fs16 class
                            job_data['company'] = company_p_element.text.splitlines()[0].strip() if company_p_element.text.strip() else 'N/A (Empresa Confidencial)'
                        except NoSuchElementException:
                            job_data['company'] = 'N/A (Not Found)'
                    
                    # Location 
                    try:
                        # Selects the span within the second <p> that has classes 'fs16 fc_base mt5'
                        location_element = offer_element.find_element(By.XPATH, "./p[contains(@class, 'fs16') and contains(@class, 'fc_base') and contains(@class, 'mt5') and not(contains(@class, 'dFlex'))]/span")
                        job_data['location'] = location_element.text.strip()
                    except NoSuchElementException:
                        # Fallback if the above is not found, try any span in a p.fs16.fc_base.mt5 (might be less accurate)
                        try:
                            location_element = offer_element.find_element(By.CSS_SELECTOR, "p.fs16.fc_base.mt5 span")
                            job_data['location'] = location_element.text.strip() if location_element.text.strip() else 'N/A (Fallback)'
                        except NoSuchElementException:
                            job_data['location'] = 'N/A (Not Found)'


                    # Description Summary - Made optional as it's not in the list item directly
                    job_data['description_summary'] = 'N/A (Not in list view)'
                    
                    all_jobs_data.append(job_data)

                except NoSuchElementException as e:
                    # This will catch if the TITLE fails, which is critical. Other fields have their own try-except.
                    print(f"Critical element (likely title) not found for a job posting: {e} - Offer text: {offer_element.text[:100]}")
                    # Fallback for critical elements like title if the initial find_element fails
                    try:
                        if 'title' not in job_data or not job_data['title']: # Ensure title is captured
                             title_element_fallback = offer_element.find_element(By.CSS_SELECTOR, "h2 a.js-o-link") # Re-attempt title
                             job_data['title'] = title_element_fallback.text.strip()
                             job_data['link'] = title_element_fallback.get_attribute('href')
                        
                        # Ensure other fields have default N/A if not already set
                        job_data.setdefault('company', 'N/A (Fallback)')
                        job_data.setdefault('location', 'N/A (Fallback)')
                        job_data.setdefault('description_summary', 'N/A (Fallback)')

                        if job_data.get('title'): # Only append if title is found
                            all_jobs_data.append(job_data)
                        else:
                            print(f"Fallback failed to retrieve title for offer: {offer_element.text[:100]}")
                    except Exception as fallback_e:
                        print(f"Outer fallback failed for a job posting: {fallback_e} - Offer text: {offer_element.text[:100]}")
                    continue
                except Exception as e:
                    print(f"An unexpected error occurred while processing a job offer: {e}")
                    continue

            print(f"Found {len(job_offers)} jobs on page {page_count}.")

        except TimeoutException:
            print("Timed out waiting for job offers to load. This might be the last page or an issue.")
            print(f"Current URL: {driver.current_url}")
            print(f"Page source length: {len(driver.page_source)}")
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Saved page source to debug_page_source.html")
            break
        except Exception as e:
            print(f"An error occurred during scraping page {page_count}: {e}")
            break

        # --- Pagination ---
        try:
            # Corrected selector for "Siguiente" (Next) button
            next_button_candidates = driver.find_elements(By.CSS_SELECTOR, "span.b_primary.buildLink[data-path*='?p=']")
            next_button = None
            for candidate in next_button_candidates:
                if "Siguiente" in candidate.get_attribute("title"):
                    next_button = candidate
                    break
            
            if next_button and "disabled" not in next_button.get_attribute("class"):
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(next_button))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                time.sleep(1) 
                driver.execute_script("arguments[0].click();", next_button)
                
                print("Navigating to the next page...")
                page_count += 1
                WebDriverWait(driver, 20).until(
                    EC.staleness_of(job_offers_container) 
                )
                time.sleep(1) 
            else:
                print("No 'Next page' button found, or it is disabled. Assuming it's the last page.")
                break
        except TimeoutException:
            print("Timeout waiting for next page button or page to load. Assuming it's the last page.")
            break
        except Exception as e:
            print(f"Error clicking next page: {e}")
            break
            
    driver.quit()

    # --- Output Data ---
    if all_jobs_data:
        print(f"\nTotal jobs scraped: {len(all_jobs_data)}")
        keys = all_jobs_data[0].keys()
        with open('job_listings.csv', 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_jobs_data)
        print("Data successfully saved to job_listings.csv")
    else:
        print("No job data was scraped.")

if __name__ == '__main__':
    scrape_computrabajo()
