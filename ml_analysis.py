# ml_analysis.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from io import BytesIO
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Helper: convert matplotlib fig to PNG bytes
def fig_to_png_bytes(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()

# Helper: create PDF report
def generate_pdf_report(best, worst, loss_months, df):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "📊 Finance Insights Report")
    y -= 40

    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"🏆 Best Month: {best['Month']} (Savings: ₹{best['Savings']:.2f})")
    y -= 20
    c.drawString(50, y, f"📉 Worst Month: {worst['Month']} (Savings: ₹{worst['Savings']:.2f})")
    y -= 30

    if not loss_months.empty:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "⚠️ Overspending Months:")
        y -= 20
        c.setFont("Helvetica", 11)
        for _, row in loss_months.iterrows():
            c.drawString(60, y, f"{row['Month']} → Income: ₹{row['Income']}, Expenses: ₹{row['Expenses']}, Savings: ₹{row['Savings']}")
            y -= 15
            if y < 80:
                c.showPage()
                y = height - 50

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "📊 Savings Rate (%) & Expense Growth (%)")
    y -= 20
    c.setFont("Helvetica", 10)

    # Show at most 8 rows in PDF
    table_df = df[["Month", "Savings_Rate_%", "Expense_Growth_%"]].round(2).head(8)
    for _, row in table_df.iterrows():
        c.drawString(60, y, f"{row['Month']} → Savings Rate: {row['Savings_Rate_%']}%, Expense Growth: {row['Expense_Growth_%']}%")
        y -= 15
        if y < 80:
            c.showPage()
            y = height - 50

    c.showPage()
    c.save()
    buf.seek(0)
    return buf

# Normalize columns
def normalize_columns(df):
    d = df.copy()
    mapping = {}
    for c in d.columns:
        low = c.strip().lower()
        if low in ("month", "date", "dt"):
            mapping[c] = "Month"
        elif low in ("income", "amount_income", "in"):
            mapping[c] = "Income"
        elif low in ("expenses", "expense", "amount_expense", "out"):
            mapping[c] = "Expenses"
    return d.rename(columns=mapping)

def run_analysis(df_input):
    st.header("🤖 ML Analysis & Insights")

    if df_input is None or df_input.empty:
        st.warning("No data available for analysis.")
        return

    # Normalize & ensure required cols
    df = normalize_columns(df_input)
    if not {"Month", "Income", "Expenses"}.issubset(df.columns):
        st.error("Data must have Month, Income, Expenses.")
        return

    # Prepare
    df["Income"] = pd.to_numeric(df["Income"], errors="coerce").fillna(0)
    df["Expenses"] = pd.to_numeric(df["Expenses"], errors="coerce").fillna(0)
    df["Savings"] = df["Income"] - df["Expenses"]
    df["Month_Index"] = np.arange(len(df))
    month_labels = df["Month"].astype(str).tolist()

    # Historical Data
    st.subheader("📊 Historical Data")
    st.dataframe(df[["Month", "Income", "Expenses", "Savings"]], use_container_width=True)
    st.download_button(
        "⬇️ Download Historical Data (CSV)",
        df[["Month", "Income", "Expenses", "Savings"]].to_csv(index=False).encode(),
        "historical_data.csv",
        "text/csv",
    )

    # Train model
    if len(df) >= 2:
        X, y = df[["Month_Index"]], df["Expenses"]
        model = LinearRegression().fit(X, y)

        # Actual vs Predicted Expenses
        st.subheader("📉 Actual vs Predicted Expenses")
        next_pred = float(model.predict([[len(df)]])[0])
        st.write(f"Predicted Expenses for next month: **₹{next_pred:,.2f}**")

        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.plot(month_labels, df["Expenses"], marker="o", label="Actual Expenses")
        ax1.plot(month_labels + ["Next Month"],
                 list(df["Expenses"]) + [next_pred],
                 marker="x", linestyle="--", color="red", label="Predicted")
        ax1.set_xticklabels(month_labels + ["Next Month"], rotation=45)
        ax1.set_title("Actual vs Predicted Expenses")
        ax1.set_ylabel("Expenses (₹)")
        ax1.legend()
        st.pyplot(fig1)
        st.download_button("⬇️ Download Expenses Prediction Chart (PNG)",
                           fig_to_png_bytes(fig1), "actual_vs_predicted.png", "image/png")

        # 6-Month Savings Forecast
        st.subheader("💰 Savings Forecast (Next 6 Months)")
        avg_income = df["Income"].mean()
        future_idx = np.arange(len(df), len(df) + 6).reshape(-1, 1)
        future_exp = model.predict(future_idx)
        future_sav = avg_income - future_exp
        future_months = pd.period_range(start=pd.Period(df["Month"].iloc[-1], freq="M") + 1,
                                        periods=6, freq="M").astype(str)
        forecast_df = pd.DataFrame({"Month": future_months,
                                    "Predicted_Expenses": future_exp.round(2),
                                    "Predicted_Savings": future_sav.round(2)})
        st.dataframe(forecast_df, use_container_width=True)
        st.download_button("⬇️ Download Forecast (CSV)",
                           forecast_df.to_csv(index=False).encode(),
                           "forecast_6_months.csv", "text/csv")

        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.plot(future_months, future_sav, marker="x", linestyle="--", color="green", label="Predicted Savings")
        ax2.set_xticklabels(future_months, rotation=45)
        ax2.set_title("Savings Forecast (6 Months)")
        ax2.set_ylabel("Savings (₹)")
        ax2.legend()
        st.pyplot(fig2)
        st.download_button("⬇️ Download Savings Forecast Chart (PNG)",
                           fig_to_png_bytes(fig2), "savings_forecast.png", "image/png")

    # Cumulative Savings
    st.subheader("📈 Cumulative Savings")
    df["Cumulative_Savings"] = df["Savings"].cumsum()
    fig3, ax3 = plt.subplots(figsize=(8, 4))
    ax3.plot(month_labels, df["Cumulative_Savings"], marker="o", color="purple")
    ax3.set_xticklabels(month_labels, rotation=45)
    ax3.set_title("Cumulative Savings")
    ax3.set_ylabel("₹ Amount")
    st.pyplot(fig3)
    st.download_button("⬇️ Download Cumulative Savings (PNG)",
                       fig_to_png_bytes(fig3), "cumulative_savings.png", "image/png")

    # Income vs Expenses vs Savings
    st.subheader("📊 Income vs Expenses vs Savings")
    fig4, ax4 = plt.subplots(figsize=(10, 5))
    x = np.arange(len(df))
    w = 0.25
    ax4.bar(x - w, df["Income"], width=w, label="Income")
    ax4.bar(x, df["Expenses"], width=w, label="Expenses")
    ax4.bar(x + w, df["Savings"], width=w, label="Savings")
    ax4.set_xticks(x)
    ax4.set_xticklabels(month_labels, rotation=45)
    ax4.set_title("Income vs Expenses vs Savings")
    ax4.set_ylabel("₹ Amount")
    ax4.legend()
    st.pyplot(fig4)
    st.download_button("⬇️ Download Income/Expenses/Savings (PNG)",
                       fig_to_png_bytes(fig4), "income_expenses_savings.png", "image/png")

    # Insights
    st.markdown("---")
    st.subheader("💡 Insights")
    best = df.loc[df["Savings"].idxmax()]
    worst = df.loc[df["Savings"].idxmin()]
    st.write(f"🏆 Best Month: **{best['Month']}** with Savings = ₹{best['Savings']:.2f}")
    st.write(f"📉 Worst Month: **{worst['Month']}** with Savings = ₹{worst['Savings']:.2f}")

    loss_months = df[df["Expenses"] > df["Income"]]
    if not loss_months.empty:
        st.warning("⚠️ Break-Even: You overspent in some months.")
        st.dataframe(loss_months[["Month", "Income", "Expenses", "Savings"]])
    else:
        st.success("✅ No overspending months found!")

    df["Savings_Rate_%"] = np.where(df["Income"] > 0, (df["Savings"] / df["Income"]) * 100, np.nan)
    df["Expense_Growth_%"] = df["Expenses"].pct_change() * 100
    st.write("📊 Savings Efficiency (%) and Expense Growth Rate (%):")
    st.dataframe(df[["Month", "Savings_Rate_%", "Expense_Growth_%"]])

    # Download Insights as PDF
    pdf_buffer = generate_pdf_report(best, worst, loss_months, df)
    st.download_button("⬇️ Download Insights Report (PDF)", pdf_buffer, "finance_insights.pdf", "application/pdf")