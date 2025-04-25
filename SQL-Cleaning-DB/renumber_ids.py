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
        logging.FileHandler('id_renumbering.log'),
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

def validate_table_structure(cursor, table: str) -> bool:
    """Validate that the jobs table has an id column."""
    try:
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'jobs_db' 
            AND TABLE_NAME = '{table}' 
            AND COLUMN_NAME = 'id';
        """)
        return cursor.fetchone()[0] > 0
    except mysql.connector.Error as e:
        logger.error(f"Error validating table structure for jobs_db.{table}: {e}")
        return False

def renumber_ids(batch_size: int = 1000) -> None:
    """Renumber the id column sequentially for the jobs table in jobs_db."""
    conn = connect_db()
    if not conn:
        logger.error("Could not connect to database jobs_db")
        return

    cursor = conn.cursor()
    table = "jobs"
    
    # Validate table structure
    if not validate_table_structure(cursor, table):
        logger.error(f"Table jobs_db.{table} does not have a valid id column")
        cursor.close()
        conn.close()
        return

    logger.info(f"Processing table jobs_db.{table}")
    try:
        # Get total number of rows
        cursor.execute(f"SELECT COUNT(*) FROM jobs_db.{table}")
        total_rows = cursor.fetchone()[0]
        logger.info(f"Table {table} has {total_rows} rows")

        # Process in batches
        offset = 0
        while offset < total_rows:
            try:
                # Create temporary table for batch
                cursor.execute(f"""
                    CREATE TEMPORARY TABLE temp_ids AS
                    SELECT id, ROW_NUMBER() OVER (ORDER BY id) + {offset} AS new_id
                    FROM jobs_db.{table}
                    ORDER BY id
                    LIMIT {batch_size} OFFSET {offset};
                """)

                # Update batch
                cursor.execute(f"""
                    UPDATE jobs_db.{table} f
                    JOIN temp_ids t ON f.id = t.id
                    SET f.id = t.new_id;
                """)
                updated_rows = cursor.rowcount

                # Drop temporary table
                cursor.execute("DROP TEMPORARY TABLE temp_ids;")

                logger.info(f"Updated {updated_rows} rows in jobs_db.{table} (batch {offset//batch_size + 1})")
                offset += batch_size
                conn.commit()

            except mysql.connector.Error as e:
                logger.error(f"Error processing batch in jobs_db.{table}: {e}")
                conn.rollback()
                break

        # Reset auto-increment counter
        cursor.execute(f"SELECT MAX(id) FROM jobs_db.{table};")
        max_id = cursor.fetchone()[0] or 0
        cursor.execute(f"ALTER TABLE jobs_db.{table} AUTO_INCREMENT = {max_id + 1};")
        logger.info(f"Set auto-increment to {max_id + 1} for jobs_db.{table}")

        conn.commit()
    except mysql.connector.Error as e:
        logger.error(f"Error renumbering IDs in jobs_db.{table}: {e}")
        conn.rollback()
    except Exception as e:
        logger.error(f"Unexpected error in jobs_db.{table}: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    """Renumber IDs in the jobs table of jobs_db."""
    logger.info("Starting ID renumbering for database: jobs_db")
    renumber_ids(batch_size=1000)
    logger.info("Finished processing database: jobs_db")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        sys.exit(1)