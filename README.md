# Computrabajo Job Scraper

This Python script uses Selenium to scrape job listings from a specific Computrabajo URL (focused on "desarrollador" roles in "Capital Federal, Argentina"). It extracts information like job title, company, location, and a direct link to the job posting, then saves this data into a `job_listings.csv` file.

## Features

- Scrapes multiple pages of job listings.
- Extracts: Job Title, Company Name, Location, Link to Job Posting.
- Saves data to `job_listings.csv`.
- Uses Selenium with ChromeDriver.

## Prerequisites

1.  **Python 3.x**: Ensure you have Python 3 installed. You can download it from [python.org](https://www.python.org/).
2.  **Google Chrome**: The script is configured to use Google Chrome. Make sure you have it installed.
3.  **ChromeDriver**: You need to download the ChromeDriver executable that matches your Google Chrome version.
    *   Check your Chrome version: Go to `chrome://settings/help`.
    *   Download ChromeDriver from the official site: [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads).
    *   **Important**: Place the `chromedriver` executable in a directory that is part of your system's PATH environment variable (e.g., `/usr/local/bin` on Linux/macOS, or a specific folder you add to PATH on Windows). Alternatively, you can modify the `scraper.py` script to specify the path to `chromedriver.exe` directly when `webdriver.Chrome()` is initialized (e.g., `driver = webdriver.Chrome(executable_path='/path/to/your/chromedriver')`).

## Setup

1.  **Clone the repository (if applicable) or download the files.**

2.  **Create a virtual environment (recommended)**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    Navigate to the project directory in your terminal and run:
    ```bash
    pip install -r requirements.txt
    ```
    This will install `selenium`.

## Usage

1.  **Ensure ChromeDriver is set up correctly** (see Prerequisites).

2.  **Run the scraper**:
    Execute the script from the project's root directory:
    ```bash
    python scraper.py
    ```

3.  **Output**:
    *   The script will print progress messages to the console, including the number of pages scraped and total jobs found.
    *   Once finished, a `job_listings.csv` file will be created in the same directory, containing the scraped job data.

## Troubleshooting

*   **`WebDriverException: 'chromedriver' executable needs to be in PATH`**: This means ChromeDriver is not correctly installed in your PATH or the script cannot find it. Double-check the ChromeDriver setup instructions.
*   **Scraper stops or encounters errors**: Websites change their structure frequently. If the scraper fails, the HTML selectors in `scraper.py` might need to be updated. You can inspect the website manually using browser developer tools to find the new selectors.
*   **Cookie pop-ups or other modals**: The script includes a basic attempt to handle cookie pop-ups. If new modals interfere, their specific selectors might need to be added to the script for handling.
