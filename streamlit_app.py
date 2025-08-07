
# Stock Research AI Web App (Final Version: Full Features)

import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import fitz  # PyMuPDF for PDF text extraction
import openai
import requests

# Set page config
st.set_page_config(page_title="AI Stock Researcher", layout="wide")
st.title("📊 AI-Powered Stock Research Assistant")

# --- 0. API Key Input ---
st.sidebar.header("🔐 API Configuration")
openai_api_key = st.sidebar.text_input("Enter your OpenAI API key", type="password")
if openai_api_key:
    openai.api_key = openai_api_key

# --- 1. Upload Financial Report (PDF) ---
st.header("1. Upload Company Financial Report (PDF)")
pdf_file = st.file_uploader("Upload an annual report or prospectus (PDF only):", type="pdf")
if pdf_file and openai_api_key:
    pdf_text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            pdf_text += page.get_text()

    truncated_text = pdf_text[:4000]

    st.subheader("📌 GPT Summary")
    summary_prompt = f"Summarize this financial report for an investor:\n{truncated_text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial analyst."},
                {"role": "user", "content": summary_prompt}
            ]
        )
        st.write(response.choices[0].message.content)
    except Exception as e:
        st.error("GPT Error: " + str(e))

    st.subheader("🔎 Ask a Question About the Report")
    question = st.text_input("Your question:")
    if question:
        qna_prompt = f"Based on this report:\n{truncated_text}\nAnswer this: {question}"
        try:
            qna_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a financial analyst."},
                    {"role": "user", "content": qna_prompt}
                ]
            )
            st.write(qna_response.choices[0].message.content)
        except Exception as e:
            st.error("GPT Error: " + str(e))

# --- 2. Web Search News Analysis ---
st.header("2. Macroeconomic / Industry News")
query = st.text_input("Enter a company or industry keyword:")
if query and openai_api_key:
    try:
        web_prompt = f"Find and summarize latest macroeconomic and industry news about: {query}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an economist summarizing business news."},
                {"role": "user", "content": web_prompt}
            ]
        )
        st.subheader("🌐 Web Summary")
        st.write(response.choices[0].message.content)
        st.markdown(f"[🔗 View Google News](https://www.google.com/search?q={query}+site:news.google.com)")
    except Exception as e:
        st.error("GPT Error: " + str(e))

# --- 3. Compare Two Stocks ---
st.header("3. Compare Two Stocks")
col1, col2 = st.columns(2)
with col1:
    stock1 = st.text_input("Stock 1 (e.g., INFY.NS)", value="TCS.NS")
with col2:
    stock2 = st.text_input("Stock 2 (e.g., TCS.NS)", value="INFY.NS")

@st.cache_data
def fetch_metrics(ticker):
    t = yf.Ticker(ticker)
    i = t.info
    return {
        "Ticker": ticker,
        "ROE": i.get("returnOnEquity"),
        "ROA": i.get("returnOnAssets"),
        "EPS (TTM)": i.get("trailingEps"),
        "Debt/Equity": i.get("debtToEquity"),
        "Current Ratio": i.get("currentRatio"),
        "Operating Margin": i.get("operatingMargins"),
        "Net Profit Margin": i.get("netMargins"),
        "PEG Ratio": i.get("pegRatio"),
        "Gross Margin": i.get("grossMargins"),
        "Free Cash Flow": i.get("freeCashflow")
    }

def calculate_fundamental_score(metrics):
    score = 0
    if metrics["ROE"] and metrics["ROE"] > 0.15: score += 1
    if metrics["ROA"] and metrics["ROA"] > 0.1: score += 1
    if metrics["Operating Margin"] and metrics["Operating Margin"] > 0.15: score += 1
    if metrics["Net Profit Margin"] and metrics["Net Profit Margin"] > 0.12: score += 1
    if metrics["Debt/Equity"] and metrics["Debt/Equity"] < 1: score += 1
    if metrics["Current Ratio"] and metrics["Current Ratio"] > 1.5: score += 1
    if metrics["EPS (TTM)"] and metrics["EPS (TTM)"] > 0: score += 1
    if metrics["PEG Ratio"] and metrics["PEG Ratio"] < 2: score += 1
    if metrics["Gross Margin"] and metrics["Gross Margin"] > 0.4: score += 1
    if metrics["Free Cash Flow"] and metrics["Free Cash Flow"] > 0: score += 1
    return score

def display_comparison(ticker1, ticker2):
    try:
        m1 = fetch_metrics(ticker1)
        m2 = fetch_metrics(ticker2)
        df = pd.DataFrame([m1, m2]).set_index("Ticker")
        st.subheader("📊 Comparison Table")
        st.dataframe(df)

        st.subheader("✅ Fundamental Scores (/10)")
        st.write(f"**{ticker1}:** {calculate_fundamental_score(m1)} / 10")
        st.write(f"**{ticker2}:** {calculate_fundamental_score(m2)} / 10")

        st.subheader("💰 Owner Earnings")
        def owner_earnings(t):
            try:
                fin = yf.Ticker(t)
                cf = fin.cashflow
                bs = fin.balance_sheet
                ni = fin.financials.loc["Net Income"].values[0]
                dep = cf.loc["Depreciation"].values[0]
                capex = cf.loc["Capital Expenditures"].values[0]
                wc = bs.loc["Total Current Assets"].values[0] - bs.loc["Total Current Liabilities"].values[0]
                return ni + dep - capex - wc
            except:
                return None
        oe1 = owner_earnings(ticker1)
        oe2 = owner_earnings(ticker2)
        st.write(f"{ticker1} Owner Earnings: ₹{oe1:,.0f}" if oe1 else f"{ticker1}: Data not available")
        st.write(f"{ticker2} Owner Earnings: ₹{oe2:,.0f}" if oe2 else f"{ticker2}: Data not available")

    except Exception as e:
        st.error("Error comparing stocks: " + str(e))

if stock1 and stock2:
    display_comparison(stock1, stock2)

st.markdown("---")
st.caption("🛠️ Built by Vigyat Mishra | AI Stock Analysis App")
