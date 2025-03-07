# import requests
# from bs4 import BeautifulSoup
# import sqlite3
# import time
# from datetime import datetime
# import logging
# from concurrent.futures import ThreadPoolExecutor

# # Set up logging with UTF-8 encoding to handle special characters
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('scrape_jobs.log', encoding='utf-8'),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

# def fetch_job_details(job_url, headers, skills_list):
#     try:
#         response = requests.get(job_url, headers=headers, timeout=10)
#         response.raise_for_status()
#         job_soup = BeautifulSoup(response.text, "html.parser")
        
#         job_title = job_soup.find("h1", {"class": "top-card-layout__title"}).text.strip() if job_soup.find("h1", {"class": "top-card-layout__title"}) else "N/A"
#         company_name = job_soup.find("a", {"class": "topcard__org-name-link"}).text.strip() if job_soup.find("a", {"class": "topcard__org-name-link"}) else "N/A"
#         time_posted = job_soup.find("span", {"class": "posted-time-ago__text"}).text.strip() if job_soup.find("span", {"class": "posted-time-ago__text"}) else "N/A"
#         num_applicants = job_soup.find("span", {"class": "num-applicants__caption"}).text.strip() if job_soup.find("span", {"class": "num-applicants__caption"}) else "N/A"
#         description = job_soup.find("div", {"class": "description__text"}).text.strip().lower() if job_soup.find("div", {"class": "description__text"}) else ""
#         skills = ",".join([skill for skill in skills_list if skill in description])

#         return {
#             "job_title": job_title,
#             "company_name": company_name,
#             "time_posted": time_posted,
#             "num_applicants": num_applicants,
#             "skills": skills,
#             "job_url": job_url
#         }
#     except requests.RequestException as e:
#         logger.error(f"Failed to scrape job URL {job_url}: {e}")
#         return None

# def scrape_linkedin_to_db(job_title="Software Developer", location="India", max_jobs=50):  # Changed to 50
#     start_time = time.time()  # Start timer

#     headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/129.0.0.0 Safari/537.36"}
#     jobs_per_page = 10
#     pages = (max_jobs + jobs_per_page - 1) // jobs_per_page

#     conn = sqlite3.connect('jobs.db')
#     cursor = conn.cursor()

#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS jobs (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             source TEXT,
#             job_url TEXT UNIQUE,
#             job_title TEXT,
#             company_name TEXT,
#             time_posted TEXT,
#             num_applicants TEXT,
#             skills TEXT,
#             date_scraped TEXT
#         )
#     ''')

#     job_list = []
#     with ThreadPoolExecutor(max_workers=5) as executor:  # 5 concurrent workers
#         futures = []
#         for page in range(pages):
#             start = page * jobs_per_page
#             url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={job_title}&location={location}&start={start}&sortBy=DD"
#             logger.info(f"Fetching LinkedIn page with start={start}")
#             try:
#                 response = requests.get(url, headers=headers, timeout=15)
#                 response.raise_for_status()
#                 soup = BeautifulSoup(response.text, "html.parser")
#             except requests.RequestException as e:
#                 logger.error(f"Failed to scrape LinkedIn page {page}: {e}")
#                 break

#             page_jobs = soup.find_all("div", {"class": "base-card"})
#             if not page_jobs:
#                 logger.warning("No more jobs found on this page.")
#                 break

#             for job in page_jobs:
#                 if len(job_list) >= max_jobs:
#                     break
#                 job_id = job.get("data-entity-urn").split(":")[3] if job.get("data-entity-urn") else None
#                 if not job_id:
#                     logger.warning("Skipping job with missing data-entity-urn")
#                     continue
#                 job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
#                 futures.append(executor.submit(fetch_job_details, job_url, headers, skills_list))

#             time.sleep(1)  # 1s between pages

#         # Collect results
#         for future in futures:
#             result = future.result()
#             if result and len(job_list) < max_jobs:
#                 job_title = result["job_title"]
#                 company_name = result["company_name"]
#                 time_posted = result["time_posted"]
#                 num_applicants = result["num_applicants"]
#                 skills = result["skills"]
#                 job_url = result["job_url"]

#                 # Print job details to terminal
#                 print("\nFetched LinkedIn Job:")
#                 print(f"Job Title: {job_title}")
#                 print(f"Company: {company_name}")
#                 print(f"Time Posted: {time_posted}")
#                 print(f"Number of Applicants: {num_applicants}")
#                 print(f"Skills: {skills if skills else 'None'}")
#                 print(f"Job URL: {job_url}")
#                 print("-" * 50)

#                 job_data = ("LinkedIn", job_url, job_title, company_name, time_posted, num_applicants, skills, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
#                 try:
#                     cursor.execute('''
#                         INSERT OR IGNORE INTO jobs (source, job_url, job_title, company_name, time_posted, num_applicants, skills, date_scraped)
#                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#                     ''', job_data)
#                     job_list.append({"job_url": job_url, "job_title": job_title, "company_name": company_name})
#                     logger.info(f"Added LinkedIn job: {job_title} from {company_name}")
#                 except sqlite3.IntegrityError:
#                     logger.warning(f"Duplicate job URL skipped: {job_url}")

#     conn.commit()
#     end_time = time.time()  # End timer
#     total_time = end_time - start_time
#     minutes, seconds = divmod(total_time, 60)
#     print("\n" + "=" * 50)
#     print(f"🎉 Scraping Completed! 🎉")
#     print(f"Total Time Taken: {int(minutes)} minutes and {seconds:.2f} seconds")
#     print("=" * 50)
    
#     logger.info(f"Scraped and stored {len(job_list)} LinkedIn jobs")
#     conn.close()

# if __name__ == "__main__":
#     skills_list = [
#         "c", "c++", "java", "python", "javascript", "typescript", "c#", "php", "go", "rust", "swift", "kotlin", "ruby",
#         "html", "css", "react.js", "next.js", "angular", "vue.js", "svelte", "node.js", "express.js", "django", "flask",
#         "spring boot", "laravel", "asp.net",
#         "sql", "mysql", "postgresql", "mongodb", "firebase", "sqlite", "redis", "cassandra",
#         "machine learning", "deep learning", "data analysis", "data visualization", "tensorflow", "pytorch", "pandas",
#         "numpy", "scikit-learn", "opencv", "natural language processing (nlp)",
#         "aws", "google cloud", "microsoft azure", "docker", "kubernetes", "jenkins", "terraform", "git", "ci/cd pipelines",
#         "ethical hacking", "penetration testing", "network security", "cryptography", "firewalls", "wireshark",
#         "linux", "shell scripting", "windows server", "kernel development",
#         "git & github", "agile", "scrum", "design patterns", "software testing", "oop", "system design",
#         "rest apis", "graphql", "websockets"
#     ]
#     scrape_linkedin_to_db()


