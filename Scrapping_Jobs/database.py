import mysql.connector
from mysql.connector import Error
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('database.log'), logging.StreamHandler()]
)

def connect_db(config):
    """Connect to the database using the provided config."""
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            logging.info("Database connection established")
            return conn
    except Error as e:
        logging.error(f"Database connection failed: {e}")
    return None

def create_table(conn):
    """Create the jobs table if it doesn’t exist, including an embedding column."""
    cursor = conn.cursor()
    query = """
        CREATE TABLE IF NOT EXISTS jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_title VARCHAR(100) NOT NULL,
            company VARCHAR(100) NOT NULL,
            location VARCHAR(100),
            salary VARCHAR(100),
            skills_required TEXT NOT NULL,
            job_link VARCHAR(500),
            posted_date DATE,
            applicants INT,
            source VARCHAR(20),
            experience_level VARCHAR(50),
            role VARCHAR(50),
            job_description TEXT,
            job_type VARCHAR(50),
            embedding TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (job_title, company, source),
            INDEX idx_role_date_exp (role, posted_date, experience_level),
            INDEX idx_location (location),
            INDEX idx_posted_date (posted_date)
        )
    """
    try:
        cursor.execute(query)
        conn.commit()
        logging.info("Created/Verified jobs table")
    except Error as e:
        logging.error(f"Failed to create jobs table: {e}")
    finally:
        cursor.close()

def insert_jobs(conn, jobs_data):
    """Insert job data into the jobs table, including embeddings, and return the number of inserted rows."""
    if not jobs_data:
        logging.warning("No jobs to insert")
        return 0
    cursor = conn.cursor()
    query = """
        INSERT IGNORE INTO jobs 
        (job_title, company, location, salary, skills_required, job_link, posted_date, applicants, source, experience_level, role, job_description, job_type, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        logging.info(f"Attempting to insert {len(jobs_data)} jobs")
        cursor.executemany(query, [
            (
                job["job_title"][:100],
                job["company"][:100],
                job["location"][:100] if job["location"] else None,
                job["salary"],
                job["skills_required"],
                job["job_link"],
                job["posted_date"],
                job["applicants"],
                job["source"],
                job["experience_level"],
                job["role"],
                job["job_description"],
                job["job_type"],
                job["embedding"]
            ) for job in jobs_data
        ])
        conn.commit()
        inserted_count = cursor.rowcount
        logging.info(f"Successfully inserted {inserted_count} jobs")
        return inserted_count
    except Error as e:
        logging.error(f"Failed to insert jobs: {e}")
        return 0
    finally:
        cursor.close()