from flask import Flask, render_template, request
from config import Config
from database import fetch_jobs_from_db
from job_processor import match_jobs_with_resume
from resume_parser import process_resume
import logging
from datetime import datetime

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Render the initial page with no jobs."""
    return render_template('index.html', jobs=[], message=None, best_job_roles=[])

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    """Handle resume upload and job matching."""
    if 'resume' not in request.files:
        return render_template('index.html', message="No file uploaded"), 400
    file = request.files['resume']
    if file.filename == '':
        return render_template('index.html', message="No file selected"), 400
    if not file or not file.filename.endswith(('.pdf', '.docx')):
        return render_template('index.html', message="Only PDF or DOCX files are allowed"), 400

    resume_data = process_resume(file)
    if not resume_data:
        return render_template('index.html', message="Failed to extract data from resume"), 400

    user_skills = resume_data['skills']
    if not user_skills:
        return render_template('index.html', message="No recognizable skills found in your resume."), 400

    experience_category = resume_data['experience_category']
    best_job_roles = resume_data['best_job_roles']
    preferred_location = request.form.get('location', None)

    if experience_category == "Mid-Level":
        return render_template('index.html', message="Sorry, we currently only support Freshers (0-1 years) and Experienced (5+ years) candidates.", best_job_roles=best_job_roles)

    form_experience = request.form.get('experience_level')
    if form_experience != experience_category:
        return render_template('index.html', message=f"Mismatch in experience level. Resume indicates {experience_category}, but you selected {form_experience}.", best_job_roles=best_job_roles)

    request.form = request.form.copy()
    request.form['total_experience_years'] = str(resume_data['total_experience_years'])

    if not best_job_roles:
        best_job_roles = ["software_engineer"]

    logger.info(f"Fetching jobs for experience: {experience_category}, location: {preferred_location}, roles: {best_job_roles}")
    raw_jobs = fetch_jobs_from_db(user_skills, experience_category, best_job_roles, preferred_location)
    logger.info(f"Fetched {len(raw_jobs)} raw jobs, now matching with resume")
    
    jobs = match_jobs_with_resume(user_skills, raw_jobs, experience_category, preferred_location)
    logger.info(f"Matched and returning {len(jobs)} jobs")

    if jobs:
        # Pre-compute days since posting for each job
        today = datetime.now().date()
        for job in jobs:
            posted_date = job.get('posted_date')
            if isinstance(posted_date, str):
                posted_date = datetime.strptime(posted_date, '%Y-%m-%d').date()
            elif not isinstance(posted_date, datetime):
                posted_date = today
            job['days_since_posted'] = (today - posted_date).days

    if not jobs:
        return render_template('index.html', message="No jobs found matching your criteria.", best_job_roles=best_job_roles)

    fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Returning {len(jobs)} jobs")
    return render_template('index.html', jobs=jobs, user_skills=user_skills, fetch_time=fetch_time, experience_category=experience_category, best_job_roles=best_job_roles)

if __name__ == "__main__":
    app.run(debug=True)