import mysql.connector
import logging
import sys
import os
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
        return None

def get_all_tables(database):
    """Retrieve all table names from the specified database."""
    conn = connect_db(database)
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{database}'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def clean_mismatched_jobs(database):
    """Remove rows from each table where job_title does not match the table name."""
    conn = connect_db(database)
    if not conn:
        logger.error(f"Could not connect to database {database}")
        return

    cursor = conn.cursor()
    tables = get_all_tables(database)
    logger.info(f"Found {len(tables)} tables in {database}: {tables}")

    for table in tables:
        # Convert table name to expected job role (e.g., full_stack_developer -> full stack)
        expected_role = table.replace('_', ' ')
        expected_role_without_developer = expected_role.replace(' developer', '')

        # Construct DELETE query based on the working logic
        query = f"""
        DELETE FROM {database}.{table}
        WHERE UPPER(job_title) NOT LIKE UPPER('%{expected_role_without_developer}%')
          AND UPPER(job_title) NOT LIKE UPPER('%{expected_role}%')
        """
        try:
            cursor.execute(query)
            deleted_rows = cursor.rowcount
            conn.commit()
            logger.info(f"Deleted {deleted_rows} mismatched rows from {database}.{table}")
        except mysql.connector.Error as e:
            logger.error(f"Error cleaning table {table} in {database}: {e}")
            conn.rollback()

    conn.close()

def main():
    """Clean mismatched jobs in both databases."""
    databases = [Config.MYSQL["fresher_db"], Config.MYSQL["experienced_db"]]
    for db in databases:
        logger.info(f"Cleaning mismatched jobs in database: {db}")
        clean_mismatched_jobs(db)

if __name__ == "__main__":
    main()