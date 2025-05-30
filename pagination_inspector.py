import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

try:
    from selenium_stealth import stealth
except ImportError:
    print("selenium-stealth not found. Consider installing with: pip install selenium-stealth")
    stealth = None

def inspect_pagination():
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

    url = "https://www.bumeran.com.ar/en-buenos-aires/capital-federal/empleos-busqueda-desarrollador.html?page=1"
    print(f"Navigating to {url}")

    try:
        driver.get(url)
        print("Waiting for page to load (10 seconds)...")
        time.sleep(10)

        page_title = driver.title
        print(f"\nPage title: {page_title}")

        if "Cloudflare" in page_title or "Attention Required" in page_title:
            print("\n[WARNING] Cloudflare challenge likely detected. Pagination inspection may fail.")
            # ... (saving logic as before)
            return

        print("\n--- Inspecting Pagination ---")

        # Selector for the "Next page" link/button element itself (whether enabled or disabled)
        next_page_element_selector = "a.sc-dzVpKk.hFOZsP"
        # Selector for an *active* (not disabled) "Next page" link
        active_next_page_selector = "a.sc-dzVpKk.hFOZsP:not([disabled])"

        print(f"Checking for general 'Next page' element using: {next_page_element_selector}")

        next_page_button_is_disabled = False
        next_page_link_href = None

        try:
            # Check for the presence of the next page button, even if disabled
            next_button_element = driver.find_element(By.CSS_SELECTOR, next_page_element_selector)
            print("Found 'Next page' element (could be enabled or disabled).")

            if next_button_element.get_attribute("disabled") is not None:
                next_page_button_is_disabled = True
                print("  'Next page' element HAS 'disabled' attribute.")
            else:
                print("  'Next page' element does NOT have 'disabled' attribute.")
                # If not explicitly disabled, try to get its href
                try:
                    active_next_button = driver.find_element(By.CSS_SELECTOR, active_next_page_selector)
                    next_page_link_href = active_next_button.get_attribute('href')
                    print(f"  Active 'Next page' link found. Href: {next_page_link_href}")
                except NoSuchElementException:
                    print(f"  Active 'Next page' button not found with: {active_next_page_selector} (might be present but disabled, or truly the last page).")

        except NoSuchElementException:
            print(f"'Next page' element NOT FOUND using selector: {next_page_element_selector}. This implies it's the last page or only page.")
            # This case means there's no next page arrow at all.
            next_page_button_is_disabled = True # Treat as effectively disabled for pagination logic

        print("\n--- Pagination Findings ---")
        print(f"Selector for the 'Next page' button element (enabled or disabled): {next_page_element_selector}")
        print(f"Selector for an *active* 'Next page' button: {active_next_page_selector}")

        if next_page_button_is_disabled:
            print("Conclusion: Currently on the last page or there is only one page of results.")
            print("  Reason: The 'Next page' button element either has a 'disabled' attribute or was not found by the active selector.")
        elif next_page_link_href:
            print(f"Conclusion: There is a next page. The link is: {next_page_link_href}")
        else:
            print("Conclusion: 'Next page' button was found but seems inactive for an undetermined reason (not explicitly disabled by attribute, but active selector failed). This might be the last page.")

        print("\n--- How to Detect Last Page (for scraper logic) ---")
        print(f"1. Attempt to find the 'Next page' button using the active selector: '{active_next_page_selector}'.")
        print("2. If the element is NOT found (raises NoSuchElementException), it means there are no more pages to navigate to.")
        print("3. The `disabled` attribute on the general selector `a.sc-dzVpKk.hFOZsP` also indicates the last page.")

        # Verify page numbers as before
        try:
            page_numbers_container = driver.find_element(By.CSS_SELECTOR, "div.sc-gIjDWZ.cNSNtX")
            page_links = page_numbers_container.find_elements(By.TAG_NAME, "a")
            current_page_span = page_numbers_container.find_element(By.CSS_SELECTOR, "a.sc-fQfKYo.fvTgHT > span")
            print(f"\nPage numbers info: Found {len(page_links)} page links. Current active page is: {current_page_span.text}")
            if len(page_links) == 1 and current_page_span.text == "1":
                print("  This confirms there is only one page of results.")
        except Exception as e:
            print(f"Could not find page numbers or current page: {e}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # ... (saving logic as before)

    finally:
        print("\nClosing browser.")
        driver.quit()

if __name__ == "__main__":
    inspect_pagination()
