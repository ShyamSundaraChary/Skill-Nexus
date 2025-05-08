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
    """Fetch relevant jobs from the database based on user criteria, showing only jobs from the specified location."""
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
    base_query = f"SELECT {fields} FROM jobs"
  
    try:
        logger.info(f"Executing query: {query} with params: {params}")
        cursor.execute(query, params)
        jobs = cursor.fetchall()
        logger.info(f"Query fetched {len(jobs)} jobs")
    except mysql.connector.Error as e:
        logger.warning(f"Query failed: {e}")

    cursor.close()
    conn.close()
    logger.info(f"Returning {len(jobs)} jobs")
    return jobs