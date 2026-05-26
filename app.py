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
<h2>代发货管理系统</h2>

<p>当前用户：{{user}}</p>

<a href="/dashboard">📊 数据分析</a> | <a href="/reset-db">🔄 重置数据库</a><br><br>

<form method="post" action="/add">
代发商品名称：<input name="supplier_product_name"><br>
代发价：<input name="dropshipping_price"><br>
售价：<input name="selling_price"><br>
商品链接：<input name="product_link"><br>
SKU/规格：<input name="sku"><br>
发货信息：<input name="shipping_info"><br>
<button>添加</button>
</form>

<h3>代发货商品列表</h3>
<table border="1">
<tr><th>ID</th><th>商品名称</th><th>代发价</th><th>售价</th><th>利润</th><th>商品链接</th><th>SKU/规格</th><th>发货信息</th><th>操作</th></tr>
{% for r in data %}
<tr>
<td>{{r[0]}}</td>
<td>{{r[2]}}</td>
<td>{{r[3]}}</td>
<td>{{r[4]}}</td>
<td>{{r[4] - r[3]}}</td>
<td><a href="{{r[5]}}" target="_blank">链接</a></td>
<td>{{r[6]}}</td>
<td>{{r[7]}}</td>
<td><a href="/delete/{{r[0]}}">删除</a></td>
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

    supplier_product_name = request.form["supplier_product_name"].strip()
    dropshipping_price_str = request.form["dropshipping_price"].strip()
    selling_price_str = request.form["selling_price"].strip()
    product_link = request.form["product_link"].strip()
    sku = request.form["sku"].strip()
    shipping_info = request.form["shipping_info"].strip()

    if not supplier_product_name or not dropshipping_price_str or not selling_price_str:
        return "请填写所有字段 <a href='/home'>返回</a>"

    dropshipping_price = float(dropshipping_price_str)
    selling_price = float(selling_price_str)

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO products (username, supplier_product_name, dropshipping_price, selling_price, product_link, sku, shipping_info)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user, supplier_product_name, dropshipping_price, selling_price, product_link, sku, shipping_info))

    conn.commit()

    return redirect("/home")


# =========================
# 重置数据库
# =========================
@app.route("/reset-db")
def reset_db():
    user = session.get("user")
    if not user:
        return redirect("/")

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        supplier_product_name TEXT,
        dropshipping_price REAL,
        selling_price REAL,
        product_link TEXT,
        sku TEXT,
        shipping_info TEXT
    )
    """)
    conn.commit()
    return redirect("/home")


# =========================
# 删除商品
# =========================
@app.route("/delete/<int:product_id>")
def delete(product_id):

    user = session.get("user")

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE id=? AND username=?", (product_id, user))
    conn.commit()

    return redirect("/home")


# =========================
# 数据仪表盘
# =========================
@app.route("/dashboard")
def dashboard():

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT dropshipping_price, selling_price FROM products")
    data = cursor.fetchall()

    total_dropshipping = sum([d[0] for d in data]) if data else 0
    total_selling = sum([d[1] for d in data]) if data else 0
    total_profit = total_selling - total_dropshipping
    count = len(data)
    avg_profit = total_profit / count if count else 0

    return f"""
    <h1>📊 数据仪表盘</h1>

    <p>商品数量：{count}</p>
    <p>总代发成本：{total_dropshipping:.2f}</p>
    <p>总销售额：{total_selling:.2f}</p>
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
    DROP TABLE IF EXISTS products
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        supplier_product_name TEXT,
        dropshipping_price REAL,
        selling_price REAL,
        product_link TEXT,
        sku TEXT,
        shipping_info TEXT
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
    with app.app_context():
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
