# 💰 Smart Finance Manager

A modern, full-stack personal finance management web application built with **Flask** (Python) and vanilla **HTML/CSS/JavaScript**. Track your income, expenses, and budgets — with built-in ML-powered financial analysis.

---

## ✨ Features

- 🔐 **User Authentication** — Secure signup & login with JWT tokens and bcrypt password hashing
- 💵 **Income Tracking** — Log income entries with source and date
- 🧾 **Expense Tracking** — Log expenses by category and date
- 📊 **Budget Management** — Set monthly category-wise budgets
- 📈 **Dashboard** — Visual overview of income vs. expenses with category breakdowns (Chart.js)
- 🤖 **ML Analysis** — Machine learning-based financial trend analysis (scikit-learn)
- 💾 **SQLite Database** — Lightweight, file-based persistence (no external DB required)

---

## 🗂️ Project Structure

```
Smart-Finance-Manager/
├── server.py           # Flask backend — API routes & auth logic
├── db_utils.py         # Database connection & schema initialization
├── ml_analysis.py      # ML-based financial analysis module
├── migrate_db.py       # Database migration script
├── index.html          # Entry point / landing page
├── login.html          # Login page
├── signup.html         # Signup page
├── dashboard.html      # Main dashboard (charts, summaries)
├── style.css           # Global styles (glassmorphism, gradients)
├── script.js           # Frontend logic & API calls
├── requirements.txt    # Python dependencies
└── finance_manager.db  # SQLite database (auto-created)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/Hemalatha150/Smart-Finance-Manager.git
cd Smart-Finance-Manager
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python server.py
```

The app will be available at **http://127.0.0.1:5000**

---

## 🔌 API Endpoints

| Method | Endpoint           | Description                  | Auth Required |
|--------|--------------------|------------------------------|---------------|
| POST   | `/api/signup`      | Register a new user          | ❌            |
| POST   | `/api/login`       | Login and receive JWT token  | ❌            |
| GET    | `/api/income`      | Get all income records       | ✅            |
| POST   | `/api/income`      | Add a new income entry       | ✅            |
| GET    | `/api/expenses`    | Get all expense records      | ✅            |
| POST   | `/api/expenses`    | Add a new expense entry      | ✅            |
| GET    | `/api/budgets`     | Get all budget entries       | ✅            |
| POST   | `/api/budgets`     | Set a monthly category budget| ✅            |
| GET    | `/api/summary`     | Financial summary overview   | ✅            |
| GET    | `/api/ml-analysis` | ML-based trend analysis      | ✅            |

> All protected routes require an `Authorization: Bearer <token>` header.

---

## 🛠️ Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Backend    | Python, Flask, Flask-CORS, Flask-Bcrypt |
| Auth       | JWT (PyJWT)                       |
| ML         | scikit-learn, pandas, numpy       |
| Database   | SQLite                            |
| Frontend   | HTML5, CSS3, Vanilla JavaScript   |
| Charts     | Chart.js                          |

---

## 📦 Dependencies

```
flask
flask-cors
flask-bcrypt
PyJWT
pandas
numpy
scikit-learn
matplotlib
reportlab
streamlit
```

---

## 🔒 Security Notes

- Passwords are hashed using **bcrypt** before storage
- JWT tokens expire after **24 hours**
- In production, replace the `SECRET_KEY` in `server.py` with a secure environment variable:
  ```python
  app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
  ```

---

## 🙋‍♀️ Author

**Hemalatha** — [GitHub](https://github.com/Hemalatha150)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
