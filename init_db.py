import sqlite3
import hashlib

# 创建数据库
conn = sqlite3.connect("saas.db")
cursor = conn.cursor()

# =====================
# 用户表
# =====================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password_hash TEXT
)
""")

# =====================
# 商品表
# =====================
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    name TEXT,
    revenue REAL,
    profit REAL
)
""")

# =====================
# 插入默认用户（如果没有）
# =====================
default_password = "123456"
password_hash = hashlib.sha256(default_password.encode()).hexdigest()

cursor.execute("SELECT * FROM users WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("""
    INSERT INTO users (username, password_hash)
    VALUES (?, ?)
    """, ('admin', password_hash))

conn.commit()
conn.close()

print("Database initialized. Default account: admin/123456")