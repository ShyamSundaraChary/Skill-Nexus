from flask import Flask, render_template, request, jsonify
from config import Config
from database import fetch_jobs_from_db
from job_processor import match_jobs_with_resume
from resume_parser import process_resume
import logging
from datetime import datetime, date
from dateutil.parser import parse as parse_date
import time
import os
import uuid
import re
from collections import Counter
from Scrapping_Jobs.settings import SKILLS_LIST

app = Flask(_name_)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name_)

@app.route('/')
def index():
    """Render the initial page with no jobs."""
    return render_template('index.html', jobs=[], message=None, best_job_roles=[])

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    """Handle resume upload and job matching."""
    start_time = time.time()
    
    # Edge case: Check if resume file is provided
    if 'resume' not in request.files:
        logger.error("No resume file provided in request")
        return render_template('index.html', jobs=[], message="No file uploaded", best_job_roles=[]), 400
    file = request.files['resume']
    
    # Edge case: Check if file is selected
    if file.filename == '':
        logger.error("No file selected for upload")
        return render_template('index.html', jobs=[], message="No file selected", best_job_roles=[]), 400
    
    # Edge case: Validate file type
    if not file or not file.filename.lower().endswith(('.pdf', '.docx')):
        logger.error(f"Invalid file type uploaded: {file.filename}")
        return render_template('index.html', jobs=[], message="Only PDF or DOCX files are allowed", best_job_roles=[]), 400

    # Validate file size (5MB max)
    if file.content_length and file.content_length > 5 * 1024 * 1024:
        logger.error(f"File too large: {file.content_length} bytes")
        return render_template('index.html', jobs=[], message="File size should be less than 5MB", best_job_roles=[]), 400

    # Process resume
    try:
        resume_data = process_resume(file)
    except Exception as e:
        logger.error(f"Resume processing error: {e}")
        return render_template('index.html', jobs=[], message="Failed to process resume. Please try again.", best_job_roles=[]), 500
    
    # Edge case: Check if resume processing failed
    if not resume_data:
        logger.error("Failed to extract data from resume")
        return render_template('index.html', jobs=[], message="Failed to extract data from resume", best_job_roles=[]), 400

    resume_text = resume_data.get('resume_text', '')
    experience_category = resume_data.get('experience_category', None)
    best_job_roles = resume_data.get('best_job_roles', [])
    
    # Extract skills from resume
    resume_skills = extract_skills(resume_text)
    
    # Get user preferences from form
    preferred_location = request.form.get('location', '').strip()
    experience_level = request.form.get('experience_level', None)
    
    # Use form input for experience if available, otherwise use the parsed value
    if experience_level:
        experience_category = experience_level

    # Edge case: Validate experience_level
    if not experience_category:
        logger.warning("No experience category provided in resume data")
        return render_template('index.html', jobs=[], message="Please provide experience level", best_job_roles=best_job_roles), 400

    logger.info(f"Fetching jobs for location: {preferred_location}, experience: {experience_category}, roles: {best_job_roles}")
    
    # Fetch jobs
    try:
        raw_jobs = fetch_jobs_from_db(preferred_location, experience_category, best_job_roles)
    except Exception as e:
        logger.error(f"Database fetch failed: {e}")
        return render_template('index.html', jobs=[], message="Error fetching jobs. Please try again later.", best_job_roles=best_job_roles), 500

    # Edge case: No jobs found
    no_jobs_found = len(raw_jobs) == 0
    if no_jobs_found:
        logger.info("No jobs found in database")
        return render_template('index.html', jobs=[], message="No jobs found matching your criteria. Try broadening your search.", best_job_roles=best_job_roles)

    # Check for experience mismatch
    experience_mismatch = experience_category and not any(is_experience_match(job['experience_level'], experience_category) for job in raw_jobs)
    
    # Set message based on experience mismatch
    message = None
    if experience_mismatch:
        message = "Experience levels don't match closely. Consider adjusting your experience level."

    # Match jobs with resume
    match_start = time.time()
    try:
        jobs = match_jobs_with_resume(resume_text, raw_jobs)
        
        # Add skill matching
        for job in jobs:
            # Extract skills from job description
            job_description = job.get('job_description', '') or ''
            job_skills = extract_skills(job_description)
            
            # Find matched skills
            matched_skills = []
            if resume_skills and job_skills:
                matched_skills = list(set(resume_skills) & set(job_skills))
                
            # Sort matched skills by relevance/frequency
            if matched_skills:
                # Count occurrences in job description to determine relevance
                skill_counts = Counter()
                for skill in matched_skills:
                    # Count occurrences with word boundaries
                    pattern = r'\b' + re.escape(skill) + r'\b'
                    skill_counts[skill] = len(re.findall(pattern, job_description, re.IGNORECASE))
                
                # Sort by frequency
                matched_skills = [skill for skill, _ in skill_counts.most_common()]
            
            job['matched_skills'] = matched_skills
            
            # Update match score based on skill matching
            if matched_skills:
                # Adjust match score: 
                # Base score (from the job_processor) + bonus for matched skills (max 20% bonus)
                skill_bonus = min(len(matched_skills) * 4, 20)  # 4% per skill, max 20%
                job['match_score'] = min(job.get('match_score', 0) + skill_bonus, 100)  # Cap at 100%
    except Exception as e:
        logger.error(f"Job matching failed: {e}")
        return render_template('index.html', jobs=[], message="Error matching jobs. Please try again.", best_job_roles=best_job_roles), 500

    logger.info(f"Matched {len(jobs)} jobs in {time.time() - match_start:.2f} seconds")

    # Edge case: No matched jobs
    if not jobs:
        logger.info("No jobs matched after processing")
        return render_template('index.html', jobs=[], message="No jobs matched your resume.", best_job_roles=best_job_roles)

    # Pre-compute days since posting
    today = date.today()
    for job in jobs:
        # Ensure job has an ID for display
        if 'id' not in job or not job['id']:
            job['id'] = str(uuid.uuid4())
            
        posted_date = job.get('posted_date')
        try:
            if isinstance(posted_date, str):
                posted_date = parse_date(posted_date).date()
            elif isinstance(posted_date, datetime):
                posted_date = posted_date.date()
            elif isinstance(posted_date, date):
                posted_date = posted_date  # Already a date object, no conversion needed
            else:
                logger.warning(f"Invalid posted_date type for job {job.get('id', 'unknown')}: type={type(posted_date)}, value={posted_date}")
                posted_date = today
            days_since_posted = (today - posted_date).days
            job['days_since_posted'] = max(0, days_since_posted)
        except Exception as e:
            logger.error(f"Error parsing posted_date for job {job.get('id', 'unknown')}: type={type(posted_date)}, value={posted_date}, error={e}")
            job['days_since_posted'] = 0

    fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_time = time.time() - start_time
    logger.info(f"Returning {len(jobs)} jobs, total processing time: {total_time:.2f} seconds")

    return render_template('index.html', jobs=jobs, fetch_time=fetch_time, best_job_roles=best_job_roles, message=message)

def extract_skills(text):
    """Extract skills from text using common skill keywords."""
    common_skills = SKILLS_LIST
    
    # Extract skills from text
    found_skills = []
    text_lower = text.lower()
    
    for skill in common_skills:
        # Look for whole word matches with word boundaries
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
    
    return found_skills

def is_experience_match(job_exp_level, user_exp_category):
    """Check if job experience level matches user experience category."""
    if not job_exp_level or not user_exp_category:
        return False
    job_min, job_max = parse_experience_range(job_exp_level)
    user_min, user_max = get_user_experience_range(user_exp_category)
    return user_min <= job_max and user_max >= job_min

def parse_experience_range(exp_level):
    """Parse experience level string (e.g., '5-8 Yrs') to min/max years."""
    import re
    if not exp_level or not isinstance(exp_level, str):
        return 0, 10
    match = re.search(r'(\d+)-(\d+)|(\d+)\+', exp_level.replace(' Yrs', ''))
    if match:
        if match.group(3):
            return int(match.group(3)), 20
        return int(match.group(1)), int(match.group(2))
    if 'Fresher' in exp_level or 'Entry' in exp_level:
        return 0, 2
    if 'Mid-Senior' in exp_level or 'Senior' in exp_level:
        return 3, 10
    return 0, 10

def get_user_experience_range(experience_category):
    """Get min/max experience years based on category."""
    return (0, 2) if experience_category == "Fresher" else (3, 20) if experience_category == "Experienced" else (0, 20)

if _name_ == "_main_":
    app.run(debug=True)
