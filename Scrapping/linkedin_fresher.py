from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import random
import re
import mysql.connector
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor
from settings import USER_AGENTS, SKILLS_LIST , JOB_ROLES

# User-Agent List (moved inside script for consistency)
USER_AGENTS = USER_AGENTS
# Updated Skills List
skills_list = SKILLS_LIST
# Predefined job roles and their skills
JOB_ROLES = JOB_ROLES

# Function to match job title to a predefined role
def match_job_role(job_title):
    job_title = job_title.lower()
    for role in JOB_ROLES:
        if any(keyword in job_title for keyword in role.lower().split()):
            return role
    if any(keyword in job_title for keyword in ["software", "engineer", "developer", "intern"]):
        return "Java Developer"  # Default for fresher-related titles
    return None

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

# Create Job Table for a Specific Role
def create_table(conn, role):
    cursor = conn.cursor()
    table_name = re.sub(r'[^a-zA-Z0-9_]', '_', role.lower())
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
            source VARCHAR(20) DEFAULT 'LinkedIn',
            UNIQUE (job_title, company, source)
        )
    """
    try:
        cursor.execute(query)
        conn.commit()
    except mysql.connector.Error as e:
        print(f"[ERROR] Failed to create table for {role}: {e}")
    finally:
        cursor.close()

# Insert Jobs into Respective Tables
def insert_jobs(conn, role, jobs_data):
    if not jobs_data:
        print(f"[WARNING] No jobs to insert for {role}")
        return
    cursor = conn.cursor()
    table_name = re.sub(r'[^a-zA-Z0-9_]', '_', role.lower())
    query = f"""
        INSERT IGNORE INTO {table_name} 
        (job_title, company, location, salary, skills_required, job_link, posted_date, applicants, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        print(f"[DEBUG] Attempting to insert {len(jobs_data)} jobs for {role}")
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
                "LinkedIn"
            ) for job in jobs_data
        ])
        conn.commit()
        print(f"[INFO] Inserted {cursor.rowcount} jobs for {role}")
    except mysql.connector.Error as e:
        print(f"[ERROR] Failed to insert jobs for {role}: {e}")
    finally:
        cursor.close()

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
def scrape_job_page(job_url, driver):
    try:
        driver.get(job_url)
        try:
            WebDriverWait(driver, 10).until(  # Reduced to 10 seconds
                EC.presence_of_element_located((By.CLASS_NAME, "top-card-layout"))
            )
        except:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        time.sleep(random.uniform(1, 3))  # Reduced to 1-3 seconds

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1, 2))  # Reduced to 1-2 seconds

        soup = BeautifulSoup(driver.page_source, "lxml")

        # Extract Title
        title = soup.find("h1", class_="top-card-layout__title")
        if not title:
            title = soup.find("h1")
        title = title.text.strip() if title else "Not Available"

        # Extract Company
        company_tag = soup.find("a", class_="topcard__org-name-link")
        if not company_tag:
            company_tag = soup.find("span", class_="topcard__flavor")
        company = company_tag.text.strip() if company_tag else "Not Available"

        # Extract Location
        location_tag = soup.find("span", class_="topcard__flavor--bullet")
        location = location_tag.text.strip() if location_tag else "Not Available"

        # Extract Posted Time
        metadata = soup.find("span", class_="posted-time-ago__text")
        posted_time = metadata.text.strip() if metadata else "Not Available"
        posted_date = parse_posted_date(posted_time)

        # Filter by Posted Time (within 1 month)
        today = datetime.now().date()
        if (today - posted_date).days > 30:
            print(f"[INFO] Skipping {job_url}: Posted date ({posted_date}) older than 1 month")
            return None

        # Extract Applicants
        applicants = 0
        applicants_tag = soup.find("span", class_="num-applicants__caption")
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
            else:
                stats_container = soup.find("div", class_=re.compile("stats|applicants", re.I))
                if stats_container:
                    applicant_stat = stats_container.find(string=re.compile(r'\d+\s*(applicants|applied)', re.I))
                    if applicant_stat:
                        match = re.search(r'\d+', applicant_stat)
                        if match:
                            applicants = int(match.group())

        if applicants == 0:
            print(f"[DEBUG] Could not find applicants for {job_url}. Page snippet:")
            stats_elements = soup.find_all(class_=re.compile("stat|applicants", re.I))
            for elem in stats_elements[:3]:
                print(f" - {elem.text.strip()}")

        # Extract Salary
        salary = "Not disclosed"

        # Extract Job Description and Match Skills
        description = soup.find("div", class_="show-more-less-html__markup")
        description_text = description.text.strip() if description else ""
        matched_skills = []
        for skill in skills_list:
            if re.search(rf'\b{re.escape(skill)}\b', description_text, re.IGNORECASE):
                matched_skills.append(skill)
        skills = ", ".join(matched_skills) if matched_skills else "Not Available"

       
        # Format as per schema
        job_data = {
            "job_title": title,
            "company": company,
            "location": location,
            "salary": salary,
            "skills_required": skills,
            "job_link": job_url,
            "posted_date": posted_date.strftime("%Y-%m-%d"),
            "applicants": applicants,
            "source": "LinkedIn"
        }

        return job_data
    except Exception as e:
        print(f"[ERROR] Failed to scrape {job_url}: {e}")
        return None

# Scrape Job Listings and Insert into Respective Role Tables with Parallel Processing
def scrape_linkedin_jobs(job_titles, jobs_per_title):
    # Setup WebDriver with WebDriver Manager
    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-webgl")
    driver = webdriver.Chrome(options=chrome_options, service=Service(ChromeDriverManager().install()))

    # Connect to Database
    conn = connect_db()

    # Create tables for all predefined roles
    for role in JOB_ROLES.keys():
        create_table(conn, role)

    all_jobs_data = []
    jobs_collected_per_title = {title: 0 for title in job_titles}

    try:
        for job_title in job_titles:
            print(f"\n[INFO] Scraping jobs for: {job_title}")
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title.replace('_', '%20')}&location=India&f_E=2"
            driver.get(search_url)
            
            try:
                WebDriverWait(driver, 10).until(  # Reduced to 10 seconds
                    EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__results-list"))
                )
            except Exception as e:
                print(f"[ERROR] Failed to load search results for {job_title}: {e}")
                continue

            for _ in range(2):  # Reduced to 2 scrolls
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1, 2))

            soup = BeautifulSoup(driver.page_source, "lxml")
            job_cards = soup.find_all("div", class_="base-card")

            job_urls = []
            for card in job_cards:
                link = card.find("a", class_="base-card__full-link")
                if link and link.get("href"):
                    job_urls.append(link["href"])
                if len(job_urls) >= jobs_per_title:  # Limit to jobs_per_title
                    break

            print(f"[INFO] Found {len(job_urls)} job URLs for {job_title}")

            # Parallel scraping of job URLs
            title_jobs_data = {}
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_url = {executor.submit(scrape_job_page, url, driver): url for url in job_urls}
                for future in future_to_url:
                    job_data = future.result()
                    if job_data:
                        role = match_job_role(job_data["job_title"])
                        if role:
                            if role not in title_jobs_data:
                                title_jobs_data[role] = []
                            title_jobs_data[role].append(job_data)
                            all_jobs_data.append(job_data)
                            print("\nJob Data (Schema Format):")
                            print(f"job_title: {job_data['job_title']}")
                            print(f"company: {job_data['company']}")
                            print(f"location: {job_data['location']}")
                            print(f"salary: {job_data['salary']}")
                            print(f"skills_required: {job_data['skills_required']}")
                            print(f"job_link: {job_data['job_link']}")
                            print(f"posted_date: {job_data['posted_date']}")
                            print(f"applicants: {job_data['applicants']}")
                            print(f"source: {job_data['source']}")
                            print(f"Matched Role: {role}")
                            print("-" * 50)

            # Insert jobs into respective role tables
            for role, jobs in title_jobs_data.items():
                insert_jobs(conn, role, jobs)

    except Exception as e:
        print(f"[ERROR] General error during scraping: {e}")
    finally:
        driver.quit()
        conn.close()

    print(f"\n[INFO] Total jobs scraped: {len(all_jobs_data)}")
    return all_jobs_data

# Main Execution with Timing
if __name__ == "__main__":
    start_time = time.time()

    job_titles = ["full_stack_developer", "java_developer", "python_developer"]
    jobs_per_title = 25
    scrape_linkedin_jobs(job_titles, jobs_per_title)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"\n[INFO] Total execution time: {execution_time / 60:.2f} minutes")
