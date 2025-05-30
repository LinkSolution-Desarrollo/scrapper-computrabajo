import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

try:
    from selenium_stealth import stealth
except ImportError:
    print("selenium-stealth not found. Consider installing with: pip install selenium-stealth")
    stealth = None

def extract_job_data():
    # --- Chrome Options Setup ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)

    # --- Apply Selenium Stealth ---
    if stealth:
        print("Applying selenium-stealth.")
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
    else:
        print("Proceeding without selenium-stealth.")

    # --- Navigate to URL ---
    start_url = "https://www.bumeran.com.ar/en-buenos-aires/capital-federal/empleos-busqueda-desarrollador.html"
    print(f"Navigating to initial URL: {start_url}")

    all_jobs_data = []
    current_page_num = 1

    try:
        driver.get(start_url)

        while True:
            print(f"\n--- Scraping Page {current_page_num} ---")
            print(f"Current URL: {driver.current_url}")

            # Allow time for dynamic content, JS execution, and Cloudflare checks
            # Increased wait time slightly for subsequent pages if needed, though 10s is generous
            print("Waiting for page to load (10 seconds)...")
            time.sleep(10)

            page_title = driver.title
            print(f"Page title: {page_title}")

            if "Cloudflare" in page_title or "Attention Required" in page_title:
                print(f"\n[WARNING] Cloudflare challenge detected on page {current_page_num}. Stopping.")
                driver.save_screenshot(f"cloudflare_page_{current_page_num}.png")
                with open(f"cloudflare_page_{current_page_num}_source.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("Saved Cloudflare page screenshot and source.")
                break

            # --- CSS Selectors ---
            job_listing_selector = "div.sc-iNwVbF"
            job_title_selector = "a.sc-ddcOto h2"
            company_name_selector = "div.sc-lffWgi h3"
            job_location_selector = "div.sc-fPbjcq i[name='icon-light-location-pin'] + span > h3"
            job_link_selector = "a.sc-ddcOto"

            active_next_page_button_selector = "a.sc-dzVpKk.hFOZsP:not([disabled])"

            job_elements = driver.find_elements(By.CSS_SELECTOR, job_listing_selector)
            print(f"Found {len(job_elements)} job listings on page {current_page_num}.")

            if not job_elements and current_page_num == 1 : # Only save if no jobs on first page
                print("No job listings found on the first page. Saving page source for debugging.")
                driver.save_screenshot("no_jobs_found_page_1.png")
                with open("no_jobs_found_page_1_source.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                break # Stop if first page has no jobs

            for index, job_element in enumerate(job_elements):
                job_data = {'title': 'Not found', 'company': 'Not found', 'location': 'Not found', 'link': 'Not found', 'page': current_page_num}

                try:
                    title_element = job_element.find_element(By.CSS_SELECTOR, job_title_selector)
                    job_data['title'] = title_element.text.strip()
                except NoSuchElementException:
                    print(f"Page {current_page_num}, Job {index+1}: Title not found")
                except Exception as e:
                    print(f"Page {current_page_num}, Job {index+1}: Error extracting title - {e}")

                try:
                    company_h3_elements = job_element.find_elements(By.CSS_SELECTOR, company_name_selector)
                    found_company = False
                    for h3_element in company_h3_elements:
                        text = h3_element.text.strip()
                        if text and not text.lower().startswith("publicado") and not text.lower().startswith("actualizado"):
                            job_data['company'] = text
                            found_company = True
                            break
                    if not found_company:
                         print(f"Page {current_page_num}, Job {index+1}: Company name not found or only date-like h3s")
                except NoSuchElementException:
                     print(f"Page {current_page_num}, Job {index+1}: Company h3s not found")
                except Exception as e:
                    print(f"Page {current_page_num}, Job {index+1}: Error extracting company - {e}")

                try:
                    location_element = job_element.find_element(By.CSS_SELECTOR, job_location_selector)
                    job_data['location'] = location_element.text.strip()
                except NoSuchElementException:
                    print(f"Page {current_page_num}, Job {index+1}: Location not found")
                except Exception as e:
                    print(f"Page {current_page_num}, Job {index+1}: Error extracting location - {e}")

                try:
                    link_element = job_element.find_element(By.CSS_SELECTOR, job_link_selector)
                    job_data['link'] = link_element.get_attribute('href')
                except NoSuchElementException:
                    print(f"Page {current_page_num}, Job {index+1}: Link not found")
                except Exception as e:
                    print(f"Page {current_page_num}, Job {index+1}: Error extracting link - {e}")
                
                all_jobs_data.append(job_data)

            # --- Pagination Logic ---
            try:
                next_page_button = driver.find_element(By.CSS_SELECTOR, active_next_page_button_selector)
                print(f"Found active 'Next page' button. Clicking...")
                driver.execute_script("arguments[0].click();", next_page_button) # JS click as a fallback
                current_page_num += 1
                # Wait is already at the beginning of the loop
            except NoSuchElementException:
                print("No active 'Next page' button found. This is the last page or only page.")
                break # Exit loop if no next page button is active
            except Exception as e:
                print(f"Error clicking next page button: {e}. Stopping pagination.")
                break

        print("\n--- End of All Data Extraction ---")

    except Exception as e:
        print(f"An unexpected error occurred during script execution: {e}")
        try:
            driver.save_screenshot("unexpected_error_page.png")
            with open("unexpected_error_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Saved page state at time of unexpected error.")
        except Exception as e_save:
            print(f"Could not save page state during error handling: {e_save}")
            
    finally:
        print("\nClosing browser.")
        driver.quit()

    return all_jobs_data

if __name__ == "__main__":
    extracted_data = extract_job_data()
    output_filename = "ofertas_desarrollador.json"

    if extracted_data:
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        print(f"\nSuccessfully extracted {len(extracted_data)} job listings from all pages and saved to {output_filename}")
    else:
        print("\nNo job data extracted. JSON file not created.")
