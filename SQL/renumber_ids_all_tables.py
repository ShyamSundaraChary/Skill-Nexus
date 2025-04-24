import sys
import os
import mysql.connector
import logging

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

def renumber_ids(database):
    """Renumber the id column sequentially for all tables in the database."""
    conn = connect_db(database)
    if not conn:
        logger.error(f"Could not connect to database {database}")
        return

    cursor = conn.cursor()
    tables = get_all_tables(database)
    logger.info(f"Found {len(tables)} tables in {database}: {tables}")

    for table in tables:
        logger.info(f"Renumbering IDs in {database}.{table}")
        try:
            # Step 1: Create a temporary table to store new IDs
            cursor.execute(f"""
                CREATE TEMPORARY TABLE temp_ids AS
                SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS new_id
                FROM {database}.{table};
            """)

            # Step 2: Update the original table with new IDs
            cursor.execute(f"""
                UPDATE {database}.{table} f
                JOIN temp_ids t ON f.id = t.id
                SET f.id = t.new_id;
            """)
            updated_rows = cursor.rowcount

            # Step 3: Drop the temporary table
            cursor.execute("DROP TEMPORARY TABLE temp_ids;")

            # Step 4: Reset the auto-increment counter
            cursor.execute(f"SELECT MAX(id) FROM {database}.{table};")
            max_id = cursor.fetchone()[0] or 0
            cursor.execute(f"ALTER TABLE {database}.{table} AUTO_INCREMENT = {max_id + 1};")

            conn.commit()
            logger.info(f"Renumbered {updated_rows} rows in {database}.{table}. New auto-increment starts at {max_id + 1}")
        except mysql.connector.Error as e:
            logger.error(f"Error renumbering IDs in {database}.{table}: {e}")
            conn.rollback()

    conn.close()

def main():
    """Renumber IDs in both databases."""
    databases = [Config.MYSQL["fresher_db"], Config.MYSQL["experienced_db"]]
    for db in databases:
        logger.info(f"Renumbering IDs in database: {db}")
        renumber_ids(db)

if __name__ == "__main__":
    main()