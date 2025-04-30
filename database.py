from datetime import datetime, timedelta
import mysql.connector
import logging
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

def fetch_jobs_from_db(preferred_location=None, experience_category=None, best_job_roles=None):
    """Fetch relevant jobs from the database based on user criteria, showing only preferred location jobs."""
    conn = connect_db()
    if not conn:
        logger.warning(f"Could not connect to database {Config.MYSQL['database']}. Returning empty list.")
        return []

    cursor = conn.cursor(dictionary=True)
    
    # Base query fields
    fields = """
        id, job_title, company, location, salary, skills_required, job_link, posted_date, 
        applicants, source, experience_level, job_description, job_type, embedding
    """
    base_query = f"SELECT DISTINCT {fields} FROM jobs"
    params = []
    jobs = []

    # Primary query: Strict filtering using indexes, only for preferred location
    if preferred_location or experience_category or best_job_roles:
        conditions = []
        if preferred_location:  # Uses idx_location
            conditions.append("LOWER(location) LIKE %s")
            params.append(f"%{preferred_location.lower()}%")
        if experience_category:  # Uses idx_role_date_exp (exp part)
            if experience_category == "Fresher":
                conditions.append("experience_level LIKE '0%'")
            elif experience_category == "Experienced":
                conditions.append("experience_level LIKE '2%' OR experience_level LIKE '5%'")
        if best_job_roles:  # Uses idx_role_date_exp (role part)
            role_conditions = []
            for role in best_job_roles:
                role_conditions.append("(job_title LIKE %s OR job_description LIKE %s)")
                params.extend([f"%{role}%", f"%{role}%"])
            if role_conditions:
                conditions.append("(" + " OR ".join(role_conditions) + ")")

        if conditions:
            query = base_query + " WHERE " + " AND ".join(conditions) + " ORDER BY posted_date DESC LIMIT 500"  # Uses idx_posted_date
            try:
                logger.info(f"Executing primary query: {query} with params: {params}")
                cursor.execute(query, params)
                jobs = cursor.fetchall()
                logger.info(f"Primary query fetched {len(jobs)} jobs")
            except mysql.connector.Error as e:
                logger.warning(f"Primary query failed: {e}")

    cursor.close()
    conn.close()
    logger.info(f"Returning {len(jobs)} jobs")
    return jobs