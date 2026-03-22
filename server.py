from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import jwt
import datetime
from db_utils import get_db_connection, init_db
import ml_analysis
import pandas as pd
import os

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = 'your_secret_key_here' # In a real app, use an env variable

# Initialize DB on start
init_db()

# --- Auth Middleware ---
def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            # Token: "Bearer <token>"
            token = token.split(' ')[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user_id, *args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# --- Auth Routes ---
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'message': 'Missing data'}), 400
    
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                     (data['name'], data['email'], hashed_pw))
        conn.commit()
    except Exception as e:
        return jsonify({'message': 'Email already exists!'}), 400
    finally:
        conn.close()
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing data'}), 400
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (data['email'],)).fetchone()
    conn.close()
    
    if user and bcrypt.check_password_hash(user['password'], data['password']):
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({'token': token, 'name': user['name']}), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

# --- Income Routes ---
@app.route('/api/income', methods=['GET', 'POST'])
@token_required
def income_handle(user_id):
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        conn.execute('INSERT INTO income (user_id, amount, source, date) VALUES (?, ?, ?, ?)',
                     (user_id, data['amount'], data['source'], data['date']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Income added'}), 201
    
    rows = conn.execute('SELECT * FROM income WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

# --- Expense Routes ---
@app.route('/api/expenses', methods=['GET', 'POST'])
@token_required
def expense_handle(user_id):
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        conn.execute('INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)',
                     (user_id, data['amount'], data['category'], data['date']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Expense added'}), 201
    
    rows = conn.execute('SELECT * FROM expenses WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

# --- Budget Routes ---
@app.route('/api/budgets', methods=['GET', 'POST'])
@token_required
def budget_handle(user_id):
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        conn.execute('INSERT INTO category_budgets (user_id, category, budget, month) VALUES (?, ?, ?, ?)',
                     (user_id, data['category'], data['budget'], data['month']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Budget set'}), 201
    
    rows = conn.execute('SELECT * FROM category_budgets WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

# --- Summary & ML Analysis ---
@app.route('/api/summary', methods=['GET'])
@token_required
def summary(user_id):
    conn = get_db_connection()
    income = conn.execute('SELECT SUM(amount) as total FROM income WHERE user_id = ?', (user_id,)).fetchone()
    expenses = conn.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = ?', (user_id,)).fetchone()
    
    # Category breakup
    category_data = conn.execute('SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category', (user_id,)).fetchall()
    
    conn.close()
    return jsonify({
        'total_income': income['total'] or 0,
        'total_expenses': expenses['total'] or 0,
        'categories': [dict(row) for row in category_data]
    })

@app.route('/api/ml-analysis', methods=['GET'])
@token_required
def run_ml(user_id):
    conn = get_db_connection()
    income_rows = conn.execute('SELECT strftime("%Y-%m", date) as Month, SUM(amount) as Income FROM income WHERE user_id = ? GROUP BY Month', (user_id,)).fetchall()
    expense_rows = conn.execute('SELECT strftime("%Y-%m", date) as Month, SUM(amount) as Expenses FROM expenses WHERE user_id = ? GROUP BY Month', (user_id,)).fetchall()
    conn.close()
    
    df_income = pd.DataFrame(income_rows)
    df_expense = pd.DataFrame(expense_rows)
    
    if df_income.empty and df_expense.empty:
        return jsonify({'message': 'Not enough data for ML analysis'}), 400
    
    # Merge dataframes
    df_final = pd.merge(df_income, df_expense, on="Month", how="outer").fillna(0).sort_values("Month")
    
    # Note: I'll need to modify ml_analysis.run_analysis to return results instead of just Streamlit components.
    # For now, let's just return the raw data and let the frontend handle basic charting.
    # Real ML analysis would return predicted values.
    
    return jsonify(df_final.to_dict(orient='records'))

# --- Serve Static Files ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
