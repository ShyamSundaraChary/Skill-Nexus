from flask import Flask, render_template, request
from PyPDF2 import PdfReader
import mysql.connector
import logging
from datetime import datetime, timedelta
import re
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
from resume_parser import process_resume, skills_list

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def connect_db(database):
    try:
        return mysql.connector.connect(
            host="localhost",
            user="shyam",
            password="shyam",
            database=database
        )
    except mysql.connector.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise

def fetch_jobs_from_db(user_skills, experience_category, best_job_roles, preferred_location=None, max_jobs=30):
    # Select database based on experience category
    database = "jobs_fresher" if experience_category == "Fresher" else "jobs_experienced"
    conn = connect_db(database)
    cursor = conn.cursor(dictionary=True)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Fetch jobs from tables corresponding to best job roles
    all_jobs = []
    for job_role in best_job_roles:
        table_name = job_role.replace(" ", "_").lower()
        try:
            # Use a try-except to handle missing experience_level column
            try:
                query = f"""
                    SELECT job_title, company, location, salary, skills_required, job_link, posted_date, applicants, source, experience_level
                    FROM {table_name}
                    WHERE posted_date >= %s
                """
                cursor.execute(query, (thirty_days_ago,))
            except mysql.connector.Error as e:
                if "Unknown column 'experience_level'" in str(e):
                    # Fallback query without experience_level
                    query = f"""
                        SELECT job_title, company, location, salary, skills_required, job_link, posted_date, applicants, source
                        FROM {table_name}
                        WHERE posted_date >= %s
                    """
                    cursor.execute(query, (thirty_days_ago,))
                else:
                    raise e

            jobs = cursor.fetchall()
            all_jobs.extend(jobs)
        except mysql.connector.Error as e:
            logger.warning(f"Could not fetch jobs from table {table_name}: {e}")
            continue

    conn.close()

    # Add default experience_level if missing
    for job in all_jobs:
        if 'experience_level' not in job:
            job['experience_level'] = "0-1 years" if database == "jobs_fresher" else "5+ years"

    # Remove duplicates using fuzzy matching
    unique_jobs = []
    seen = set()
    for job in all_jobs:
        job_key = (job['job_title'], job['company'], job['source'])
        is_duplicate = False
        for seen_key in seen:
            if (fuzz.ratio(job_key[0], seen_key[0]) > 90 and
                fuzz.ratio(job_key[1], seen_key[1]) > 90 and
                job_key[2] != seen_key[2]):
                is_duplicate = True
                break
        if not is_duplicate:
            seen.add(job_key)
            unique_jobs.append(job)

    # TF-IDF and Cosine Similarity
    resume_text = " ".join(user_skills)
    job_descriptions = [job['skills_required'] if job['skills_required'] else " " for job in unique_jobs]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([resume_text] + job_descriptions)
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    # Calculate scores and identify premium jobs
    job_list = []
    today = datetime.now().date()
    for i, job in enumerate(unique_jobs):
        job_skills = job['skills_required'].split(", ") if job['skills_required'] else []
        matching_skills = set(user_skills) & set(job_skills)
        skills_match_percentage = (len(matching_skills) / len(job_skills)) * 100 if job_skills else 0
        
        # Calculate days since posting
        days_since_posting = (today - job['posted_date']).days
        
        applicant_count = job['applicants'] if job['applicants'] is not None else 100
        salary_value = 0
        if job['salary'] != "Not disclosed":
            match = re.search(r'(\d+\.?\d*)', job['salary'].replace("₹", "").replace("LPA", "").replace(" ", ""))
            salary_value = float(match.group(1)) * 100000 if match else 0

        # Experience match
        job_exp_match = 0
        if job['experience_level']:
            years_match = re.search(r'(\d+)-(\d+)', job['experience_level']) or re.search(r'(\d+)\+', job['experience_level'])
            if years_match:
                if "+" in job['experience_level']:
                    min_years = int(years_match.group(1))
                    max_years = min_years + 5
                else:
                    min_years, max_years = map(int, years_match.groups())
                user_years = request.form.get('total_experience_years', type=float, default=0)
                if min_years <= user_years <= max_years:
                    job_exp_match = 1

        # Location match
        location_match = preferred_location and preferred_location.lower() in job['location'].lower()

        # Salary filter
        if experience_category == "Fresher":
            if salary_value > 1000000:  # Exclude jobs > ₹10 LPA
                continue
        else:  # Experienced
            if salary_value < 1000000:  # Exclude jobs < ₹10 LPA
                continue
            if skills_match_percentage < 60:  # Require 60% skills match for experienced users
                continue

        # Scoring
        if experience_category == "Fresher":
            similarity_score = (len(matching_skills) / len(job_skills)) * 50 if job_skills else 0  # 50% weight
            freshness_score = max(30 - days_since_posting, 0) * 1  # 30% weight
            applicant_score = max(50 - min(applicant_count, 50), 0) * 0.4  # 20% weight
            total_score = similarity_score + freshness_score + applicant_score + (10 if location_match else 0)
            # Premium score with higher emphasis on skills match
            premium_score = (skills_match_percentage if skills_match_percentage >= 80 else 0) + \
                           (50 if applicant_count < 30 else 0) + \
                           (30 if days_since_posting < 7 else 0)
        else:  # Experienced
            similarity_score = (len(matching_skills) / len(job_skills)) * 40 if job_skills else 0  # 40% weight
            salary_score = (salary_value / 1000000) * 30  # 30% weight
            experience_score = job_exp_match * 20  # 20% weight
            freshness_score = max(30 - days_since_posting, 0) * 0.33  # 10% weight
            total_score = similarity_score + salary_score + experience_score + freshness_score + (10 if location_match else 0)
            # Premium score with higher emphasis on skills match
            premium_score = (skills_match_percentage if skills_match_percentage >= 80 else 0) + \
                           (50 if applicant_count < 50 else 0) + \
                           (salary_value / 1000000) * 20 + \
                           (30 if job_exp_match else 0)

        job['matching_skills'] = len(matching_skills)
        job['matching_skills_list'] = list(matching_skills)
        job['total_score'] = total_score
        job['premium_score'] = premium_score
        job_list.append(job)

    # Sort by total score and identify premium jobs
    job_list.sort(key=lambda x: x['total_score'], reverse=True)
    job_list = job_list[:max_jobs]

    # Mark 5-10 premium jobs
    job_list.sort(key=lambda x: x['premium_score'], reverse=True)
    premium_count = min(10, max(5, len(job_list) // 4))  # 5-10 premium jobs
    for i, job in enumerate(job_list):
        job['is_premium'] = i < premium_count

    # Re-sort by total score for display
    job_list.sort(key=lambda x: x['total_score'], reverse=True)
    return job_list

@app.route('/')
def index():
    return render_template('index.html', jobs=[], message=None, best_job_roles=[])

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return "No file uploaded", 400
    file = request.files['resume']
    if file.filename == '':
        return "No file selected", 400
    if not file or not file.filename.endswith(('.pdf', '.docx')):
        return "Only PDF or DOCX files are allowed", 400

    # Extract text
    if file.filename.endswith('.pdf'):
        resume_data = process_resume(file)
    else:  # docx
        from docx import Document
        doc = Document(file)
        text = "".join(paragraph.text.lower() for paragraph in doc.paragraphs)
        # For docx, we need to save it temporarily as PDF or process directly
        # Here, we'll assume a PDF conversion is handled elsewhere
        return "DOCX processing not fully implemented", 400

    if not resume_data:
        return "Failed to extract data from resume", 400

    user_skills = resume_data['skills']
    if not user_skills:
        return "No recognizable skills found in your resume.", 400

    total_experience_years = resume_data['total_experience_years']
    experience_category = resume_data['experience_category']
    best_job_roles = resume_data['best_job_roles']
    preferred_location = request.form.get('location', None)

    # Check experience category
    if experience_category == "Mid-Level":
        return render_template('index.html', message="Sorry, we currently only support Freshers (0-1 years) and Experienced (5+ years) candidates.", best_job_roles=best_job_roles)

    # Validate experience category from form
    form_experience = request.form.get('experience_level')
    if form_experience != experience_category:
        return render_template('index.html', message=f"Mismatch in experience level. Resume indicates {experience_category}, but you selected {form_experience}.", best_job_roles=best_job_roles)

    # Pass total_experience_years to the form for use in fetch_jobs_from_db
    request.form = request.form.copy()
    request.form['total_experience_years'] = str(total_experience_years)

    # If no best job roles are found, default to a generic role
    if not best_job_roles:
        best_job_roles = ["software_engineer"]

    logger.info(f"Fetching jobs for experience: {experience_category}, location: {preferred_location}, roles: {best_job_roles}")
    jobs = fetch_jobs_from_db(user_skills, experience_category, best_job_roles, preferred_location)

    if not jobs:
        return render_template('index.html', message="No jobs found matching your criteria.", best_job_roles=best_job_roles)

    fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Returning {len(jobs)} jobs")
    return render_template('index.html', jobs=jobs, user_skills=user_skills, fetch_time=fetch_time, experience_category=experience_category, best_job_roles=best_job_roles)

if __name__ == "__main__":
    app.run(debug=True)