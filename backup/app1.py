from flask import Flask, render_template, request
import pandas as pd
from PyPDF2 import PdfReader
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import logging

app = Flask(__name__)

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Expanded skills list
skills_list = [
    "c", "c++", "java", "python", "javascript", "typescript", "c#", "php", "go", "rust", "swift", "kotlin", "ruby",
    "html", "css", "react.js", "next.js", "angular", "vue.js", "svelte", "node.js", "express.js", "django", "flask",
    "spring boot", "laravel", "asp.net",
    "sql", "mysql", "postgresql", "mongodb", "firebase", "sqlite", "redis", "cassandra",
    "machine learning", "deep learning", "data analysis", "data visualization", "tensorflow", "pytorch", "pandas",
    "numpy", "scikit-learn", "opencv", "natural language processing (nlp)",
    "aws", "google cloud", "microsoft azure", "docker", "kubernetes", "jenkins", "terraform", "git", "ci/cd pipelines",
    "ethical hacking", "penetration testing", "network security", "cryptography", "firewalls", "wireshark",
    "linux", "shell scripting", "windows server", "kernel development",
    "git & github", "agile", "scrum", "design patterns", "software testing", "oop", "system design",
    "rest apis", "graphql", "websockets"
]

# Expanded mapping of skills to job titles
skill_to_job_mapping = {
    "Python Developer": ["python", "django", "flask", "sql", "pandas", "numpy", "scikit-learn"],
    "Java Developer": ["java", "spring boot", "hibernate", "sql"],
    "Frontend Developer": ["javascript", "typescript", "html", "css", "react.js", "next.js", "angular", "vue.js", "svelte"],
    "Backend Developer": ["node.js", "express.js", "django", "flask", "spring boot", "laravel", "sql", "mongodb", "rest apis"],
    "Full Stack Developer": ["javascript", "python", "java", "node.js", "react.js", "django", "sql", "html", "css"],
    "Data Scientist": ["machine learning", "deep learning", "data analysis", "data visualization", "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "python"],
    "DevOps Engineer": ["aws", "google cloud", "microsoft azure", "docker", "kubernetes", "jenkins", "terraform", "git", "ci/cd pipelines", "linux"],
    "Cybersecurity Analyst": ["ethical hacking", "penetration testing", "network security", "cryptography", "firewalls", "wireshark"],
    "C++ Developer": ["c", "c++", "oop", "system design"],
    "Mobile App Developer": ["swift", "kotlin", "java", "firebase"],
    "PHP Developer": ["php", "laravel", "mysql"],
    "Go Developer": ["go", "rest apis", "docker"],
    "Ruby Developer": ["ruby", "rails", "postgresql"],
    "Machine Learning Engineer": ["machine learning", "deep learning", "tensorflow", "pytorch", "python", "opencv", "natural language processing (nlp)"],
    "Database Administrator": ["sql", "mysql", "postgresql", "mongodb", "sqlite", "redis", "cassandra"],
    "Software Engineer": ["python", "java", "c++", "javascript", "git", "agile", "scrum", "design patterns", "software testing", "oop"]
}

def get_job_title_from_skills(user_skills):
    best_match = None
    max_matches = 0
    for job_title, required_skills in skill_to_job_mapping.items():
        matches = len(set(user_skills) & set(required_skills))
        if matches > max_matches:
            max_matches = matches
            best_match = job_title
    return best_match if best_match else "Software Engineer"

def scrape_jobs_with_retries(url, headers, max_retries=2, timeout=15):
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < max_retries:
                time.sleep(2)
            else:
                logger.error(f"All retries failed for {url}: {e}")
                return None
    return None

def scrape_linkedin_jobs(job_title, location="India", max_jobs=10):
    job_list = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"}
    jobs_per_page = 10
    pages = (max_jobs + jobs_per_page - 1) // jobs_per_page

    for page in range(pages):
        start = page * jobs_per_page
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={job_title}&location={location}&start={start}&sortBy=DD"
        soup = scrape_jobs_with_retries(url, headers)
        if not soup:
            break

        page_jobs = soup.find_all("li")
        for job in page_jobs:
            if len(job_list) >= max_jobs:
                break
            base_card_div = job.find("div", {"class": "base-card"})
            if base_card_div:
                job_id = base_card_div.get("data-entity-urn").split(":")[3]
                job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
                job_soup = scrape_jobs_with_retries(job_url, headers)
                if job_soup:
                    job_post = {"source": "LinkedIn", "job_url": job_url}
                    job_post["job_title"] = job_soup.find("h1", {"class": "top-card-layout__title"}).text.strip() if job_soup.find("h1", {"class": "top-card-layout__title"}) else None
                    job_post["company_name"] = job_soup.find("a", {"class": "topcard__org-name-link"}).text.strip() if job_soup.find("a", {"class": "topcard__org-name-link"}) else None
                    job_post["time_posted"] = job_soup.find("span", {"class": "posted-time-ago__text"}).text.strip() if job_soup.find("span", {"class": "posted-time-ago__text"}) else None
                    job_post["num_applicants"] = job_soup.find("span", {"class": "num-applicants__caption"}).text.strip() if job_soup.find("span", {"class": "num-applicants__caption"}) else None
                    description = job_soup.find("div", {"class": "description__text"}).text.strip().lower() if job_soup.find("div", {"class": "description__text"}) else ""
                    job_post["skills"] = ",".join([skill for skill in skills_list if skill in description])
                    job_list.append(job_post)
                    time.sleep(1)
        time.sleep(2)
    return job_list

def scrape_naukri_jobs(job_title, location="India", max_jobs=10):
    job_list = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"}
    url = f"https://www.naukri.com/{job_title.replace(' ', '-')}-jobs-in-{location.lower()}?sort=date"
    soup = scrape_jobs_with_retries(url, headers)
    if not soup:
        return job_list

    job_cards = soup.find_all("article", {"class": "jobTuple"})
    for job in job_cards[:max_jobs]:
        job_post = {"source": "Naukri"}
        job_link = job.find("a", {"class": "title"})
        job_post["job_url"] = job_link["href"] if job_link and "href" in job_link.attrs else None
        job_post["job_title"] = job_link.text.strip() if job_link else None
        job_post["company_name"] = job.find("a", {"class": "subTitle"}).text.strip() if job.find("a", {"class": "subTitle"}) else None
        job_post["time_posted"] = job.find("span", {"class": "fleft postedDate"}).text.strip() if job.find("span", {"class": "fleft postedDate"}) else None
        description = job.find("div", {"class": "job-description"}).text.strip().lower() if job.find("div", {"class": "job-description"}) else ""
        job_post["skills"] = ",".join([skill for skill in skills_list if skill in description])
        job_post["num_applicants"] = None
        if job_post["job_url"]:  # Only add if URL is valid
            job_list.append(job_post)
        time.sleep(1)
    return job_list

def scrape_indeed_jobs(job_title, location="India", max_jobs=10):
    job_list = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"}
    url = f"https://in.indeed.com/jobs?q={job_title.replace(' ', '+')}&l={location}&sort=date"
    soup = scrape_jobs_with_retries(url, headers)
    if not soup:
        return job_list

    job_cards = soup.find_all("div", {"class": "job_seen_beacon"})
    for job in job_cards[:max_jobs]:
        job_post = {"source": "Indeed"}
        job_link = job.find("a", {"class": "jcs-JobTitle"})
        job_post["job_url"] = "https://in.indeed.com" + job_link["href"] if job_link and "href" in job_link.attrs else None
        job_post["job_title"] = job_link.text.strip() if job_link else None
        job_post["company_name"] = job.find("span", {"class": "companyName"}).text.strip() if job.find("span", {"class": "companyName"}) else None
        job_post["time_posted"] = job.find("span", {"class": "date"}).text.strip() if job.find("span", {"class": "date"}) else None
        description = job.find("div", {"class": "job-snippet"}).text.strip().lower() if job.find("div", {"class": "job-snippet"}) else ""
        job_post["skills"] = ",".join([skill for skill in skills_list if skill in description])
        job_post["num_applicants"] = None
        if job_post["job_url"]:  # Only add if URL is valid
            job_list.append(job_post)
        time.sleep(1)
    return job_list

def scrape_glassdoor_jobs(job_title, location="India", max_jobs=10):
    job_list = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"}
    url = f"https://www.glassdoor.co.in/Job/{job_title.replace(' ', '-')}-jobs-SRCH_KO0,{len(job_title)}.htm?sortBy=date_desc&locT=C&locName={location}"
    soup = scrape_jobs_with_retries(url, headers)
    if not soup:
        return job_list

    job_cards = soup.find_all("li", {"class": "JobsList_jobListItem__JBBem"})
    for job in job_cards[:max_jobs]:
        job_post = {"source": "Glassdoor"}
        job_link = job.find("a", {"class": "JobCard_jobTitle___7I6y"})
        job_post["job_url"] = "https://www.glassdoor.co.in" + job_link["href"] if job_link and "href" in job_link.attrs else None
        job_post["job_title"] = job_link.text.strip() if job_link else None
        job_post["company_name"] = job.find("div", {"class": "JobCard_companyName__N1Qca"}).text.strip() if job.find("div", {"class": "JobCard_companyName__N1Qca"}) else None
        job_post["time_posted"] = job.find("div", {"class": "JobCard_listingAge__col_U"}).text.strip() if job.find("div", {"class": "JobCard_listingAge__col_U"}) else None
        description = job.find("div", {"class": "JobCard_jobDescriptionSnippet__HUIan"}).text.strip().lower() if job.find("div", {"class": "JobCard_jobDescriptionSnippet__HUIan"}) else ""
        job_post["skills"] = ",".join([skill for skill in skills_list if skill in description])
        job_post["num_applicants"] = None
        if job_post["job_url"]:  # Only add if URL is valid
            job_list.append(job_post)
        time.sleep(1)
    return job_list

@app.route('/')
def index():
    return render_template('index.html', jobs=[])

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return 'No file uploaded', 400
    file = request.files['resume']
    if file.filename == '':
        return 'No file selected', 400
    if file and file.filename.endswith('.pdf'):
        # Extract text from the PDF
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text().lower()
        # Identify skills from the resume
        user_skills = [skill for skill in skills_list if skill in text]
        if not user_skills:
            return "No recognizable skills found in your resume.", 400
        
        # Determine job title based on skills
        job_title = get_job_title_from_skills(user_skills)
        
        # Scrape latest jobs from multiple portals
        logger.info(f"Scraping jobs for title: {job_title}")
        linkedin_jobs = scrape_linkedin_jobs(job_title)
        naukri_jobs = scrape_naukri_jobs(job_title)
        indeed_jobs = scrape_indeed_jobs(job_title)
        glassdoor_jobs = scrape_glassdoor_jobs(job_title)
        
        # Aggregate all jobs
        all_jobs = linkedin_jobs + naukri_jobs + indeed_jobs + glassdoor_jobs
        failed_portals = []
        if not all_jobs:
            return "Failed to fetch real-time jobs from any portal. Please try again later.", 500
        if not linkedin_jobs:
            failed_portals.append("LinkedIn")
        if not naukri_jobs:
            failed_portals.append("Naukri")
        if not indeed_jobs:
            failed_portals.append("Indeed")
        if not glassdoor_jobs:
            failed_portals.append("Glassdoor")
        
        # Filter and sort jobs based on user skills
        for job in all_jobs:
            job_skills = job['skills'].split(',') if job['skills'] else []
            matching_skills = set(user_skills) & set(job_skills)
            job['matching_skills'] = len(matching_skills)
            job['matching_skills_list'] = list(matching_skills)
        
        # Sort by matching skills and take top 30
        all_jobs.sort(key=lambda x: x['matching_skills'], reverse=True)
        top_jobs = all_jobs[:30]
        
        # Add timestamp and failed portals info
        fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        failed_message = f"Failed to fetch from: {', '.join(failed_portals)}" if failed_portals else None
        
        logger.info(f"Returning {len(top_jobs)} jobs")
        return render_template('index.html', jobs=top_jobs, user_skills=user_skills, job_title=job_title, fetch_time=fetch_time, failed_message=failed_message)
    else:
        return 'Only PDF files are allowed', 400

if __name__ == '__main__':
    app.run(debug=True)