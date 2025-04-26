import mysql.connector
from mysql.connector import Error

class Config:
    MYSQL = {
        "host": "localhost",
        "user": "shyam",
        "password": "shyam",
        "database": "jobs_db"
    }

def update_experience_levels():
    try:
        # Connect to the database using Config
        connection = mysql.connector.connect(
            host=Config.MYSQL["host"],
            user=Config.MYSQL["user"],
            password=Config.MYSQL["password"],
            database=Config.MYSQL["database"]
        )

        if connection.is_connected():
            cursor = connection.cursor()

            update_query = """
            UPDATE jobs
            SET experience_level = CASE 
                WHEN source = 'LinkedIn' AND experience_level = 'Internship' THEN '0-0 Yrs'
                WHEN source = 'LinkedIn' AND experience_level = 'Entry level' THEN '0-2 Yrs'
                WHEN source = 'LinkedIn' AND experience_level = 'Associate' THEN '2-5 Yrs'
                WHEN source = 'LinkedIn' AND experience_level = 'Mid-Senior level' THEN '5-8 Yrs'
                WHEN source = 'LinkedIn' AND experience_level = 'Director' THEN '8-12 Yrs'
                WHEN source = 'LinkedIn' AND experience_level = 'Executive (VP, C-Level)' THEN '12-20 Yrs'
                WHEN source = 'LinkedIn' AND experience_level = 'Not Applicable' THEN '0-10 Yrs'
                ELSE experience_level  -- Keep existing values for non-LinkedIn sources
            END
            WHERE source = 'LinkedIn';
            """

            cursor.execute(update_query)
            connection.commit()

            print("✅ Successfully updated experience levels for LinkedIn jobs!")

    except Error as e:
        print(f"❌ Error while connecting to database: {e}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("✅ MySQL connection closed.")

if __name__ == "__main__":
    update_experience_levels()
