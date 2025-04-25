import sys
import os
import mysql.connector
import logging
from typing import Optional

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_cleaning.log'),
        logging.StreamHandler()
    ]
)

def connect_db() -> Optional[mysql.connector.connection.MySQLConnection]:
    """Establish a connection to the jobs_db database."""
    try:
        return mysql.connector.connect(
            host=Config.MYSQL["host"],
            user=Config.MYSQL["user"],
            password=Config.MYSQL["password"],
            database="jobs_db"
        )
    except mysql.connector.Error as e:
        logger.error(f"Database connection failed for jobs_db: {e}")
        return None

def validate_table_exists(cursor, table: str) -> bool:
    """Validate that the specified table exists in jobs_db."""
    try:
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'jobs_db' 
            AND TABLE_NAME = '{table}';
        """)
        return cursor.fetchone()[0] > 0
    except mysql.connector.Error as e:
        logger.error(f"Error validating table existence for jobs_db.{table}: {e}")
        return False

def clean_invalid_jobs():
    """Remove rows from the jobs table where skills_required, job_type, job_description, or applicants are invalid."""
    conn = connect_db()
    if not conn:
        logger.error("Could not connect to database jobs_db")
        return

    cursor = conn.cursor()
    table = "jobs"

    # Validate table existence
    if not validate_table_exists(cursor, table):
        logger.error(f"Table jobs_db.{table} does not exist")
        cursor.close()
        conn.close()
        return

    logger.info(f"Cleaning invalid jobs in jobs_db.{table}")
    try:
        # Construct DELETE query to remove rows with:
        # - skills_required is NULL, empty, or "Not Available"
        # - job_type is NULL, empty, or "Not Available"
        # - job_description is NULL, empty, or "Not Available"
        # - applicants is 0
        query = f"""
        DELETE FROM jobs_db.{table}
        WHERE skills_required IS NULL 
           OR skills_required = '' 
           OR skills_required = 'Not Available'
           OR job_type IS NULL 
           OR job_type = '' 
           OR job_type = 'Not Available'
           OR job_description IS NULL 
           OR job_description = '' 
           OR job_description = 'Not Available'
           OR applicants = 0;
        """
        cursor.execute(query)
        deleted_rows = cursor.rowcount
        conn.commit()
        logger.info(f"Deleted {deleted_rows} invalid rows from jobs_db.{table}")
    except mysql.connector.Error as e:
        logger.error(f"Error cleaning table {table} in jobs_db: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    """Clean invalid jobs in the jobs table of jobs_db."""
    logger.info("Starting job cleaning for database: jobs_db")
    clean_invalid_jobs()
    logger.info("Finished processing database: jobs_db")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        sys.exit(1)