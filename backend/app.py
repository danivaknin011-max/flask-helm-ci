from flask import Flask, request, jsonify, Response
from flask_cors import CORS

import os
import pymysql
import time

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST


app = Flask(__name__)
CORS(app)


# --- הגדרות Prometheus ---

HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total', 'Total HTTP Requests',
    ['method', 'endpoint', 'http_status']
)

HTTP_REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 'HTTP request latency',
    ['endpoint']
)

BANK_BALANCE_GAUGE = Gauge(
    'bank_total_balance_amount',
    'Current balance of account 1'
)


@app.before_request
def start_timer():
    request._start_time = time.time()


@app.after_request
def log_metrics(response):
    if request.path != '/metrics':
        latency = time.time() - request._start_time

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=request.path,
            http_status=response.status_code
        ).inc()

        HTTP_REQUEST_LATENCY.labels(
            endpoint=request.path
        ).observe(latency)

    return response


# --- DB Functions ---

def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'mysql'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor
    )


def init_db():
    time.sleep(5)

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INT PRIMARY KEY,
                    balance DECIMAL(10,2)
                )
            """)

            cursor.execute("SELECT COUNT(*) as count FROM accounts")

            if cursor.fetchone()['count'] == 0:
                cursor.execute(
                    "INSERT INTO accounts (id, balance) VALUES (1, 0.00)"
                )

        conn.commit()

    finally:
        conn.close()


# --- Routes ---


@app.route('/balance', methods=['GET'])
def get_balance():

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("SELECT balance FROM accounts WHERE id = 1")

            result = cursor.fetchone()

            balance_val = float(result['balance']) if result else 0

            BANK_BALANCE_GAUGE.set(balance_val)

            return jsonify({"balance": balance_val}), 200

    finally:
        conn.close()


@app.route('/deposit', methods=['POST'])
def deposit():

    amount = request.get_json().get('amount', 0)

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute(
                "UPDATE accounts SET balance = balance + %s WHERE id = 1",
                (amount,)
            )

            conn.commit()

            cursor.execute("SELECT balance FROM accounts WHERE id = 1")

            new_balance = float(cursor.fetchone()['balance'])

            BANK_BALANCE_GAUGE.set(new_balance)

        return jsonify({"message": "Deposit successful"}), 200

    finally:
        conn.close()


@app.route('/withdraw', methods=['POST'])
def withdraw():

    amount = request.get_json().get('amount', 0)

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("SELECT balance FROM accounts WHERE id = 1")

            current_balance = float(cursor.fetchone()['balance'])

            if amount > current_balance:
                return jsonify({"error": "Insufficient funds"}), 400

            cursor.execute(
                "UPDATE accounts SET balance = balance - %s WHERE id = 1",
                (amount,)
            )

            conn.commit()

            cursor.execute("SELECT balance FROM accounts WHERE id = 1")

            new_balance = float(cursor.fetchone()['balance'])

            BANK_BALANCE_GAUGE.set(new_balance)

        return jsonify({"message": "Withdrawal successful"}), 200

    finally:
        conn.close()


@app.route('/metrics')
def metrics():
    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )


if __name__ == '__main__':

    init_db()

    BANK_BALANCE_GAUGE.set(0)

    app.run(
        host='0.0.0.0',
        port=5000
    )