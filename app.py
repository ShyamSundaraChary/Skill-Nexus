from flask import Flask, render_template, request
from PyPDF2 import PdfReader
import sqlite3
import logging
from datetime import datetime

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Skills list (same as yours)
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

# Skill-to-job mapping (same as yours)
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

def fetch_jobs_from_db(job_title, user_skills, max_jobs=30):
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    
    # Fetch jobs from both LinkedIn and Naukri
    cursor.execute('SELECT * FROM jobs WHERE job_title LIKE ?', ('%' + job_title + '%',))
    jobs = cursor.fetchall()
    conn.close()
    
    job_list = [
        {
            "source": job[1],
            "job_url": job[2],
            "job_title": job[3],
            "company_name": job[4],
            "time_posted": job[5],
            "num_applicants": job[6],
            "skills": job[7] if job[7] else "",
            "date_scraped": job[8]
        } for job in jobs
    ]
    
    for job in job_list:
        job_skills = job['skills'].split(',') if job['skills'] else []
        matching_skills = set(user_skills) & set(job_skills)
        job['matching_skills'] = len(matching_skills)
        job['matching_skills_list'] = list(matching_skills)
    
    job_list.sort(key=lambda x: x['matching_skills'], reverse=True)
    return job_list[:max_jobs]

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
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text().lower()
        user_skills = [skill for skill in skills_list if skill in text]
        if not user_skills:
            return "No recognizable skills found in your resume.", 400
        
        job_title = get_job_title_from_skills(user_skills)
        
        logger.info(f"Fetching jobs for title: {job_title} from database")
        jobs = fetch_jobs_from_db(job_title, user_skills)
        
        if not jobs:
            return "No jobs found in the database. Please try again later.", 500
        
        fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Returning {len(jobs)} jobs from database")
        return render_template('index.html', jobs=jobs, user_skills=user_skills, job_title=job_title, fetch_time=fetch_time)
    else:
        return 'Only PDF files are allowed', 400

if __name__ == '__main__':
    app.run(debug=True)