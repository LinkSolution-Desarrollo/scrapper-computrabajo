import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
try:
    from selenium_stealth import stealth
except ImportError:
    print("selenium-stealth not found. Proceeding without it. Cloudflare bypass might fail.")
    stealth = None

def inspect_job_site():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)

    if stealth:
        print("Applying selenium-stealth.")
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)

    url = "https://www.bumeran.com.ar/en-buenos-aires/capital-federal/empleos-busqueda-desarrollador.html"
    print(f"Navigating to {url}")

    try:
        driver.get(url)
        print("Waiting for page to load (10 seconds)...")
        time.sleep(10)

        page_title = driver.title
        print(f"\nPage title: {page_title}")

        if "Cloudflare" in page_title or "Attention Required" in page_title:
            print("\n[WARNING] Cloudflare challenge likely detected again.")
            # page_source = driver.page_source[:2000]
            # print(f"Page source snippet: {page_source}")
            driver.save_screenshot("debug_page_source.png") # Save screenshot if Cloudflare or error
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        else:
            print("\nSuccessfully accessed the target page.")
            # page_source = driver.page_source # Already have it from previous step, not needed to save again unless debugging

            print("\n--- Identified Selectors and Data Extraction ---")

            # Main container for all job listings
            # listings_container_id = "listado-avisos"
            # listings_container = driver.find_element(By.ID, listings_container_id)

            # Main container for each job listing (relative to listings_container or document)
            job_listing_selector = "div.sc-iNwVbF" # Each individual job card

            # Job title (relative to each job_listing_element)
            job_title_selector = "a.sc-ddcOto h2"

            # Company name (relative to each job_listing_element)
            company_name_selector = "div.sc-lffWgi h3" # This might be too broad, let's test
                                                    # More specific: "div.sc-lffWgi span.sc-fGSyRc > h3"
                                                    # Or based on img sibling: "img.sc-jFpLkX + div.sc-lmrgJh h3"

            # Job location (relative to each job_listing_element)
            # This selector looks for an h3 that is a sibling of a span that is a sibling of an i tag with name="icon-light-location-pin"
            job_location_selector = "div.sc-fPbjcq i[name='icon-light-location-pin'] + span > h3"

            # Link to job details page (extract href from this element, relative to job_listing_element)
            job_link_selector = "a.sc-ddcOto"

            print(f"\nUsing Main Job Listing Container CSS Selector: {job_listing_selector}")
            job_elements = driver.find_elements(By.CSS_SELECTOR, job_listing_selector)
            print(f"Found {len(job_elements)} job listings.")

            if not job_elements:
                print("\nNo job listings found with the specified selector. Saving page source for debugging.")
                with open("debug_no_jobs_page_source.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                driver.save_screenshot("debug_no_jobs_screenshot.png")


            for index, job_element in enumerate(job_elements):
                print(f"\n--- Job Listing {index + 1} ---")
                title = "Not found"
                company = "Not found"
                location = "Not found"
                link = "Not found"

                try:
                    title_element = job_element.find_element(By.CSS_SELECTOR, job_title_selector)
                    title = title_element.text.strip()
                except Exception:
                    pass # Keep "Not found"

                try:
                    # Trying a more specific company selector first
                    # company_element = job_element.find_element(By.CSS_SELECTOR, "div.sc-lffWgi span.sc-fGSyRc > h3")
                    # Simpler one for now based on direct observation of structure:
                    company_elements = job_element.find_elements(By.CSS_SELECTOR, company_name_selector)
                    for ce in company_elements: # Iterate because h3 might be used for other things
                        if ce.text.strip(): # Take the first non-empty one
                            # Check if it's not the date like "Publicado hace X dias"
                            if not ce.text.strip().startswith("Publicado") and not ce.text.strip().startswith("Actualizado"):
                                company = ce.text.strip()
                                break
                    if company == "Not found" and company_elements: # Fallback if text was empty or only date
                         company = company_elements[0].text.strip() if company_elements[0].text.strip() else "Company text empty"


                except Exception:
                    pass # Keep "Not found"

                try:
                    location_element = job_element.find_element(By.CSS_SELECTOR, job_location_selector)
                    location = location_element.text.strip()
                except Exception:
                    pass

                try:
                    link_element = job_element.find_element(By.CSS_SELECTOR, job_link_selector)
                    link = link_element.get_attribute('href')
                except Exception:
                    pass

                print(f"  Title: {title}")
                print(f"  Company: {company}")
                print(f"  Location: {location}")
                print(f"  Link: {link}")

            print("\n--- End of Data Extraction ---")

    except Exception as e:
        print(f"An error occurred: {e}")
        try:
            driver.save_screenshot("error_page.png")
            with open("error_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Saved error page source and screenshot.")
        except:
            print("Could not save error page source/screenshot.")

    finally:
        print("\nClosing browser.")
        driver.quit()

if __name__ == "__main__":
    inspect_job_site()
