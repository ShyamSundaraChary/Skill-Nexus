from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
import mysql.connector
import logging
import re
from config import Config

logger = logging.getLogger(__name__)

def connect_db():
    """Establish a connection to the MySQL database."""
    try:
        return mysql.connector.connect(
            host=Config.MYSQL["host"],
            user=Config.MYSQL["user"],
            password=Config.MYSQL["password"],
            database=Config.MYSQL["database"]
        )
    except mysql.connector.Error as e:
        logger.error(f"Database connection failed: {e}")
        return None

def parse_experience_range(exp_level):
    """Parse experience level string (e.g., '5-8 Yrs') to min/max years."""
    if not exp_level or not isinstance(exp_level, str):
        return 0, 10
    match = re.search(r'(\d+)-(\d+)|(\d+)\+', exp_level.replace(' Yrs', ''))
    if match:
        if match.group(3):  # e.g., '12+' case
            return int(match.group(3)), 20
        return int(match.group(1)), int(match.group(2))
    return 0, 10  # Default range for invalid formats

def fetch_jobs_from_db(user_skills, experience_category, best_job_roles, preferred_location=None):
    """Fetch jobs from the unified jobs table based on user profile."""
    conn = connect_db()
    if not conn:
        logger.warning(f"Could not connect to database {Config.MYSQL['database']}. Returning empty list.")
        return []

    cursor = conn.cursor(dictionary=True)
    sixty_days_ago = (datetime.now() - timedelta(days=Config.RECENT_DAYS + 30)).strftime("%Y-%m-%d")

    # Define experience range
    if experience_category == "Fresher":
        exp_min, exp_max = 0, 2
    else:  # Experienced
        exp_min, exp_max = 3, 20

    # Ensure at least one job role
    if not best_job_roles:
        best_job_roles = ["software_engineer", "full_stack_developer", "frontend_developer", "python_developer"]
    best_job_roles = list(set(best_job_roles))

    # Build query with dynamic role filter
    role_placeholders = ','.join(['%s'] * len(best_job_roles))
    query = f"""
        SELECT id, job_title, company, location, salary, skills_required, job_link, posted_date, 
               applicants, source, experience_level, job_description, job_type
        FROM jobs
        WHERE role IN ({role_placeholders})
        AND posted_date >= %s
    """
    params = best_job_roles + [sixty_days_ago]

    # Add location filter if provided
    if preferred_location:
        query += " AND location LIKE %s"
        params.append(f"%{preferred_location}%")

    query += " ORDER BY posted_date DESC LIMIT 200"

    try:
        cursor.execute(query, params)
        jobs = cursor.fetchall()
        logger.info(f"Fetched {len(jobs)} jobs from jobs table")
    except mysql.connector.Error as e:
        logger.warning(f"Could not fetch jobs: {e}")
        jobs = []
    finally:
        cursor.close()
        conn.close()

    # Filter jobs based on experience range
    filtered_jobs = []
    for job in jobs:
        job_exp_min, job_exp_max = parse_experience_range(job.get('experience_level', '0-10 Yrs'))
        if exp_min <= job_exp_max and exp_max >= job_exp_min:
            filtered_jobs.append(job)

    # Remove duplicates using fuzzy matching
    unique_jobs = []
    seen = set()
    for job in filtered_jobs:
        job_key = (job['job_title'], job['company'], job['source'])
        is_duplicate = False
        for seen_key in seen:
            if (fuzz.ratio(job_key[0], seen_key[0]) > 90 and
                fuzz.ratio(job_key[1], seen_key[1]) > 90 and
                job_key[2] == seen_key[2]):
                is_duplicate = True
                break
        if not is_duplicate:
            seen.add(job_key)
            unique_jobs.append(job)

    logger.info(f"Returning {len(unique_jobs)} unique jobs")
    logger.info("End of job fetching process\n\n\n\n")
    return unique_jobs