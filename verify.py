# import sqlite3
# conn = sqlite3.connect('jobs.db')
# cursor = conn.cursor()
# cursor.execute("SELECT job_title,source FROM jobs LIMIT 50")
# for row in cursor.fetchall():
#     print(row)
# conn.close()


import sqlite3
conn = sqlite3.connect('jobs.db')
cursor = conn.cursor()
cursor.execute("SELECT source, COUNT(*) FROM jobs GROUP BY source")

#TRUNCATE TABLE jobs;
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]} jobs")
conn.close()