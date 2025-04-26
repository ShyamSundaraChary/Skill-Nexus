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
import mysql.connector
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor
from settings import USER_AGENTS, SKILLS_LIST

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('linkedin_scraper.log'), logging.StreamHandler()]
)

# ScraperAPI Configuration
SCRAPERAPI_KEY = '266192e70f4646dc04e86c63da463dd1'  # Replace with your ScraperAPI API key
SCRAPERAPI_PROXY = f'http://api.scraperapi.com:8010?api_key={SCRAPERAPI_KEY}&url='

# Define job roles to scrape
JOB_ROLES = [
    "full_stack_developer",
    "java_developer",
    "python_developer"
]

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "shyam",
    "password": "shyam",
    "database": "jobs_db"
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

    # Configure ScraperAPI proxy
    proxy = Proxy()
    proxy.proxy_type = ProxyType.MANUAL
    proxy.http_proxy = SCRAPERAPI_PROXY
    proxy.ssl_proxy = SCRAPERAPI_PROXY

    # Add proxy to Chrome options
    chrome_options.proxy = proxy

    return webdriver.Chrome(options=chrome_options, service=Service(ChromeDriverManager().install()))

# Rest of your script remains unchanged (get_db_connection, create_table, insert_jobs, etc.)
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            logging.info("Database connection established")
            return conn
        logging.error("Failed to establish database connection")
    except mysql.connector.Error as e:
        logging.error(f"Database connection failed: {e}")
    return None

db_connection = get_db_connection()
if not db_connection:
    raise Exception("Database connection not valid")

# Create Unified Jobs Table
def create_table(conn):
    with conn.cursor() as cursor:
        query = """
            CREATE TABLE IF NOT EXISTS jobs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                job_title VARCHAR(100) NOT NULL,
                company VARCHAR(100) NOT NULL,
                location VARCHAR(100),
                salary VARCHAR(100),
                skills_required TEXT NOT NULL,
                job_link VARCHAR(500),
                posted_date DATE,
                applicants INT,
                source VARCHAR(20) DEFAULT 'LinkedIn',
                experience_level VARCHAR(50),
                role VARCHAR(50),
                job_description TEXT,
                job_type VARCHAR(50),
                UNIQUE (job_title, company, source),
                INDEX idx_role_date_exp (role, posted_date, experience_level),
                INDEX idx_location (location)
            )
        """
        try:
            cursor.execute(query)
            conn.commit()
            logging.info("Created/Verified jobs table")
        except mysql.connector.Error as e:
            logging.error(f"Failed to create jobs table: {e}")

# Insert Jobs into Jobs Table
def insert_jobs(conn, jobs_data):
    if not jobs_data:
        logging.warning("No jobs to insert")
        return
    with conn.cursor() as cursor:
        query = """
            INSERT IGNORE INTO jobs 
            (job_title, company, location, salary, skills_required, job_link, posted_date, applicants, source, experience_level, role, job_description, job_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            logging.info(f"Attempting to insert {len(jobs_data)} valid jobs")
            cursor.executemany(query, [
                (
                    job["job_title"][:100],
                    job["company"][:100],
                    job["location"][:100],
                    job["salary"],
                    job["skills_required"],
                    job["job_link"],
                    job["posted_date"],
                    job["applicants"],
                    "LinkedIn",
                    job["experience_level"],
                    job["role"],
                    job["job_description"],
                    job["job_type"]
                ) for job in jobs_data
            ])
            conn.commit()
            logging.info(f"Inserted {cursor.rowcount} jobs")
        except mysql.connector.Error as e:
            logging.error(f"Failed to insert jobs: {e}")

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
        return today
    except:
        return datetime.now().date()

# Scrape Individual Job Page
def scrape_job_page(job_url, role):
    driver = create_chrome_driver()
    driver.implicitly_wait(5)

    try:
        driver.get(job_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.top-card-layout__title, h1"))
        )
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(0.5, 1.5))

        soup = BeautifulSoup(driver.page_source, "lxml")

        # Extract Title
        title = soup.find("h1", class_="top-card-layout__title") or soup.find("h1")
        job_title = title.text.strip() if title else "Not Available"

        # Extract Company
        company_tag = (
            soup.find("a", class_="topcard__org-name-link") or
            soup.find("span", class_="topcard__flavor") or
            soup.find("span", class_="jobs-top-card__company-title")
        )
        company = company_tag.text.strip() if company_tag else "Not Available"

        # Extract Location
        location_tag = soup.find("span", class_="topcard__flavor--bullet") or soup.find("span", class_="jobs-unified-top-card__bullet")
        location = location_tag.text.strip() if location_tag else "Not Available"

        # Extract Posted Time
        metadata = soup.find("span", class_="posted-time-ago__text") or soup.find("span", class_="jobs-unified-top-card__posted-date")
        posted_time = metadata.text.strip() if metadata else "Not Available"
        posted_date = parse_posted_date(posted_time)

        # Extract Applicants
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

        # Extract Salary
        salary = "Not disclosed"
        salary_tag = soup.find("span", class_="topcard__flavor--salary") or soup.find("span", class_="jobs-unified-top-card__salary")
        if salary_tag:
            salary = salary_tag.text.strip()

        # Extract Job Description
        description = soup.find("div", class_="show-more-less-html__markup") or soup.find("div", class_="jobs-description__content")
        job_description = description.text.strip() if description else "Not Available"

        # Extract Skills
        matched_skills = []
        for skill in SKILLS_LIST:
            if re.search(rf'\b{re.escape(skill)}\b', job_description, re.IGNORECASE):
                matched_skills.append(skill)
        skills_required = ", ".join(matched_skills) if matched_skills else "Not Available"

        # Extract Experience Level
        experience_tag = soup.find("span", class_="description__job-criteria-text") or soup.find("span", class_="jobs-unified-top-card__experience-level")
        experience_level = experience_tag.text.strip() if experience_tag else "Not Available"

        # Extract Job Type
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
            "posted_date": posted_date.strftime("%Y-%m-%d"),
            "applicants": applicants,
            "source": "LinkedIn",
            "experience_level": experience_level,
            "role": role,
            "job_description": job_description,
            "job_type": job_type
        }

        return job_data
    except Exception as e:
        logging.error(f"Failed to scrape {job_url}: {e}")
        return None
    finally:
        driver.quit()

# Scrape Job Listings and Insert into Jobs Table
def scrape_linkedin_jobs(job_titles, jobs_per_title):
    # Set up Selenium WebDriver
    driver = create_chrome_driver()
    driver.implicitly_wait(5)

    # Create jobs table
    conn = get_db_connection()
    if conn:
        create_table(conn)

    jobs_data = []
    total_jobs_scraped = 0
    seen_urls = set()

    try:
        for job_title in job_titles:
            logging.info(f"Scraping jobs for: {job_title}")
            jobs_collected = 0
            page = 1
            while jobs_collected < jobs_per_title and page <= 3:
                # Construct search URL no experience level filter
                search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title.replace('_', '%20')}&location=India&start={(page-1)*25}"
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

                logging.info(f"Found {len(job_urls)} job URLs for {job_title} on page {page}")

                # Parallel scraping of job URLs
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_url = {executor.submit(scrape_job_page, url, job_title): url for url in job_urls}
                    for future in future_to_url:
                        job_data = future.result()
                        if job_data:
                            jobs_data.append(job_data)
                            jobs_collected += 1
                            total_jobs_scraped += 1
                            logging.info(f"Scraped job: {job_data['job_title']} at {job_data['company']}")

                page += 1
                time.sleep(random.uniform(2, 4))

        # Insert scraped jobs into the database
        if jobs_data:
            conn = get_db_connection()
            if conn:
                insert_jobs(conn, jobs_data)
        else:
            logging.info(f"No valid jobs found for {job_title}")

    except Exception as e:
        logging.error(f"error during scraping: {e}")
    finally:
        driver.quit()

    return jobs_data

# Main Execution
if __name__ == "__main__":
    start_time = time.time()
    try:
        scrape_linkedin_jobs(JOB_ROLES, jobs_per_title=50)
    finally:
        if db_connection.is_connected():
            db_connection.close()
            logging.info("Database connection closed")
    end_time = time.time()
    logging.info(f"Total execution time: {end_time - start_time:.2f} seconds")