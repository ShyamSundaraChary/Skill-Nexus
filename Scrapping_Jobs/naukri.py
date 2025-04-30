from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time, random, re
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
from settings import USER_AGENTS
import logging
from typing import List, Dict, Any
from threading import Lock
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
import os
from sentence_transformers import SentenceTransformer
import json
from database import connect_db, create_table, insert_jobs

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('naukri_scraper.log'), logging.StreamHandler()]
)

# Load the embedding model once at module level
model = SentenceTransformer('all-MiniLM-L6-v2')

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

def parse_posted_date(posted_text: str) -> datetime.date:
    try:
        posted_text = posted_text.lower()
        today = datetime.now().date()
        if "hour" in posted_text or "minute" in posted_text or "just now" in posted_text:
            return today
        elif "today" in posted_text:
            return today
        elif "yesterday" in posted_text:
            return today - timedelta(days=1)
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

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def scrape_job_page(job_title: str, page: int, max_jobs: int) -> List[Dict[str, Any]]:
    jobs = []
    driver = create_driver()
    try:
        base_url = f"https://www.naukri.com/{job_title}-jobs?jobAge=7&pageNo={page}"
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
                company = job.find("a", class_="comp-name").text.strip() if job.find("a", class_="comp-name") else "Unknown"
                skills_tags = job.find_all("li", class_="tag-li")
                skills = [skill.text.strip().lower() for skill in skills_tags]
                skills = list(dict.fromkeys(skills))
                skills_str = ", ".join(skills) if skills else "Not Available"
                location = job.find("span", class_="locWdth").text.strip() if job.find("span", class_="locWdth") else "Not Available"
                salary = job.find("span", class_="sal").text.strip() if job.find("span", class_="sal") else "Not Disclosed"
                experience = job.find("span", class_="exp").text.strip() if job.find("span", class_="exp") else "Not Available"
                posted_date = parse_posted_date(job.find("span", class_="job-post-day").text.strip())
                driver.get(job_link)
                time.sleep(random.uniform(2, 3))
                job_soup = BeautifulSoup(driver.page_source, "lxml")
                description_section = job_soup.find("section", class_="styles_job-desc-container__txpYf")
                job_description = description_section.text.strip() if description_section else "Not Available"
                if job_description == "Not Available":
                    logging.warning(f"No job description found for {title} at {company}")
                if job_description != "Not Available":
                    embedding = model.encode(job_description).tolist()
                    embedding_json = json.dumps(embedding)
                else:
                    embedding_json = None
                job_type = "Not Available"
                if job_description != "Not Available":
                    employment_match = re.search(r"Employment Type:\s*([^,\n;]+)", job_description, re.IGNORECASE)
                    if employment_match:
                        job_type = employment_match.group(1).strip()
                    else:
                        type_match = re.search(r"(Full Time|Part Time|Contract|Permanent|Internship)", job_description, re.IGNORECASE)
                        if type_match:
                            job_type = type_match.group(1).strip()
                if job_type == "Not Available":
                    logging.warning(f"No job type found for {title} at {company}")
                applicants = 0
                applicants_span = job_soup.find("label", string=lambda text: text and "Applicants:" in text)
                if applicants_span:
                    applicants_elem = applicants_span.find_next("span")
                    if applicants_elem:
                        applicants_text = applicants_elem.text.strip()
                        applicants = int(re.search(r'\d+', applicants_text).group()) if re.search(r'\d+', applicants_text) else 0
                job_data = {
                    "job_title": title,
                    "company": company,
                    "location": location,
                    "salary": salary,
                    "skills_required": skills_str,
                    "job_link": job_link,
                    "posted_date": posted_date,
                    "applicants": applicants,
                    "source": "Naukri",
                    "experience_level": experience,
                    "role": job_title.replace("-", "_"),
                    "job_description": job_description,
                    "job_type": job_type,
                    "embedding": embedding_json
                }
                jobs.append(job_data)
                if len(jobs) >= max_jobs:
                    break
            except Exception as e:
                logging.error(f"Error processing job: {e}")
                continue
        if jobs:
            logging.info(f"Scraped {len(jobs)} jobs for {job_title} on page {page}")
        time.sleep(random.uniform(3, 5))
        return jobs
    except Exception as e:
        logging.error(f"Error scraping page {page} for {job_title}: {e}")
        return jobs
    finally:
        driver.quit()

def scrape_naukri_jobs(job_titles: List[str], max_jobs: int) -> Dict[str, List[Dict[str, Any]]]:
    conn = connect_db(DB_CONFIG)
    if not conn:
        raise Exception("Database connection not valid")
    try:
        create_table(conn)
        jobs_by_title = {title: [] for title in job_titles}
        total_jobs_scraped = 0
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for job_title in job_titles:
                for page in range(1, 4):
                    if len(jobs_by_title[job_title]) >= max_jobs:
                        break
                    futures.append(executor.submit(scrape_job_page, job_title, page, max_jobs - len(jobs_by_title[job_title])))
            for future in as_completed(futures):
                try:
                    jobs = future.result()
                    if jobs:
                        job_title = jobs[0]["role"].replace("_", "-")
                        jobs_by_title[job_title].extend(jobs[:max_jobs - len(jobs_by_title[job_title])])
                        total_jobs_scraped += len(jobs)
                except Exception as e:
                    logging.error(f"Error in thread: {e}")
        all_jobs = [job for jobs in jobs_by_title.values() for job in jobs]
        if all_jobs:
            insert_jobs(conn, all_jobs)
    except Exception as e:
        logging.error(f"Failed to scrape jobs: {e}")
    finally:
        conn.close()
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info(f"\nTotal jobs scraped: {total_jobs_scraped}")
    logging.info(f"Total execution time: {execution_time:.2f} seconds")
    logging.info(f"Average time per job: {execution_time/total_jobs_scraped:.2f} seconds" if total_jobs_scraped > 0 else "No jobs scraped")
    return jobs_by_title

if __name__ == "__main__":
    start_time = time.time()
    results = scrape_naukri_jobs(JOB_ROLES, max_jobs=100)
    for title, jobs in results.items():
        logging.info(f"Results for {title}:")
        logging.info(f"Total jobs found: {len(jobs)}")
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info(f"\nTotal execution time: {execution_time:.2f} seconds")