# app.py
import streamlit as st
import sqlite3
import pandas as pd
import os
import io
from datetime import datetime
import matplotlib.pyplot as plt
import ml_analysis   # Import ML analysis module

# ----------------- Database -----------------
db_path = "finance_manager.db"

try:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    c = conn.cursor()
    c.execute("PRAGMA integrity_check;")
    result = c.fetchone()
    if result[0] != "ok":
        conn.close()
        os.remove(db_path)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        c = conn.cursor()
except sqlite3.DatabaseError:
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    c = conn.cursor()

# Create tables
c.execute('''
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    source TEXT NOT NULL,
    date TEXT NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    date TEXT NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS category_budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    budget REAL NOT NULL,
    month TEXT NOT NULL
)
''')

conn.commit()

# ----------------- Streamlit App -----------------
st.title("💰 Multi-Month Smart Finance Manager")

# -------- CSV Upload --------
st.sidebar.header("📂 Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV file (Income + Expenses)", type=["csv"])

if uploaded_file is not None:
    try:
        df_upload = pd.read_csv(uploaded_file)
        df_upload.columns = df_upload.columns.str.strip().str.lower()
        required_cols = {'type', 'amount', 'category', 'date'}
        if not required_cols.issubset(df_upload.columns):
            st.sidebar.error("CSV must contain: [type, amount, category, date]. Type = income/expense.")
        else:
            for _, row in df_upload.iterrows():
                row_type = str(row['type']).strip().lower()
                amount = float(row['amount'])
                category = str(row['category']).strip()
                date = str(row['date']).strip()
                if row_type == "income":
                    c.execute("INSERT INTO income (amount, source, date) VALUES (?, ?, ?)", (amount, category, date))
                elif row_type == "expense":
                    c.execute("INSERT INTO expenses (amount, category, date) VALUES (?, ?, ?)", (amount, category, date))
            conn.commit()
            st.sidebar.success("CSV data uploaded successfully!")
    except Exception as e:
        st.sidebar.error(f"Error reading CSV: {e}")

# -------- Income Section --------
with st.expander("➕ Add Income"):
    with st.form("income_form", clear_on_submit=True):
        income_amount = st.number_input("Amount", min_value=0.0, step=0.01, key="income_amt")
        income_source = st.text_input("Source (Salary, Bonus, etc.)", key="income_src")
        income_date = st.date_input("Date", value=datetime.today(), key="income_date")
        submitted_income = st.form_submit_button("Add Income")
        if submitted_income and income_amount > 0 and income_source.strip() != "":
            c.execute("INSERT INTO income (amount, source, date) VALUES (?, ?, ?)",
                      (income_amount, income_source, income_date.strftime("%Y-%m-%d")))
            conn.commit()
            st.success("Income added successfully!")
            st.rerun()

# -------- Expense Section --------
with st.expander("➖ Add Expense"):
    with st.form("expense_form", clear_on_submit=True):
        expense_amount = st.number_input("Amount", min_value=0.0, step=0.01, key="exp_amt")
        expense_category = st.text_input("Category (Food, Rent, Travel, etc.)", key="exp_cat")
        expense_date = st.date_input("Date", value=datetime.today(), key="exp_date")
        submitted_expense = st.form_submit_button("Add Expense")
        if submitted_expense and expense_amount > 0 and expense_category.strip() != "":
            c.execute("INSERT INTO expenses (amount, category, date) VALUES (?, ?, ?)",
                      (expense_amount, expense_category, expense_date.strftime("%Y-%m-%d")))
            conn.commit()
            st.success("Expense added successfully!")
            st.rerun()

# -------- Multi-Month Summary --------
st.header("📊 Multi-Month Summary")

# Fetch months
c.execute("SELECT DISTINCT strftime('%Y-%m', date) FROM income")
income_months = [row[0] for row in c.fetchall()]
c.execute("SELECT DISTINCT strftime('%Y-%m', date) FROM expenses")
expense_months = [row[0] for row in c.fetchall()]
all_months = sorted(list(set(income_months + expense_months)))

if all_months:
    selected_month = st.selectbox("Select Month", all_months)

    # -------- Clear Data --------
    if st.button(f"🗑 Clear Data for {selected_month}"):
        c.execute("DELETE FROM income WHERE strftime('%Y-%m', date) = ?", (selected_month,))
        c.execute("DELETE FROM expenses WHERE strftime('%Y-%m', date) = ?", (selected_month,))
        conn.commit()
        st.success(f"Data for {selected_month} cleared!")
        st.rerun()

    # -------- Monthly Summary --------
    c.execute("SELECT SUM(amount) FROM income WHERE strftime('%Y-%m', date) = ?", (selected_month,))
    total_income = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM expenses WHERE strftime('%Y-%m', date) = ?", (selected_month,))
    total_expense = c.fetchone()[0] or 0
    remaining = total_income - total_expense

    st.markdown(f"**Month: {selected_month}**")
    st.markdown(f"**Total Income:** ₹{total_income:.2f}")
    st.markdown(f"**Total Expenses:** ₹{total_expense:.2f}")
    st.markdown(f"**Remaining Balance:** ₹{remaining:.2f}")

    # -------- Income Table --------
    st.subheader("📒 Income Details")
    c.execute("SELECT id, amount, source, date FROM income WHERE strftime('%Y-%m', date) = ?", (selected_month,))
    income_rows = c.fetchall()
    if income_rows:
        df_income = pd.DataFrame(income_rows, columns=['ID', 'Amount', 'Source', 'Date'])
        st.dataframe(df_income, use_container_width=True)
        st.download_button("📥 Download Income Data", df_income.to_csv(index=False).encode("utf-8"),
                           file_name=f"income_{selected_month}.csv", mime="text/csv")
    else:
        st.write("No income recorded for this month.")

    # -------- Expense Table --------
    st.subheader("📒 Expense Details")
    c.execute("SELECT id, amount, category, date FROM expenses WHERE strftime('%Y-%m', date) = ?", (selected_month,))
    expense_rows = c.fetchall()
    if expense_rows:
        df_expense = pd.DataFrame(expense_rows, columns=['ID', 'Amount', 'Category', 'Date'])
        st.dataframe(df_expense, use_container_width=True)
        st.download_button("📥 Download Expense Data", df_expense.to_csv(index=False).encode("utf-8"),
                           file_name=f"expenses_{selected_month}.csv", mime="text/csv")
    else:
        st.write("No expenses recorded for this month.")

    # -------- Budget & Alerts --------
    st.subheader("⚠️ Budget & Alerts")
    with st.form("budget_form", clear_on_submit=True):
        budget_category = st.text_input("Enter category")
        budget_amount = st.number_input("Enter budget (₹)", min_value=100.0, step=100.0)
        budget_submit = st.form_submit_button("Set Budget")
        if budget_submit and budget_category.strip() != "":
            c.execute("INSERT INTO category_budgets (category, budget, month) VALUES (?, ?, ?)",
                      (budget_category.strip(), budget_amount, selected_month))
            conn.commit()
            st.success(f"Budget set for {budget_category} in {selected_month}")
            st.rerun()

    c.execute("SELECT category, budget FROM category_budgets WHERE month = ?", (selected_month,))
    budgets = c.fetchall()
    if budgets:
        rows = []
        for category, planned in budgets:
            c.execute("SELECT SUM(amount) FROM expenses WHERE strftime('%Y-%m', date) = ? AND category = ?",
                      (selected_month, category))
            spent = c.fetchone()[0] or 0
            remain = planned - spent
            status = "✅ Within Budget" if remain >= 0 else "🚨 Over Budget"
            rows.append([category, planned, spent, remain, status])
        df_budget = pd.DataFrame(rows, columns=["Category", "Planned", "Spent", "Remaining", "Status"])
        st.dataframe(df_budget, use_container_width=True)
        st.download_button("📥 Download Budget Report", df_budget.to_csv(index=False).encode("utf-8"),
                           file_name=f"budget_{selected_month}.csv", mime="text/csv")

    # -------- Expense Distribution (Bar) --------
    st.subheader("📊 Expense Distribution by Category")
    c.execute("SELECT category, SUM(amount) FROM expenses WHERE strftime('%Y-%m', date) = ? GROUP BY category",
              (selected_month,))
    dist_data = c.fetchall()
    if dist_data:
        df_dist = pd.DataFrame(dist_data, columns=["Category", "Amount"])
        fig1, ax1 = plt.subplots()
        df_dist.plot(kind="bar", x="Category", y="Amount", ax=ax1, legend=False)
        ax1.set_title("Expense Distribution")
        ax1.set_ylabel("Amount (₹)")
        ax1.set_xlabel("Category")
        plt.xticks(rotation=0)
        st.pyplot(fig1)
        buf1 = io.BytesIO()
        fig1.savefig(buf1, format="png")
        st.download_button("📥 Download Expense Distribution Chart", buf1.getvalue(),
                           file_name=f"expense_distribution_{selected_month}.png", mime="image/png")

    # -------- Income vs Expense Trend --------
    st.subheader("📈 Income vs Expenses Trend Over Months")
    c.execute("SELECT strftime('%Y-%m', date), SUM(amount) FROM income GROUP BY strftime('%Y-%m', date)")
    income_trend = c.fetchall()
    c.execute("SELECT strftime('%Y-%m', date), SUM(amount) FROM expenses GROUP BY strftime('%Y-%m', date)")
    expense_trend = c.fetchall()

    if income_trend or expense_trend:
        df_income_trend = pd.DataFrame(income_trend, columns=["Month", "Income"])
        df_expense_trend = pd.DataFrame(expense_trend, columns=["Month", "Expenses"])
        df_trend = pd.merge(df_income_trend, df_expense_trend, on="Month", how="outer").fillna(0).sort_values("Month")

        fig2, ax2 = plt.subplots()
        ax2.plot(df_trend["Month"], df_trend["Income"], marker="o", label="Income")
        ax2.plot(df_trend["Month"], df_trend["Expenses"], marker="o", label="Expenses")
        ax2.set_title("Income vs Expenses Trend")
        ax2.set_ylabel("Amount (₹)")
        ax2.set_xlabel("Month")
        ax2.legend()
        plt.xticks(rotation=45)
        st.pyplot(fig2)
        buf2 = io.BytesIO()
        fig2.savefig(buf2, format="png")
        st.download_button("📥 Download Income vs Expenses Chart", buf2.getvalue(),
                           file_name="income_vs_expenses_trend.png", mime="image/png")

    # -------- Historical Distribution --------
    st.subheader("📊 Historical Expense Distribution by Category")
    c.execute("SELECT strftime('%Y-%m', date), category, SUM(amount) FROM expenses GROUP BY strftime('%Y-%m', date), category")
    exp_hist = c.fetchall()
    if exp_hist:
        df_hist = pd.DataFrame(exp_hist, columns=["Month", "Category", "Spent"])
        df_pivot = df_hist.pivot(index="Month", columns="Category", values="Spent").fillna(0)
        fig3, ax3 = plt.subplots()
        df_pivot.plot(kind="bar", stacked=True, ax=ax3)
        ax3.set_title("Historical Expense Distribution")
        ax3.set_ylabel("Amount (₹)")
        plt.xticks(rotation=45)
        st.pyplot(fig3)
        buf3 = io.BytesIO()
        fig3.savefig(buf3, format="png")
        st.download_button("📥 Download Historical Expense Chart", buf3.getvalue(),
                           file_name="historical_expense_distribution.png", mime="image/png")

    # -------- Run ML Analysis --------
    st.markdown("---")
    if st.button("🤖 Run ML Analysis"):
        c.execute("SELECT strftime('%Y-%m', date), SUM(amount) FROM income GROUP BY strftime('%Y-%m', date)")
        income_data = c.fetchall()
        df_income_final = pd.DataFrame(income_data, columns=["Month", "Income"])
        c.execute("SELECT strftime('%Y-%m', date), SUM(amount) FROM expenses GROUP BY strftime('%Y-%m', date)")
        expense_data = c.fetchall()
        df_expense_final = pd.DataFrame(expense_data, columns=["Month", "Expenses"])
        df_final = pd.merge(df_income_final, df_expense_final, on="Month", how="outer").fillna(0).sort_values("Month")
        ml_analysis.run_analysis(df_final)

else:
    st.write("No income or expenses recorded yet.")