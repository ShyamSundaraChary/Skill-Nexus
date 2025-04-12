from datetime import datetime,timedelta
from fuzzywuzzy import fuzz
import mysql.connector
import logging
from config import Config

logger = logging.getLogger(__name__)

def connect_db(database):
    """Establish a connection to the MySQL database."""
    try:
        return mysql.connector.connect(
            host=Config.MYSQL["host"],
            user=Config.MYSQL["user"],
            password=Config.MYSQL["password"],
            database=database
        )
    except mysql.connector.Error as e:
        logger.error(f"Database connection failed: {e}")
        return None  # Return None if connection fails

def fetch_jobs_from_db(user_skills, experience_category, best_job_roles, preferred_location=None):
    """Fetch jobs from the database based on user profile, or return empty list if database is unavailable."""
    database = Config.MYSQL["fresher_db"] if experience_category == "Fresher" else Config.MYSQL["experienced_db"]
    conn = connect_db(database)
    if not conn:
        logger.warning(f"Could not connect to database {database}. Continuing without jobs.")
        return []  # Return empty list if connection fails

    cursor = conn.cursor(dictionary=True)
    thirty_days_ago = (datetime.now() - timedelta(days=Config.RECENT_DAYS)).strftime("%Y-%m-%d")

    all_jobs = []
    for job_role in best_job_roles:
        table_name = job_role.replace(" ", "_").lower()
        try:
            query = f"""
                SELECT job_title, company, location, salary, skills_required, job_link, posted_date, applicants, source
                FROM {table_name}
                WHERE posted_date >= %s
            """
            cursor.execute(query, (thirty_days_ago,))
            jobs = cursor.fetchall()
            all_jobs.extend(jobs)
        except mysql.connector.Error as e:
            logger.warning(f"Could not fetch jobs from table {table_name}: {e}")
            continue

    conn.close()

    # Add default experience_level if missing
    for job in all_jobs:
        if 'experience_level' not in job:
            job['experience_level'] = "0-1 years" if database == Config.MYSQL["fresher_db"] else "5+ years"

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

    return unique_jobs