from datetime import datetime, timedelta
import re
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from config import Config
from flask import request

logger = logging.getLogger(__name__)

def extract_skills_from_description(description):
    """Extract skills from job description using keyword matching."""
    if not description or not isinstance(description, str):
        return []
    known_skills = [
        "python", "java", "sql", "javascript", "react", "node.js", "aws", "docker",
        "django", "flask", "spring boot", "kubernetes", "graphql", "rest", "angular",
        "machine learning", "data analysis", "cloud computing", "git", "postgresql"
    ]
    description = description.lower()
    matched_skills = [skill for skill in known_skills if skill in description]
    return matched_skills

def calculate_job_score(user_skills, job, experience_category, preferred_location, preferred_job_type=None):
    """Calculate job match score with enhanced logic."""
    today = datetime.now().date()
    posted_date = job['posted_date']
    if isinstance(posted_date, str):
        posted_date = datetime.strptime(posted_date, '%Y-%m-%d').date()
    days_since_posting = (today - posted_date).days

    # Skill matching
    job_skills = job.get('skills_required', '').split(", ") if job.get('skills_required') else []
    desc_skills = extract_skills_from_description(job.get('job_description', ''))
    all_job_skills = list(set(job_skills + desc_skills))
    matching_skills = set(user_skills) & set(all_job_skills)
    skills_match_percentage = (len(matching_skills) / max(len(user_skills), 1)) * 100

    # Applicants score
    applicant_count = job.get('applicants', 100) or 100
    applicant_score = max(20 - min(applicant_count, 50) * 0.4, 0)

    # Salary score
    salary_score = 15  # Neutral score for "Not disclosed"
    if job.get('salary') and job['salary'] != "Not disclosed":
        match = re.search(r'(\d+\.?\d*)', job['salary'].replace("₹", "").replace("LPA", "").replace(" ", ""))
        salary_value = float(match.group(1)) * 100000 if match else 0
        salary_score = min(salary_value / 1000000 * 30, 30)

    # Location match
    location_match = preferred_location and preferred_location.lower() in job['location'].lower() if job.get('location') else False
    location_bonus = 10 if location_match else 0

    # Job type match
    job_type_match = preferred_job_type and preferred_job_type.lower() == job.get('job_type', '').lower() if job.get('job_type') else False
    type_bonus = 10 if job_type_match else 0

    # Experience match
    exp_match = 0
    user_years = float(request.form.get('total_experience_years', 0))
    exp_min = job.get('experience_years_min', 0)
    exp_max = job.get('experience_years_max', 10)
    if exp_min <= user_years <= exp_max:
        exp_match = 1

    # Scoring weights
    if experience_category == "Fresher":
        total_score = (
            skills_match_percentage * 0.5 +  # 50%
            applicant_score * 0.2 +          # 20%
            max(30 - days_since_posting * 0.1, 0) * 0.2 +  # 20%
            location_bonus + type_bonus + (exp_match * 10)
        )
        premium_score = (
            (80 if skills_match_percentage >= 70 else 0) +
            (50 if applicant_count < 50 else 0) +
            (30 if days_since_posting < 10 else 0)
        )
    else:  # Experienced
        total_score = (
            skills_match_percentage * 0.4 +  # 40%
            salary_score * 0.2 +            # 20%
            exp_match * 0.2 +              # 20%
            max(10 - days_since_posting * 0.33, 0) * 0.1 +  # 10%
            location_bonus + type_bonus
        )
        premium_score = (
            (80 if skills_match_percentage >= 70 else 0) +
            (50 if applicant_count < 50 else 0) +
            (min(salary_score * 2, 20)) +
            (30 if exp_match else 0)
        )

    return {
        'total_score': min(total_score, 100),
        'premium_score': min(premium_score, 100),
        'matching_skills': len(matching_skills),
        'matching_skills_list': list(matching_skills)
    }

def match_jobs_with_resume(user_skills, jobs, experience_category, preferred_location, resume_text="", preferred_job_type=None):
    """Match jobs with resume using TF-IDF and custom scoring."""
    if not jobs:
        logger.warning("No jobs provided for matching")
        return []

    # Combine resume skills and text for TF-IDF
    resume_content = resume_text or " ".join(user_skills)
    job_texts = [job.get('job_description', job.get('skills_required', '')) for job in jobs]

    # Compute TF-IDF similarity
    cosine_similarities = [0.5] * len(jobs)  # Default if TF-IDF fails
    if resume_content.strip() and any(text.strip() for text in job_texts):
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform([resume_content] + job_texts)
            cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        except Exception as e:
            logger.error(f"TF-IDF calculation failed: {e}")

    job_list = []
    for i, job in enumerate(jobs):
        score_data = calculate_job_score(user_skills, job, experience_category, preferred_location, preferred_job_type)
        if score_data['total_score'] > 20:  # Filter low-scoring jobs
            job.update({
                'match_score': round((cosine_similarities[i] * 50 + score_data['total_score'] * 0.5), 2),
                'matching_skills': score_data['matching_skills'],
                'matching_skills_list': score_data['matching_skills_list'],
                'is_premium': score_data['premium_score'] >= 80
            })
            job_list.append(job)

    # Sort by match score and limit to MAX_JOBS
    result = sorted(job_list, key=lambda x: x.get('match_score', 0), reverse=True)[:Config.MAX_JOBS]

    # If fewer than MAX_JOBS, add fallback jobs
    if len(result) < Config.MAX_JOBS:
        remaining_jobs = [job for job in jobs if job not in job_list]
        for job in remaining_jobs[:Config.MAX_JOBS - len(result)]:
            job.update({
                'match_score': 45,
                'matching_skills': 0,
                'matching_skills_list': [],
                'is_premium': False
            })
            result.append(job)

    logger.info(f"Returning {len(result)} jobs after matching")
    return result