from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import mysql.connector
from datetime import datetime, timedelta
import time
import random
import re
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
from settings import USER_AGENTS
import logging
from typing import List, Dict, Any
from threading import Lock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('naukri_scraper.log'),
        logging.StreamHandler()
    ]
)

# Define job roles to scrape
JOB_ROLES = [
    "python-developer",
    "java-developer"
]

# Thread-safe counter for user agent rotation
user_agent_counter = 0
user_agent_lock = Lock()

def get_next_user_agent():
    global user_agent_counter
    with user_agent_lock:
        user_agent = USER_AGENTS[user_agent_counter % len(USER_AGENTS)]
        user_agent_counter += 1
        return user_agent

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={get_next_user_agent()}")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(options=chrome_options, service=Service(ChromeDriverManager().install()))

def connect_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="shyam",
            password="shyam",
            database="jobs_fresher",
            pool_size=5
        )
    except mysql.connector.Error as e:
        logging.error(f"Database connection failed: {e}")
        raise

def create_table(conn, job_title: str) -> None:
    cursor = conn.cursor()
    table_name = re.sub(r'[^a-zA-Z0-9_]', '_', job_title.replace("-", "_").lower())
    query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_title VARCHAR(100) NOT NULL,
            company VARCHAR(100) NOT NULL,
            location VARCHAR(100),
            salary VARCHAR(100),
            skills_required TEXT NOT NULL,
            job_link VARCHAR(500),
            posted_date DATE,
            applicants INT,
            source VARCHAR(20) DEFAULT 'Naukri',
            experience_level VARCHAR(50),
            UNIQUE (job_title, company, source)
        )
    """     
    try:
        cursor.execute(query)
        conn.commit()
        logging.info(f"Created/Verified table for {job_title}")
    except mysql.connector.Error as e:
        logging.error(f"Failed to create table for {job_title}: {e}")
    finally:
        cursor.close()

def insert_jobs(conn, job_title: str, jobs_data: List[Dict[str, Any]]) -> None:
    if not jobs_data:
        logging.warning(f"No jobs to insert for {job_title}")
        return
    cursor = conn.cursor()
    table_name = re.sub(r'[^a-zA-Z0-9_]', '_', job_title.replace("-", "_").lower())
    query = f"""
        INSERT IGNORE INTO {table_name} 
        (job_title, company, location, salary, skills_required, job_link, posted_date, applicants, source, experience_level)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        logging.info(f"Attempting to insert {len(jobs_data)} jobs for {job_title}")
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
                "Naukri",
                job["experience_level"]
            ) for job in jobs_data
        ])
        conn.commit()
        logging.info(f"Successfully inserted {cursor.rowcount} jobs for {job_title}")
    except mysql.connector.Error as e:
        logging.error(f"Failed to insert jobs for {job_title}: {e}")
    finally:
        cursor.close()

def parse_posted_date(posted_text: str) -> datetime.date:
    try:
        posted_text = posted_text.lower()
        today = datetime.now().date()
        if "today" in posted_text:
            return today
        elif "yesterday" in posted_text:
            return today - timedelta(days=1)
        elif "day" in posted_text:
            days = int(re.search(r'\d+', posted_text).group())
            return today - timedelta(days=days)
        elif "hour" in posted_text or "minute" in posted_text or "just now" in posted_text:
            return today
        elif "week" in posted_text:
            weeks = int(re.search(r'\d+', posted_text).group())
            return today - timedelta(days=weeks * 7)
        return today
    except Exception as e:
        logging.error(f"Error parsing date: {e}")
        return datetime.now().date()

def scrape_applicants(job_url: str, driver: webdriver.Chrome) -> int:
    applicants = 0
    try:
        driver.get(job_url)
        time.sleep(random.uniform(2, 3))
        soup = BeautifulSoup(driver.page_source, "lxml")
        applicants_span = soup.find("label", string=lambda text: text and "Applicants:" in text)
        if applicants_span:
            applicants_elem = applicants_span.find_next("span")
            if applicants_elem:
                applicants_text = applicants_elem.text.strip()
                applicants = int(re.search(r'\d+', applicants_text).group()) if re.search(r'\d+', applicants_text) else 0
        return applicants
    except Exception as e:
        logging.error(f"Failed to scrape applicants for {job_url}: {e}")
        return 0

def scrape_job_page(job_title: str, page: int, max_jobs: int, driver: webdriver.Chrome) -> List[Dict[str, Any]]:
    jobs = []
    try:
 # Modified URL to fetch fresher jobs (0-3 years experience) and recent postings (last 7 days)
        base_url = f"https://www.naukri.com/{job_title}-jobs?experience=0&jobAge=7&pageNo={page}"
        driver.get(base_url)
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "srp-jobtuple-wrapper"))
            )
        except Exception as e:
            logging.error(f"Failed to load search results for {job_title} page {page}: {e}")
            return jobs

        soup = BeautifulSoup(driver.page_source, "lxml")
        job_elements = soup.find_all("div", class_="srp-jobtuple-wrapper")
        
        if not job_elements:
            return jobs

        for job in job_elements:
            try:
                title_tag = job.find("a", class_="title")
                if not title_tag:
                    continue

                title = title_tag.text.strip()
                job_link = title_tag["href"]
                company = job.find("a", class_="comp-name").text.strip()
                skills_tags = job.find_all("li", class_="tag-li")
                skills = [skill.text.strip().lower() for skill in skills_tags]
                skills = list(dict.fromkeys(skills))
                skills_str = ", ".join(skills) if skills else "Not Available"
                location = job.find("span", class_="locWdth").text.strip()
                salary = job.find("span", class_="sal").text.strip() if job.find("span", class_="sal") else "Not Disclosed"
                experience = job.find("span", class_="exp").text.strip() if job.find("span", class_="exp") else "Not Available"
                posted_date = parse_posted_date(job.find("span", class_="job-post-day").text.strip())
                
                applicants = scrape_applicants(job_link, driver)
                
                job_data = {
                    "job_title": title,
                    "company": company,
                    "location": location,
                    "salary": salary,
                    "skills_required": skills_str,
                    "job_link": job_link,
                    "posted_date": posted_date,
                    "applicants": applicants,
                    "experience_level": experience
                }
                
                logging.info(f"Scraped job: {title} at {company}")
                jobs.append(job_data)
                
                if len(jobs) >= max_jobs:
                    break
                    
            except Exception as e:
                logging.error(f"Error processing job: {e}")
                continue

        time.sleep(random.uniform(3, 5))
        return jobs

    except Exception as e:
        logging.error(f"Error scraping page {page} for {job_title}: {e}")
        return jobs

def scrape_naukri_jobs(job_titles: List[str], max_jobs: int) -> Dict[str, List[Dict[str, Any]]]:
    conn = connect_db()
    
    # Create tables for all job titles
    for job_title in job_titles:
        create_table(conn, job_title)

    jobs_by_title = {}
    total_jobs_scraped = 0
    start_time = time.time()

    try:
        # Create a thread pool with 3 workers
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            for job_title in job_titles:
                jobs_by_title[job_title] = []
                # Submit tasks for each page
                for page in range(1, 4):  # 3 pages per job title
                    futures.append(executor.submit(scrape_job_page, job_title, page, max_jobs, create_driver()))
            
            # Process completed tasks
            for future in as_completed(futures):
                try:
                    jobs = future.result()
                    if jobs:
                        # Find which job title these jobs belong to
                        for job in jobs:
                            for job_title in job_titles:
                                if job["job_title"].lower().find(job_title.replace("-", " ")) != -1:
                                    jobs_by_title[job_title].append(job)
                                    total_jobs_scraped += 1
                                    break
                except Exception as e:
                    logging.error(f"Error in thread: {e}")

        # Insert jobs into respective tables
        for job_title, jobs in jobs_by_title.items():
            if jobs:
                insert_jobs(conn, job_title, jobs)

    except Exception as e:
        logging.error(f"Failed to scrape jobs: {e}")
    finally:
        conn.close()

    end_time = time.time()
    execution_time = end_time - start_time
    logging.info(f"\nTotal jobs scraped: {total_jobs_scraped}")
    logging.info(f"Total execution time: {execution_time:.2f} seconds")
    logging.info(f"Average time per job: {execution_time/total_jobs_scraped:.2f} seconds")
    
    return jobs_by_title

if __name__ == "__main__":
    start_time = time.time()
    
    # Scrape jobs for all defined roles
    results = scrape_naukri_jobs(JOB_ROLES, max_jobs=15)  # Get 15 jobs per role
    
    # Print summary
    for title, jobs in results.items():
        logging.info(f"\nResults for {title}:")
        logging.info(f"Total jobs found: {len(jobs)}")
    
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info(f"\nTotal execution time: {execution_time:.2f} seconds")