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
    revenue = float(request.form["revenue"])
    profit = float(request.form["profit"])

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
# 启动程序（必须放最后）
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)