from db import get_conn

conn = get_conn()
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
print(cursor.fetchall())