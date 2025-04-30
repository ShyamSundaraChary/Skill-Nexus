import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

# Configuration
API_KEY = os.getenv('SCRAPERAPI_KEY', '266192e70f4646dc04e86c63da463dd1')  # Use environment variables
SEARCH_QUERY = "python+developer"
LOCATION = "hyderabad"
JOB_COUNT = 10  # Increased to 10 jobs

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    return uc.Chrome(options=options, use_subprocess=True)

def scrape_indeed():
    driver = get_driver()
    try:
        target_url = f"https://www.indeed.com/jobs?q={SEARCH_QUERY}&l={LOCATION}"
        scraper_url = f"https://api.scraperapi.com/?api_key={API_KEY}&url={target_url}&render=true"
        
        driver.get(scraper_url)
        
        # Wait for job cards to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "job_seen_beacon"))
        )
        
        # Scroll to load more jobs
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        job_cards = driver.find_elements(By.CLASS_NAME, "job_seen_beacon")[:JOB_COUNT]
        
        for i, card in enumerate(job_cards, 1):
            try:
                title = card.find_element(By.CSS_SELECTOR, "h2.jobTitle").text.strip()
                company = card.find_element(By.CSS_SELECTOR, "[data-testid='company-name']").text.strip()
                location = card.find_element(By.CSS_SELECTOR, "[data-testid='text-location']").text.strip()
                summary = card.find_element(By.CSS_SELECTOR, ".job-snippet").text.strip().replace('\n', ' ')
                
                print(f"\nJob {i}:")
                print(f"Title    : {title}")
                print(f"Company  : {company}")
                print(f"Location : {location}")
                print(f"Summary  : {summary}")
                
            except Exception as e:
                print(f"Error parsing job {i}: {str(e)}")
                
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_indeed()
