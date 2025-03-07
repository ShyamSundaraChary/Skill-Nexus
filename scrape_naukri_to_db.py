import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3
import time
from datetime import datetime, timedelta
import logging

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

# Skills list (for potential future use)
skills_list = [
    "c", "c++", "java", "python", "javascript", "typescript", "c#", "php", "go", "rust", "swift", "kotlin", "ruby",
    "html", "css", "react.js", "next.js", "angular", "vue.js", "svelte", "node.js", "express.js", "django", "flask",
    "spring boot", "laravel", "asp.net", "sql", "mysql", "postgresql", "mongodb", "firebase", "sqlite", "redis",
    "cassandra", "machine learning", "deep learning", "data analysis", "data visualization", "tensorflow", "pytorch",
    "pandas", "numpy", "scikit-learn", "opencv", "natural language processing (nlp)", "aws", "google cloud",
    "microsoft azure", "docker", "kubernetes", "jenkins", "terraform", "git", "ci/cd pipelines", "ethical hacking",
    "penetration testing", "network security", "cryptography", "firewalls", "wireshark", "linux", "shell scripting",
    "windows server", "kernel development", "git & github", "agile", "scrum", "design patterns", "software testing",
    "oop", "system design", "rest apis", "graphql", "websockets"
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

def scrape_naukri_to_db(num_pages=5, max_jobs=50):
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            job_url TEXT UNIQUE,
            job_title TEXT,
            company_name TEXT,
            time_posted TEXT,
            num_applicants TEXT,
            skills TEXT,
            date_scraped TEXT
        )
    ''')

    base_url = "https://www.naukri.com/jobs-in-india"
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    job_list = []
    
    try:
        for page in range(1, num_pages + 1):
            url = base_url if page == 1 else f"{base_url}?page={page}"
            logger.info(f"Scraping Naukri page {page} - URL: {url}")
            
            driver.get(url)
            time.sleep(6)
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            job_listings = soup.find_all("div", class_="cust-job-tuple")
            
            if not job_listings:
                logger.warning("No jobs found on this page or structure has changed.")
                break
            
            for job in job_listings[:max_jobs - len(job_list)]:
                title_elem = job.find("a", class_="title")
                title = title_elem.text.strip() if title_elem else "N/A"
                link = title_elem['href'] if title_elem and 'href' in title_elem.attrs else "#"
                
                company_elem = job.find("a", class_="comp-name")
                company = company_elem.text.strip() if company_elem else "N/A"
                
                time_elem = job.find("span", class_="job-post-day")
                time_posted = time_elem.text.strip() if time_elem else "N/A"
                
                skills = ""
                
                job_data = ("Naukri", link, title, company, time_posted, "N/A", skills, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO jobs (source, job_url, job_title, company_name, time_posted, num_applicants, skills, date_scraped)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', job_data)
                    job_list.append({"job_url": link, "job_title": title, "company_name": company})
                    logger.info(f"Added Naukri job: {title} from {company}")
                except sqlite3.IntegrityError:
                    logger.warning(f"Duplicate job URL skipped: {link}")
            
            if len(job_list) >= max_jobs:
                break
            
            time.sleep(1)
        
        conn.commit()
        logger.info(f"Scraped and stored {len(job_list)} Naukri jobs")
    
    except Exception as e:
        logger.error(f"Error scraping Naukri: {e}")
        logger.error(f"Page source (first 2000 chars): {driver.page_source[:2000]}")
    finally:
        driver.quit()
        conn.close()

def scrape_all_to_db():
    logger.info("Starting job scraping for both portals")
    start_time = time.time()
    
    clean_old_jobs()
    scrape_naukri_to_db()
    
    end_time = time.time()
    logger.info(f"Completed scraping for both LinkedIn and Naukri in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    scrape_all_to_db()