from datetime import datetime, timedelta
import re
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from flask import request

logger = logging.getLogger(__name__)

def calculate_job_score(user_skills, job, experience_category, preferred_location):
    """Calculate job match score based on skills, recency, applicants, and location."""
    today = datetime.now().date()
    if isinstance(job['posted_date'], str):
        posted_date = datetime.strptime(job['posted_date'], '%Y-%m-%d').date()
    elif isinstance(job['posted_date'], datetime):
        posted_date = job['posted_date'].date()
    else:
        posted_date = datetime.now().date()
    days_since_posting = (today - posted_date).days

    job_skills = job.get('skills_required', '').split(", ") if job.get('skills_required') else []
    matching_skills = set(user_skills) & set(job_skills)
    skills_match_percentage = (len(matching_skills) / max(len(job_skills), 1)) * 100 if job_skills else 0

    applicant_count = job.get('applicants', 100) or 100
    salary_value = 0
    if job['salary'] != "Not disclosed":
        match = re.search(r'(\d+\.?\d*)', job['salary'].replace("₹", "").replace("LPA", "").replace(" ", ""))
        salary_value = float(match.group(1)) * 100000 if match else 0

    location_match = preferred_location and preferred_location.lower() in job['location'].lower()
    job_exp_match = 0
    if job.get('experience_level'):
        years_match = re.search(r'(\d+)-(\d+)', job['experience_level']) or re.search(r'(\d+)\+', job['experience_level'])
        if years_match:
            if "+" in job['experience_level']:
                min_years, max_years = int(years_match.group(1)), int(years_match.group(1)) + 5
            else:
                min_years, max_years = map(int, years_match.groups())
            user_years = float(request.form.get('total_experience_years', 0))
            job_exp_match = 1 if min_years <= user_years <= max_years else 0

    if experience_category == "Fresher":
        similarity_score = skills_match_percentage * 0.5  # 50%
        freshness_score = max(30 - days_since_posting * 0.1, 0)  # 30%
        applicant_score = max(20 - min(applicant_count, 50) * 0.4, 0)  # 20%
        total_score = similarity_score + freshness_score + applicant_score + (10 if location_match else 0)
        premium_score = (80 if skills_match_percentage >= 80 else 0) + (50 if applicant_count < 30 else 0) + (30 if days_since_posting < 7 else 0)
        if salary_value > 1000000:
            total_score = 0  # Exclude high-salary jobs for freshers
    else:  # Experienced
        similarity_score = skills_match_percentage * 0.4  # 40%
        salary_score = min(salary_value / 1000000 * 30, 30)  # 30%
        experience_score = job_exp_match * 20  # 20%
        freshness_score = max(10 - days_since_posting * 0.33, 0)  # 10%
        total_score = similarity_score + salary_score + experience_score + freshness_score + (10 if location_match else 0)
        premium_score = (80 if skills_match_percentage >= 80 else 0) + (50 if applicant_count < 50 else 0) + (min(salary_value / 1000000 * 20, 20)) + (30 if job_exp_match else 0)
        if salary_value < 1000000 or skills_match_percentage < 60:
            total_score = 0  # Exclude low-salary or low-skill-match jobs for experienced

    return {
        'total_score': min(total_score, 100),
        'premium_score': min(premium_score, 100),
        'matching_skills': len(matching_skills),
        'matching_skills_list': list(matching_skills)
    }

def match_jobs_with_resume(user_skills, jobs, experience_category, preferred_location):
    """Match jobs with resume using TF-IDF and custom scoring."""
    resume_text = " ".join(user_skills)
    job_descriptions = [job.get('skills_required', ' ') for job in jobs]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([resume_text] + job_descriptions)
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    job_list = []
    for i, job in enumerate(jobs):
        score_data = calculate_job_score(user_skills, job, experience_category, preferred_location)
        if score_data['total_score'] > 0:
            job.update({
                'match_score': round((cosine_similarities[i] * 50 + score_data['total_score'] * 0.5), 2),
                'matching_skills': score_data['matching_skills'],
                'matching_skills_list': score_data['matching_skills_list'],
                'is_premium': score_data['premium_score'] >= 80
            })
            job_list.append(job)

    return sorted(job_list, key=lambda x: x.get('match_score', 0), reverse=True)[:30]