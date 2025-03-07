from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Function to scrape jobs from Naukri.com
def scrape_naukri_jobs(job_title, num_pages=1):
    # Format the job title for the URL
    job_title_formatted = job_title.lower().replace(" ", "-")
    base_url = f"https://www.naukri.com/{job_title_formatted}-jobs"
    
    # Set up Selenium WebDriver (Chrome)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    try:
        for page in range(1, num_pages + 1):
            # Construct URL for each page
            url = base_url if page == 1 else f"{base_url}-{page}"
            print(f"Scraping page: {page} - URL: {url}")
            
            # Load the page
            driver.get(url)
            time.sleep(5)  # Wait for dynamic content to load
            
            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Find job listings (update class names as needed)
            job_listings = soup.find_all("div", class_="cust-job-tuple")  # Updated class based on recent structure
            
            if not job_listings:
                print("No jobs found on this page or structure has changed.")
                print("Check the HTML structure or try a different approach.")
                break
            
            # Extract and print job details
            for job in job_listings:
                title = job.find("a", class_="title").text.strip() if job.find("a", class_="title") else "N/A"
                company = job.find("a", class_="comp-name").text.strip() if job.find("a", class_="comp-name") else "N/A"
                location = job.find("span", class_="locWdth").text.strip() if job.find("span", class_="locWdth") else "N/A"
                experience = job.find("span", class_="expwdth").text.strip() if job.find("span", class_="expwdth") else "N/A"
                
                print("\nJob Title:", title)
                print("Company:", company)
                print("Location:", location)
                print("Experience:", experience)
                print("-" * 50)
            
            # Delay between pages
            time.sleep(2)
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        driver.quit()  # Close the browser

# Example usage
if __name__ == "__main__":
    job_title = "DevOps"  # Replace with your desired job title
    scrape_naukri_jobs(job_title, num_pages=2)  # Scrape 2 pages