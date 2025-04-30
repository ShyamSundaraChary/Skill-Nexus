from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time, random, re, logging
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor
from settings import USER_AGENTS, SKILLS_LIST
from sentence_transformers import SentenceTransformer
import json
from database import connect_db, create_table, insert_jobs
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('linkedin_scraper.log'), logging.StreamHandler()]
)

# Load the embedding model once at module level
model = SentenceTransformer('all-MiniLM-L6-v2')

# ScraperAPI Configuration
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
if not SCRAPERAPI_KEY:
    raise ValueError("ScraperAPI key not found. Please set the SCRAPERAPI_KEY environment variable.")
SCRAPERAPI_PROXY = f'http://api.scraperapi.com:8010?api_key={SCRAPERAPI_KEY}&url='

# Define job roles to scrape
JOB_ROLES = ["full_stack_developer", "java_developer", "python_developer","Frontend Developer", 
             "Backend Developer","Data Scientist", "DevOps Engineer","software_engineer"]

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

# Create Chrome Driver with ScraperAPI Proxy
def create_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    chrome_options.add_argument("--disable-webgl")
    proxy = Proxy()
    proxy.proxy_type = ProxyType.MANUAL
    proxy.http_proxy = SCRAPERAPI_PROXY
    proxy.ssl_proxy = SCRAPERAPI_PROXY
    chrome_options.proxy = proxy
    return webdriver.Chrome(options=chrome_options, service=Service(ChromeDriverManager().install()))

# Parse Posted Date
def parse_posted_date(posted_text):
    try:
        posted_text = posted_text.lower()
        today = datetime.now().date()
        if "hour" in posted_text or "minute" in posted_text or "just now" in posted_text:
            return today
        elif "day" in posted_text:
            days = int(re.search(r'\d+', posted_text).group())
            return today - timedelta(days=days)
        elif "week" in posted_text:
            weeks = int(re.search(r'\d+', posted_text).group())
            return today - timedelta(days=weeks * 7)
        elif "month" in posted_text:
            months = int(re.search(r'\d+', posted_text).group())
            return today - timedelta(days=months * 30)
        return today
    except Exception as e:
        logging.error(f"Error parsing date: {e}")
        return datetime.now().date()

# Scrape Individual Job Page
def scrape_job_page(job_url, role):
    driver = create_chrome_driver()
    driver.implicitly_wait(7)
    try:
        driver.get(job_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.top-card-layout__title, h1"))
        )
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(0.5, 1.5))
        soup = BeautifulSoup(driver.page_source, "lxml")
        title = soup.find("h1", class_="top-card-layout__title") or soup.find("h1")
        job_title = title.text.strip() if title else "Not Available"
        company_tag = (
            soup.find("a", class_="topcard__org-name-link") or
            soup.find("span", class_="topcard__flavor") or
            soup.find("span", class_="jobs-top-card__company-title")
        )
        company = company_tag.text.strip() if company_tag else "Not Available"
        location_tag = soup.find("span", class_="topcard__flavor--bullet") or soup.find("span", class_="jobs-unified-top-card__bullet")
        location = location_tag.text.strip() if location_tag else "Not Available"
        metadata = soup.find("span", class_="posted-time-ago__text") or soup.find("span", class_="jobs-unified-top-card__posted-date")
        posted_time = metadata.text.strip() if metadata else "Not Available"
        posted_date = parse_posted_date(posted_time)
        applicants = 0
        applicants_tag = soup.find("span", class_="num-applicants__caption") or soup.find("span", class_="jobs-unified-top-card__applicant-count")
        if applicants_tag:
            match = re.search(r'\d+', applicants_tag.text.strip())
            if match:
                applicants = int(match.group())
        else:
            applicants_text = soup.find(string=re.compile(r'\d+\s*(applicants|applied)', re.I))
            if applicants_text:
                match = re.search(r'\d+', applicants_text)
                if match:
                    applicants = int(match.group())
        salary = "Not disclosed"
        salary_tag = soup.find("span", class_="topcard__flavor--salary") or soup.find("span", class_="jobs-unified-top-card__salary")
        if salary_tag:
            salary = salary_tag.text.strip()
        description = soup.find("div", class_="show-more-less-html__markup") or soup.find("div", class_="jobs-description__content")
        job_description = description.text.strip() if description else "Not Available"
        # Compute embedding
        if job_description != "Not Available":
            embedding = model.encode(job_description).tolist()
            embedding_json = json.dumps(embedding)
        else:
            embedding_json = None
        matched_skills = []
        for skill in SKILLS_LIST:
            if job_description != "Not Available" and re.search(rf'\b{re.escape(skill)}\b', job_description, re.IGNORECASE):
                matched_skills.append(skill)
        skills_required = ", ".join(matched_skills) if matched_skills else "Not Available"
        experience_tag = soup.find("span", class_="description__job-criteria-text") or soup.find("span", class_="jobs-unified-top-card__experience-level")
        experience_level = experience_tag.text.strip() if experience_tag else "Not Available"
        job_type = "Not Available"
        employment_containers = (
            soup.find_all("li", class_="description__job-criteria-item") or
            soup.find_all("li", class_="jobs-unified-top-card__job-insight")
        )
        for container in employment_containers:
            header = container.find("h3", class_="description__job-criteria-subheader") or container.find("span")
            if header and "employment type" in header.text.lower():
                value = container.find("span", class_="description__job-criteria-text") or container.find("span")
                if value:
                    job_type = value.text.strip()
                    break
        job_data = {
            "job_title": job_title,
            "company": company,
            "location": location,
            "salary": salary,
            "skills_required": skills_required,
            "job_link": job_url,
            "posted_date": posted_date,
            "applicants": applicants,
            "source": "LinkedIn",
            "experience_level": experience_level,
            "role": role,
            "job_description": job_description,
            "job_type": job_type,
            "embedding": embedding_json
        }
        return job_data
    except Exception as e:
        logging.error(f"Failed to scrape {job_url}: {e}")
        return None
    finally:
        driver.quit()

# Scrape Job Listings and Insert into Jobs Table
def scrape_linkedin_jobs(job_titles, jobs_per_title):
    driver = create_chrome_driver()
    driver.implicitly_wait(5)
    conn = connect_db(DB_CONFIG)
    if not conn:
        raise Exception("Database connection not valid")
    try:
        create_table(conn)
        jobs_data = []
        total_jobs_scraped = 0
        seen_urls = set()
        for job_title in job_titles:
            logging.info(f"Scraping jobs for: {job_title}")
            jobs_collected = 0
            page = 1
            while jobs_collected < jobs_per_title and page <= 5:
                search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title.replace('_', '%20')}&location=India&f_TPR=r86400&start={(page-1)*25}"
                # search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title.replace('_', '%20')}&location=India&f_TPR=r2592000&start={(page-1)*25}"
                driver.get(search_url)
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__results-list"))
                    )
                except Exception as e:
                    logging.error(f"Failed to load search results for {job_title} page {page}: {e}")
                    page += 1
                    time.sleep(random.uniform(3, 5))
                    continue

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(0.5, 1.5))
                soup = BeautifulSoup(driver.page_source, "lxml")
                job_cards = soup.find_all("div", class_="base-card")
                job_urls = []
                for card in job_cards:
                    link = card.find("a", class_="base-card__full-link")
                    if link and link.get("href") and link["href"] not in seen_urls:
                        job_urls.append(link["href"])
                        seen_urls.add(link["href"])
                    if len(job_urls) + jobs_collected >= jobs_per_title:
                        break
                logging.info(f"Found {len(job_urls)} valid job URLs for {job_title} on page {page}")
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_url = {executor.submit(scrape_job_page, url, job_title): url for url in job_urls}
                    for future in future_to_url:
                        job_data = future.result()
                        if job_data:
                            jobs_data.append(job_data)
                            jobs_collected += 1
                            total_jobs_scraped += 1
                            logging.info(f"Scraped job: {job_data['job_title']} at {job_data['company']}")
                        else:
                            logging.warning(f"Skipping invalid job data for URL: {future_to_url[future]}")
                page += 1
                time.sleep(random.uniform(2, 4))
        if jobs_data:
            insert_jobs(conn, jobs_data)
        else:
            logging.info("No valid jobs found")
    except Exception as e:
        logging.error(f"Error during scraping: {e}")
    finally:
        driver.quit()
        if conn.is_connected():
            conn.close()
            logging.info("Database connection closed")
    return jobs_data

# Main Execution
if __name__ == "__main__":
    start_time = time.time()
    try:
        scrape_linkedin_jobs(JOB_ROLES, jobs_per_title=50)
    finally:
        logging.info("Scraping completed")
    end_time = time.time()
    logging.info(f"Total execution time: {end_time - start_time:.2f} seconds")