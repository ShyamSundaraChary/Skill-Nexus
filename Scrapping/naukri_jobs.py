# import threading
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup
# import mysql.connector
# from datetime import datetime, timedelta
# import time
# import concurrent.futures
# import random
# import re

# # User-Agent List
# USER_AGENTS = [
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:121.0) Gecko/20100101 Firefox/121.0",
#     "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.91",
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.2151.97",
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
#     "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
# ]

# # Database Connection
# def connect_db():
#     try:
#         return mysql.connector.connect(
#             host="localhost",
#             user="shyam",
#             password="shyam",
#             database="jobs_fresher"
#         )
#     except mysql.connector.Error as e:
#         print(f"[ERROR] Database connection failed: {e}")
#         raise

# # Create Job Table
# def create_table(conn, job_title):
#     cursor = conn.cursor()
#     table_name = job_title.replace(" ", "_").lower()
#     query = f"""
#         CREATE TABLE IF NOT EXISTS {table_name} (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             job_title VARCHAR(100) NOT NULL,
#             company VARCHAR(100) NOT NULL,
#             location VARCHAR(100),
#             salary VARCHAR(100),
#             skills_required TEXT NOT NULL,
#             job_link VARCHAR(500),
#             posted_date DATE,
#             applicants INT,
#             source VARCHAR(20) DEFAULT 'Naukri',
#             UNIQUE (job_title, company, source)
#         )
#     """
#     try:
#         cursor.execute(query)
#         conn.commit()
#     except mysql.connector.Error as e:
#         print(f"[ERROR] Failed to create table for {job_title}: {e}")
#     finally:
#         cursor.close()

# # Insert Jobs into DB with Dynamic Source
# def insert_jobs(conn, job_title, jobs_data, source):
#     if not jobs_data:
#         print(f"[WARNING] No jobs to insert for {job_title} from {source}")
#         return
#     cursor = conn.cursor()
#     table_name = job_title.replace(" ", "_").lower()
#     query = f"""
#         INSERT IGNORE INTO {table_name} 
#         (job_title, company, location, salary, skills_required, job_link, posted_date, applicants, source)
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#     """
#     try:
#         print(f"[DEBUG] Attempting to insert {len(jobs_data)} jobs for {job_title} from {source}")
#         cursor.executemany(query, [
#             (
#                 job["job_title"][:100],
#                 job["company"][:100],
#                 job["location"][:100],
#                 job["salary"],
#                 job["skills_required"],
#                 job["job_link"],
#                 job["posted_date"],
#                 job["applicants"],
#                 source[:20]
#             ) for job in jobs_data
#         ])
#         conn.commit()
#         print(f"[INFO] Inserted {cursor.rowcount} jobs for {job_title} from {source}")
#     except mysql.connector.Error as e:
#         print(f"[ERROR] Failed to insert jobs for {job_title} from {source}: {e}")
#     finally:
#         cursor.close()

# # Parse Posted Date
# def parse_posted_date(posted_text):
#     try:
#         posted_text = posted_text.lower()
#         today = datetime.now().date()
#         if "today" in posted_text:
#             return today
#         elif "yesterday" in posted_text:
#             return today - timedelta(days=1)
#         elif "day" in posted_text:
#             days = int(re.search(r'\d+', posted_text).group())
#             return today - timedelta(days=days)
#         else:
#             return today
#     except:
#         return datetime.now().date()

# # Get Total Pages (Updated)
# def get_total_pages(driver, base_url):
#     try:
#         driver.get(base_url)
#         # Wait explicitly for job listings or pagination to appear
#         WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.CLASS_NAME, "srp-jobtuple-wrapper"))  # Job listings
#         )
#         time.sleep(random.uniform(3, 5))  # Extra buffer for dynamic content

#         soup = BeautifulSoup(driver.page_source, "lxml")
#         # Try multiple pagination selectors
#         pagination = soup.find("div", class_="pagination") or soup.find("div", class_=re.compile("pagination", re.I))
#         if pagination:
#             last_page = pagination.find_all("a")[-2].text if len(pagination.find_all("a")) > 1 else "1"
#             print(f"[DEBUG] Total pages for {base_url}: {last_page}")
#             return int(last_page)
        
#         # If no pagination found, log the issue and page snippet for debugging
#         print(f"[DEBUG] No pagination found for {base_url}, defaulting to 1 page")
#         print(f"[DEBUG] Page snippet: {str(soup)[:500]}")  # First 500 chars of page source
#         return 1
#     except Exception as e:
#         print(f"[ERROR] Failed to get total pages for {base_url}: {e}")
#         return 1

# # Scrape Applicants from Individual Job Page
# def scrape_applicants(job_url, driver_path):
#     service = Service(driver_path)
#     chrome_options = Options()
#     chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--window-size=1920,1080")
#     driver = webdriver.Chrome(service=service, options=chrome_options)

#     applicants = 0
#     try:
#         driver.get(job_url)
#         time.sleep(random.uniform(5, 8))
        
#         soup = BeautifulSoup(driver.page_source, "lxml")
        
#         # Strategy 1: Look for label with "Applicants:"
#         applicants_span = soup.find("label", string=lambda text: text and "Applicants:" in text)
#         if applicants_span:
#             applicants_elem = applicants_span.find_next("span")
#             if applicants_elem:
#                 applicants_text = applicants_elem.text.strip()
#                 applicants = int(re.search(r'\d+', applicants_text).group()) if re.search(r'\d+', applicants_text) else 0
#                 return applicants

#         # Strategy 2: Look for stats container
#         stats_container = soup.find("div", class_=re.compile("stats", re.I))
#         if stats_container:
#             applicant_stat = stats_container.find(string=re.compile(r'\d+\s*Applicants', re.I))
#             if applicant_stat:
#                 applicants = int(re.search(r'\d+', applicant_stat).group())
#                 return applicants

#         # Strategy 3: Look for any element with "Applicants" and a number
#         applicant_text = soup.find(string=re.compile(r'\d+\s*Applicants', re.I))
#         if applicant_text:
#             applicants = int(re.search(r'\d+', applicant_text).group())
#             return applicants

#         print(f"[DEBUG] Could not find applicants for {job_url}. Page snippet:")
#         stats_elements = soup.find_all(class_=re.compile("stat", re.I))
#         for elem in stats_elements[:3]:
#             print(f" - {elem.text.strip()}")

#     except Exception as e:
#         print(f"[ERROR] Failed to scrape applicants for {job_url}: {e}")
#     finally:
#         driver.quit()

#     return applicants

# # Scrape Single Page
# def scrape_page(job_title, page_url, driver_path, max_jobs):
#     service = Service(driver_path)
#     chrome_options = Options()
#     chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#     chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     driver = webdriver.Chrome(service=service, options=chrome_options)

#     jobs_data = []
#     try:
#         driver.get(page_url)
#         WebDriverWait(driver, 15).until(
#             EC.presence_of_element_located((By.CLASS_NAME, "srp-jobtuple-wrapper"))
#         )

#         for _ in range(5):
#             driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#             time.sleep(random.uniform(2, 4))

#         soup = BeautifulSoup(driver.page_source, "lxml")
#         jobs = soup.find_all("div", class_="srp-jobtuple-wrapper")
#         print(f"[DEBUG] Found {len(jobs)} jobs on page {page_url}")
#         unique_jobs = set()

#         for job in jobs:
#             try:
#                 title_tag = job.find("a", class_="title")
#                 company_tag = job.find("a", class_="comp-name")
#                 location_tag = job.find("span", class_="locWdth")
#                 salary_tag = job.find("span", class_="sal")
#                 skills_tags = job.find_all("li", class_="tag-li")
#                 posted_date_tag = job.find("span", class_="job-post-day")

#                 title = title_tag.text.strip() if title_tag else "Not Available"
#                 company = company_tag.text.strip() if company_tag else "Not Available"
#                 location = location_tag.text.strip() if location_tag else "Not Available"
#                 salary = salary_tag.text.strip() if salary_tag else "Not Disclosed"
#                 skills = ", ".join([skill.text.strip() for skill in skills_tags]) if skills_tags else "Not Available"
#                 job_link = title_tag["href"] if title_tag else "Not Available"
#                 posted_date = parse_posted_date(posted_date_tag.text.strip()) if posted_date_tag else datetime.now().date()

#                 applicants = 0
#                 if job_link != "Not Available":
#                     applicants = scrape_applicants(job_link, driver_path)
#                     time.sleep(random.uniform(3, 5))

#                 job_key = (title, company, str(posted_date))
#                 if job_key in unique_jobs:
#                     continue

#                 jobs_data.append({
#                     "job_title": title,
#                     "company": company,
#                     "location": location,
#                     "salary": salary,
#                     "skills_required": skills,
#                     "job_link": job_link,
#                     "posted_date": posted_date,
#                     "applicants": applicants
#                 })
#                 unique_jobs.add(job_key)
#             except Exception as e:
#                 print(f"[ERROR] Error scraping job on {page_url}: {e}")
#                 continue

#     except Exception as e:
#         print(f"[ERROR] Failed to scrape page {page_url}: {e}")
#     finally:
#         driver.quit()

#     return jobs_data

# # Scrape Fresher Jobs with Dynamic Source
# def scrape_fresher_jobs(job_title, driver_path, source="Naukri", max_jobs=15):
#     try:
#         conn = connect_db()
#         create_table(conn, job_title)
#         base_url = f"https://www.naukri.com/fresher-jobs?k={job_title.replace(' ', '%20')}&jobAge=7"

#         temp_driver = webdriver.Chrome(service=Service(driver_path), options=Options().add_argument("--headless"))
#         total_pages = get_total_pages(temp_driver, base_url)
#         temp_driver.quit()
#         urls = [f"{base_url}&pageNo={i}" for i in range(1, total_pages + 1)]

#         all_jobs_data = []
#         with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
#             futures = [executor.submit(scrape_page, job_title, url, driver_path, max_jobs) for url in urls]
#             for future in concurrent.futures.as_completed(futures):
#                 try:
#                     jobs = future.result()
#                     all_jobs_data.extend(jobs)
#                     if len(all_jobs_data) >= max_jobs:
#                         break
#                 except Exception as e:
#                     print(f"[ERROR] Failed to process future for {job_title} from {source}: {e}")

#         all_jobs_data = all_jobs_data[:max_jobs]
#         print(f"[DEBUG] Final total jobs scraped for {job_title} from {source}: {len(all_jobs_data)}")
#         insert_jobs(conn, job_title, all_jobs_data, source)
#     except Exception as e:
#         print(f"[ERROR] Failed to scrape jobs for {job_title} from {source}: {e}")
#     finally:
#         conn.close()

# # Main Execution
# if __name__ == "__main__":
#     start_time = time.time()  # Record start time

#     driver_path = "C:/Users/shyam/OneDrive/Desktop/job-portal-app/chromedriver-win64/chromedriver.exe"
#     job_titles = ["Full Stack Developer", "Python Developer"]
#     threads = []

#     for job_title in job_titles:
#         thread = threading.Thread(target=scrape_fresher_jobs, args=(job_title, driver_path, "Naukri", 15))
#         threads.append(thread)
#         thread.start()
#         time.sleep(random.uniform(2, 4))

#     for thread in threads:
#         thread.join()
    
#     print("All fresher job scraping completed!")

#     end_time = time.time()  # Record end time
#     execution_time = end_time - start_time
#     print(f"Total execution time: {execution_time:.2f} seconds")








import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import mysql.connector
from datetime import datetime, timedelta
import time
import concurrent.futures
import random
import re

# User-Agent List
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.91",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.2151.97",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
]

# Database Connection
def connect_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="shyam",
            password="shyam",
            database="jobs_fresher"
        )
    except mysql.connector.Error as e:
        print(f"[ERROR] Database connection failed: {e}")
        raise

# Create Job Table (Updated with experience_level)
def create_table(conn, job_title):
    cursor = conn.cursor()
    table_name = job_title.replace(" ", "_").lower()
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
            experience_level VARCHAR(50) DEFAULT '0-1 years',
            UNIQUE (job_title, company, source)
        )
    """
    try:
        cursor.execute(query)
        conn.commit()
    except mysql.connector.Error as e:
        print(f"[ERROR] Failed to create table for {job_title}: {e}")
    finally:
        cursor.close()

# Insert Jobs into DB with Dynamic Source (Updated to include experience_level)
def insert_jobs(conn, job_title, jobs_data, source):
    if not jobs_data:
        print(f"[WARNING] No jobs to insert for {job_title} from {source}")
        return
    cursor = conn.cursor()
    table_name = job_title.replace(" ", "_").lower()
    query = f"""
        INSERT IGNORE INTO {table_name} 
        (job_title, company, location, salary, skills_required, job_link, posted_date, applicants, source, experience_level)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        print(f"[DEBUG] Attempting to insert {len(jobs_data)} jobs for {job_title} from {source}")
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
                source[:20],
                "0-1 years"  # Default for fresher jobs
            ) for job in jobs_data
        ])
        conn.commit()
        print(f"[INFO] Inserted {cursor.rowcount} jobs for {job_title} from {source}")
    except mysql.connector.Error as e:
        print(f"[ERROR] Failed to insert jobs for {job_title} from {source}: {e}")
    finally:
        cursor.close()

# Parse Posted Date
def parse_posted_date(posted_text):
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
        else:
            return today
    except:
        return datetime.now().date()

# Get Total Pages
def get_total_pages(driver, base_url):
    try:
        driver.get(base_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "srp-jobtuple-wrapper"))
        )
        time.sleep(random.uniform(3, 5))

        soup = BeautifulSoup(driver.page_source, "lxml")
        pagination = soup.find("div", class_="pagination") or soup.find("div", class_=re.compile("pagination", re.I))
        if pagination:
            last_page = pagination.find_all("a")[-2].text if len(pagination.find_all("a")) > 1 else "1"
            print(f"[DEBUG] Total pages for {base_url}: {last_page}")
            return int(last_page)
        
        print(f"[DEBUG] No pagination found for {base_url}, defaulting to 1 page")
        print(f"[DEBUG] Page snippet: {str(soup)[:500]}")
        return 1
    except Exception as e:
        print(f"[ERROR] Failed to get total pages for {base_url}: {e}")
        return 1

# Scrape Applicants from Individual Job Page
def scrape_applicants(job_url, driver_path):
    service = Service(driver_path)
    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    applicants = 0
    try:
        driver.get(job_url)
        time.sleep(random.uniform(5, 8))
        
        soup = BeautifulSoup(driver.page_source, "lxml")
        
        applicants_span = soup.find("label", string=lambda text: text and "Applicants:" in text)
        if applicants_span:
            applicants_elem = applicants_span.find_next("span")
            if applicants_elem:
                applicants_text = applicants_elem.text.strip()
                applicants = int(re.search(r'\d+', applicants_text).group()) if re.search(r'\d+', applicants_text) else 0
                return applicants

        stats_container = soup.find("div", class_=re.compile("stats", re.I))
        if stats_container:
            applicant_stat = stats_container.find(string=re.compile(r'\d+\s*Applicants', re.I))
            if applicant_stat:
                applicants = int(re.search(r'\d+', applicant_stat).group())
                return applicants

        applicant_text = soup.find(string=re.compile(r'\d+\s*Applicants', re.I))
        if applicant_text:
            applicants = int(re.search(r'\d+', applicant_text).group())
            return applicants

        print(f"[DEBUG] Could not find applicants for {job_url}. Page snippet:")
        stats_elements = soup.find_all(class_=re.compile("stat", re.I))
        for elem in stats_elements[:3]:
            print(f" - {elem.text.strip()}")

    except Exception as e:
        print(f"[ERROR] Failed to scrape applicants for {job_url}: {e}")
    finally:
        driver.quit()

    return applicants

# Scrape Single Page
def scrape_page(job_title, page_url, driver_path, max_jobs):
    service = Service(driver_path)
    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(service=service, options=chrome_options)

    jobs_data = []
    try:
        driver.get(page_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "srp-jobtuple-wrapper"))
        )

        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))

        soup = BeautifulSoup(driver.page_source, "lxml")
        jobs = soup.find_all("div", class_="srp-jobtuple-wrapper")
        print(f"[DEBUG] Found {len(jobs)} jobs on page {page_url}")
        unique_jobs = set()

        for job in jobs:
            try:
                title_tag = job.find("a", class_="title")
                company_tag = job.find("a", class_="comp-name")
                location_tag = job.find("span", class_="locWdth")
                salary_tag = job.find("span", class_="sal")
                skills_tags = job.find_all("li", class_="tag-li")
                posted_date_tag = job.find("span", class_="job-post-day")

                title = title_tag.text.strip() if title_tag else "Not Available"
                company = company_tag.text.strip() if company_tag else "Not Available"
                location = location_tag.text.strip() if location_tag else "Not Available"
                salary = salary_tag.text.strip() if salary_tag else "Not Disclosed"
                skills = ", ".join([skill.text.strip() for skill in skills_tags]) if skills_tags else "Not Available"
                job_link = title_tag["href"] if title_tag else "Not Available"
                posted_date = parse_posted_date(posted_date_tag.text.strip()) if posted_date_tag else datetime.now().date()

                applicants = 0
                if job_link != "Not Available":
                    applicants = scrape_applicants(job_link, driver_path)
                    time.sleep(random.uniform(3, 5))

                job_key = (title, company, str(posted_date))
                if job_key in unique_jobs:
                    continue

                jobs_data.append({
                    "job_title": title,
                    "company": company,
                    "location": location,
                    "salary": salary,
                    "skills_required": skills,
                    "job_link": job_link,
                    "posted_date": posted_date,
                    "applicants": applicants
                })
                unique_jobs.add(job_key)
            except Exception as e:
                print(f"[ERROR] Error scraping job on {page_url}: {e}")
                continue

    except Exception as e:
        print(f"[ERROR] Failed to scrape page {page_url}: {e}")
    finally:
        driver.quit()

    return jobs_data

# Scrape Fresher Jobs with Dynamic Source
def scrape_fresher_jobs(job_title, driver_path, source="Naukri", max_jobs=15):
    try:
        conn = connect_db()
        create_table(conn, job_title)
        base_url = f"https://www.naukri.com/fresher-jobs?k={job_title.replace(' ', '%20')}&jobAge=7"

        temp_driver = webdriver.Chrome(service=Service(driver_path), options=Options().add_argument("--headless"))
        total_pages = get_total_pages(temp_driver, base_url)
        temp_driver.quit()
        urls = [f"{base_url}&pageNo={i}" for i in range(1, total_pages + 1)]

        all_jobs_data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(scrape_page, job_title, url, driver_path, max_jobs) for url in urls]
            for future in concurrent.futures.as_completed(futures):
                try:
                    jobs = future.result()
                    all_jobs_data.extend(jobs)
                    if len(all_jobs_data) >= max_jobs:
                        break
                except Exception as e:
                    print(f"[ERROR] Failed to process future for {job_title} from {source}: {e}")

        all_jobs_data = all_jobs_data[:max_jobs]
        print(f"[DEBUG] Final total jobs scraped for {job_title} from {source}: {len(all_jobs_data)}")
        insert_jobs(conn, job_title, all_jobs_data, source)
    except Exception as e:
        print(f"[ERROR] Failed to scrape jobs for {job_title} from {source}: {e}")
    finally:
        conn.close()

# Main Execution
if __name__ == "__main__":
    start_time = time.time()

    driver_path = "C:/Users/shyam/OneDrive/Desktop/job-portal-app/chromedriver-win64/chromedriver.exe"
    job_titles = ["Full Stack Developer", "Python Developer"]
    threads = []

    for job_title in job_titles:
        thread = threading.Thread(target=scrape_fresher_jobs, args=(job_title, driver_path, "Naukri", 15))
        threads.append(thread)
        thread.start()
        time.sleep(random.uniform(2, 4))

    for thread in threads:
        thread.join()
    
    print("All fresher job scraping completed!")

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Total execution time: {execution_time:.2f} seconds")