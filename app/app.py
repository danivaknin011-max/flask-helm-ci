from flask import Flask, request, jsonify, Response, render_template, session, redirect, url_for
import os
import pymysql
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_bank_key' # הכרחי לשימוש ב-session

# --- הגדרות Prometheus (נשאר ללא שינוי) ---
HTTP_REQUESTS_TOTAL = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'http_status'])
HTTP_REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['endpoint'])
BANK_BALANCE_GAUGE = Gauge('bank_total_balance_amount', 'Current balance of account')

@app.before_request
def start_timer():
    request._start_time = time.time()

@app.after_request
def log_metrics(response):
    if request.path != '/metrics' and hasattr(request, '_start_time'):
        latency = time.time() - request._start_time
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=request.path,
            http_status=response.status_code
        ).inc()
        HTTP_REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
    return response

# --- פונקציות ה-DB ---
def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'mysql'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    time.sleep(3)
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # טבלת משתמשים
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    first_name VARCHAR(50),
                    last_name VARCHAR(50),
                    tz VARCHAR(9) UNIQUE,
                    password VARCHAR(255)
                )
            """)
            # טבלת חשבונות (מקושרת ל-user_id)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    user_id INT PRIMARY KEY,
                    balance DECIMAL(10,2) DEFAULT 0.00,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
        conn.commit()
    finally:
        conn.close()

# --- Routes ---

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('index.html', user=session['first_name'])
    return render_template('welcome.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_pw = generate_password_hash(data['password'])
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO users (first_name, last_name, tz, password) VALUES (%s, %s, %s, %s)",
                           (data['first_name'], data['last_name'], data['tz'], hashed_pw))
            user_id = cursor.lastrowid
            cursor.execute("INSERT INTO accounts (user_id, balance) VALUES (%s, 0.00)", (user_id,))
        conn.commit()
        return jsonify({"message": "Registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": "User with this ID already exists"}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE tz = %s", (data['tz'],))
            user = cursor.fetchone()
            if user and check_password_hash(user['password'], data['password']):
                session['user_id'] = user['id']
                session['first_name'] = user['first_name']
                return jsonify({"message": "Logged in"}), 200
        return jsonify({"error": "Invalid credentials"}), 401
    finally:
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/balance', methods=['GET'])
def get_balance():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT balance FROM accounts WHERE user_id = %s", (session['user_id'],))
            result = cursor.fetchone()
            balance_val = float(result['balance']) if result else 0
            BANK_BALANCE_GAUGE.set(balance_val)
            return jsonify({"balance": balance_val}), 200
    finally:
        conn.close()

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    amount = request.get_json().get('amount', 0)
    if amount <= 0: return jsonify({"error": "Amount must be positive"}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE accounts SET balance = balance + %s WHERE user_id = %s", (amount, session['user_id']))
            conn.commit()
            cursor.execute("SELECT balance FROM accounts WHERE user_id = %s", (session['user_id'],))
            new_balance = float(cursor.fetchone()['balance'])
            BANK_BALANCE_GAUGE.set(new_balance)
        return jsonify({"message": "Deposit successful"}), 200
    finally:
        conn.close()

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    amount = request.get_json().get('amount', 0)
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT balance FROM accounts WHERE user_id = %s", (session['user_id'],))
            current_balance = float(cursor.fetchone()['balance'])
            if amount > current_balance: return jsonify({"error": "Insufficient funds"}), 400
            cursor.execute("UPDATE accounts SET balance = balance - %s WHERE user_id = %s", (amount, session['user_id']))
            conn.commit()
            cursor.execute("SELECT balance FROM accounts WHERE user_id = %s", (session['user_id'],))
            new_balance = float(cursor.fetchone()['balance'])
            BANK_BALANCE_GAUGE.set(new_balance)
        return jsonify({"message": "Withdrawal successful"}), 200
    finally:
        conn.close()

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)