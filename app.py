from flask import Flask, request, redirect, session, render_template_string, g
from db import get_conn, close_conn
from ai import generate_title
import hashlib

app = Flask(__name__)
app.secret_key = "pdd_secret"
app.teardown_appcontext(close_conn)

# =========================
# 登录页面
# =========================
login_html = """
<h2>登录系统</h2>
<form method="post">
用户名:<input name="username"><br>
密码:<input name="password" type="password"><br>
<button type="submit">登录</button>
</form>
"""

# =========================
# 首页页面
# =========================
home_html = """
<h2>AI电商后台</h2>

<p>当前用户：{{user}}</p>

<a href="/dashboard">📊 数据分析</a><br><br>

<form method="post" action="/add">
商品：<input name="name"><br>
销售额：<input name="revenue"><br>
利润：<input name="profit"><br>
<button>添加</button>
</form>

<form method="post" action="/ai">
商品名：<input name="name">
<button>AI生成标题</button>
</form>

<h3>AI结果</h3>
<pre>{{ai}}</pre>

<h3>数据</h3>
<table border="1">
<tr><th>ID</th><th>商品</th><th>销售额</th><th>利润</th></tr>
{% for r in data %}
<tr>
<td>{{r[0]}}</td>
<td>{{r[2]}}</td>
<td>{{r[3]}}</td>
<td>{{r[4]}}</td>
</tr>
{% endfor %}
</table>
"""

# =========================
# 登录
# =========================
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password_hash=?",
            (username, password_hash)
        )

        user = cursor.fetchone()

        if user:
            session["user"] = username
            return redirect("/home")

    return login_html


# =========================
# 首页
# =========================
@app.route("/home")
def home():

    user = session.get("user")

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE username=?",
        (user,)
    )

    data = cursor.fetchall()

    return render_template_string(
        home_html,
        user=user,
        data=data,
        ai=""
    )


# =========================
# 添加商品
# =========================
@app.route("/add", methods=["POST"])
def add():

    user = session.get("user")

    name = request.form["name"]
    revenue_str = request.form["revenue"].strip()
    profit_str = request.form["profit"].strip()

    if not name or not revenue_str or not profit_str:
        return "请填写所有字段 <a href='/home'>返回</a>"

    revenue = float(revenue_str)
    profit = float(profit_str)

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO products (username, name, revenue, profit)
    VALUES (?, ?, ?, ?)
    """, (user, name, revenue, profit))

    conn.commit()

    return redirect("/home")


# =========================
# AI生成标题
# =========================
@app.route("/ai", methods=["POST"])
def ai():

    name = request.form["name"]

    result = generate_title(name)

    return f"<pre>{result}</pre>"


# =========================
# 数据仪表盘
# =========================
@app.route("/dashboard")
def dashboard():

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT revenue, profit FROM products")
    data = cursor.fetchall()

    total_revenue = sum([d[0] for d in data]) if data else 0
    total_profit = sum([d[1] for d in data]) if data else 0
    count = len(data)
    avg_profit = total_profit / count if count else 0

    return f"""
    <h1>📊 数据仪表盘</h1>

    <p>商品数量：{count}</p>
    <p>总销售额：{total_revenue:.2f}</p>
    <p>总利润：{total_profit:.2f}</p>
    <p>平均利润：{avg_profit:.2f}</p>

    <br>
    <a href="/home">返回首页</a>
    """


# =========================
# 初始化数据库（模块级别，gunicorn worker 共享）
# =========================
def init_db_once():
    from db import get_conn
    import hashlib

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password_hash TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        name TEXT,
        revenue REAL,
        profit REAL
    )
    """)

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


# =========================
# 启动程序（必须放最后）
# =========================
if __name__ == "__main__":
    # 本地开发模式
    init_db_once()
    app.run(host="0.0.0.0", port=5000)
else:
    # Render 部署模式
    import atexit
    _initialized = False
    def _lazy_init():
        global _initialized
        if not _initialized:
            _initialized = True
            init_db_once()
    atexit.register(_lazy_init)
    # 每个请求前检查并初始化
    @app.before_request
    def before_request():
        global _initialized
        if not _initialized:
            _initialized = True
            init_db_once()