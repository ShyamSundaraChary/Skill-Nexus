import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3
import time
from datetime import datetime, timedelta
import logging
import concurrent.futures
from threading import Lock

# Set up logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scrape_jobs.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Skills list for filtering
skills_list = [
    "python", "javascript", "java", "sql", "aws", "docker", "react", "node.js",
    "machine learning", "data science", "devops", "cloud", "typescript", "kubernetes"
]

def clean_old_jobs():
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("DELETE FROM jobs WHERE date_scraped < ?", (cutoff_date,))
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    logger.info(f"Cleaned up {deleted_count} old jobs from database")

def scrape_page(url, page_num):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        driver.get(url)
        time.sleep(7)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_listings = soup.find_all("div", class_="cust-job-tuple")
        job_list = []
        for job in job_listings:
            title_elem = job.find("a", class_="title")
            title = title_elem.text.strip() if title_elem else "N/A"
            link = title_elem['href'] if title_elem and 'href' in title_elem.attrs else "#"
            company_elem = job.find("a", class_="comp-name")
            company = company_elem.text.strip() if company_elem else "N/A"
            time_elem = job.find("span", class_="job-post-day")
            time_posted = time_elem.text.strip() if time_elem else "N/A"
            skills_elem = job.find("ul", class_="tags has-description")
            skills = ", ".join([tag.text.strip() for tag in skills_elem.find_all("li")]) if skills_elem else ""
            is_relevant = any(skill in title.lower() or skill in skills.lower() 
                            for skill in skills_list) or skills == ""  # Include jobs even if no skills listed
            if not is_relevant:
                continue
            job_data = ("Naukri", link, title, company, time_posted, "N/A", skills, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            job_list.append(job_data)
    finally:
        driver.quit()
    return job_list

def scrape_naukri_to_db(num_pages=5, max_jobs=25):
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    base_url = "https://www.naukri.com/software-developer-it-programming-jobs-in-india"
    urls = [base_url if page_num == 1 else f"{base_url}-{page_num}" for page_num in range(1, num_pages + 1)]

    job_list = []
    job_list_lock = Lock()

    def scrape_and_collect(url, page_num):
        try:
            jobs = scrape_page(url, page_num)
            with job_list_lock:
                job_list.extend(jobs)
        except Exception as exc:
            logger.error(f"Error scraping Naukri page {page_num}: {exc}")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(scrape_and_collect, url, page_num) for url, page_num in zip(urls, range(1, num_pages + 1))]
        concurrent.futures.wait(futures)

    try:
        cursor.executemany('''
            INSERT OR IGNORE INTO jobs (source, job_url, job_title, company_name, time_posted, num_applicants, skills, date_scraped)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', job_list)
        conn.commit()
    except Exception as exc:
        logger.error(f"Error inserting jobs into database: {exc}")
    finally:
        conn.close()
    logger.info(f"Scraped and stored {len(job_list)} Naukri jobs")

def scrape_all_to_db():
    logger.info("Starting job scraping for both portals")
    start_time = time.time()
    
    clean_old_jobs()
    scrape_naukri_to_db(num_pages=5, max_jobs=25)
    
    end_time = time.time()
    logger.info(f"Completed scraping in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    from db_init import initialize_database
    initialize_database()
    scrape_all_to_db()