import io, sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import feedparser
from urllib.parse import quote
import re
import time
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf
from pdf_generator import clean_ai_text, generate_pdf, render_report_upload_section
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from serpapi import GoogleSearch
from project.orchestrator import run_pipeline
from style import inject_css, render_news_card, render_metric_card, render_section_badge
from intelligence_navigator import render_intelligence_navigator
load_dotenv()

# ── yfinance crumb fix — must be set before any yfinance calls ─────────────────
import requests as _requests
_YF_SESSION = _requests.Session()
_YF_SESSION.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

# ── Config ─────────────────────────────────────────────────────────────────────
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")
MONGO_URI    = os.getenv("MONGO_URI")

COLORS = [
    ("#4F8EF7", "rgba(79,142,247,0.12)"),
    ("#F76A4F", "rgba(247,106,79,0.12)"),
    ("#2ECC71", "rgba(46,204,113,0.12)"),
    ("#F1C40F", "rgba(241,196,15,0.12)"),
    ("#9B59B6", "rgba(155,89,182,0.12)"),
]

st.set_page_config(
    page_title="Company Intelligence Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()
# ══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_db():
    client = MongoClient(MONGO_URI)
    return client["market_intelligence"]

# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ══════════════════════════════════════════════════════════════════════════════
USERS = {
    "admin":    {"password": "admin", "role": "admin"},
    "employee": {"password": "1234",  "role": "employee"},
}

def show_login():
    st.title("🧠 Company Intelligence Dashboard")
    st.divider()
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.subheader("Sign In")
        user_id  = st.text_input("User ID", placeholder="employee or admin")
        password = st.text_input("Password", type="password")
        if st.button("Login", type="primary", use_container_width=True):
            user = USERS.get(user_id.strip())
            if user and user["password"] == password.strip():
                st.session_state["logged_in"] = True
                st.session_state["user_id"]   = user_id.strip()
                st.session_state["role"]      = user["role"]
                st.rerun()
            else:
                st.error("Invalid user ID or password.")

def is_admin() -> bool:
    return st.session_state.get("role") == "admin"

# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS (MongoDB)
# ══════════════════════════════════════════════════════════════════════════════
CONFIG_DOC_ID = "global_company_config"

def load_settings() -> dict:
    try:
        db  = get_db()
        doc = db["config"].find_one({"_id": CONFIG_DOC_ID})
        if doc:
            return {
                "company_name":     doc.get("company_name", ""),
                "company_ticker":   doc.get("company_ticker", ""),
                "competitors":      doc.get("competitors", []),
                "auto_competitors": doc.get("auto_competitors", True),
            }
    except Exception:
        pass
    return {"company_name": "", "company_ticker": "", "competitors": [], "auto_competitors": True}

def save_settings(s: dict):
    try:
        db = get_db()
        db["config"].update_one(
            {"_id": CONFIG_DOC_ID},
            {"$set": {
                "company_name":     s["company_name"],
                "company_ticker":   s["company_ticker"],
                "competitors":      s["competitors"],
                "auto_competitors": s["auto_competitors"],
                "updated_at":       datetime.utcnow(),
                "updated_by":       st.session_state.get("user_id", "admin"),
            }},
            upsert=True,
        )
    except Exception as e:
        st.error(f"Failed to save settings: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TICKER RESOLUTION
# ══════════════════════════════════════════════════════════════════════════════
KNOWN_TICKERS = {
    "apple": "AAPL", "samsung": "005930.KS", "google": "GOOGL",
    "alphabet": "GOOGL", "microsoft": "MSFT", "amazon": "AMZN",
    "meta": "META", "facebook": "META", "tesla": "TSLA",
    "nvidia": "NVDA", "nike": "NKE", "adidas": "ADDYY",
    "puma": "PUMSY", "sony": "SONY", "intel": "INTC",
    "amd": "AMD", "netflix": "NFLX", "spotify": "SPOT",
    "uber": "UBER", "airbnb": "ABNB", "coca cola": "KO",
    "pepsi": "PEP", "walmart": "WMT", "disney": "DIS",
    "ford": "F", "toyota": "TM", "jpmorgan": "JPM",
    "tata": "TATAMOTORS.NS", "infosys": "INFY", "wipro": "WIT",
    "reliance": "RELIANCE.NS", "hdfc": "HDFCBANK.NS",
}

def resolve_ticker(keyword: str) -> str | None:
    key = keyword.lower().strip()
    if key in KNOWN_TICKERS:
        return KNOWN_TICKERS[key]
    try:
        results = yf.Search(keyword, max_results=1).quotes
        if results:
            return results[0].get("symbol")
    except Exception:
        pass
    return None

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCHERS
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def fetch_trend(keyword: str) -> pd.DataFrame:
    """Fetch Google Trends data via SerpAPI (falls back to empty if unavailable)."""
    if not SERP_API_KEY:
        return pd.DataFrame()
    try:
        data = GoogleSearch({
            "engine": "google_trends", "q": keyword,
            "data_type": "TIMESERIES", "date": "today 12-m",
            "api_key": SERP_API_KEY,
        }).get_dict()
        rows = [
            {"date": p["date"], "value": p["values"][0].get("extracted_value", 0)}
            for p in data.get("interest_over_time", {}).get("timeline_data", [])
        ]
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_news(keyword: str, num: int = 6):

    encoded_keyword = quote(keyword)

    url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)

    articles = []

    for entry in feed.entries[:num]:

        snippet = re.sub('<.*?>', '', entry.summary)

        articles.append({
            "title": entry.title,
            "source": entry.source.title if "source" in entry else "Google News",
            "date": entry.published,
            "snippet": snippet,
            "link": entry.link
        })

    return articles
def fetch_stock_price(ticker: str) -> pd.DataFrame:
    for use_session in [True, False]:
        try:
            t  = yf.Ticker(ticker, session=_YF_SESSION) if use_session else yf.Ticker(ticker)
            df = t.history(period="1y")[["Close"]].reset_index()
            if df.empty:
                continue
            df.columns = ["date", "price"]
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            return df
        except Exception:
            continue
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_financials(ticker: str) -> dict:
    for use_session in [True, False]:
        try:
            t    = yf.Ticker(ticker, session=_YF_SESSION) if use_session else yf.Ticker(ticker)
            info = t.info
            if not info or not info.get("longName"):
                continue
            q_fin = t.quarterly_financials
            revenue_series = {}
            if q_fin is not None and not q_fin.empty:
                rev_row = q_fin.loc["Total Revenue"] if "Total Revenue" in q_fin.index else None
                if rev_row is not None:
                    revenue_series = {
                        str(col.date()): int(val / 1e6)
                        for col, val in rev_row.items() if str(val) != "nan"
                    }
            return {
                "ticker":            ticker.upper(),
                "company_name":      info.get("longName", ticker),
                "market_cap":        info.get("marketCap", 0),
                "revenue_ttm":       info.get("totalRevenue", 0),
                "gross_margin":      info.get("grossMargins", 0),
                "pe_ratio":          info.get("trailingPE", 0),
                "52w_high":          info.get("fiftyTwoWeekHigh", 0),
                "52w_low":           info.get("fiftyTwoWeekLow", 0),
                "current_price":     info.get("currentPrice", 0),
                "revenue_quarterly": revenue_series,
                "debt_to_equity":    info.get("debtToEquity", 0),
                "return_on_equity":  info.get("returnOnEquity", 0),
                "operating_margin":  info.get("operatingMargins", 0),
                "eps":               info.get("trailingEps", 0),
                "dividend_yield":    info.get("dividendYield", 0),
            }
        except Exception:
            continue
    return {}

# ══════════════════════════════════════════════════════════════════════════════
# CHART BUILDERS
# ══════════════════════════════════════════════════════════════════════════════
def build_trend_chart(keywords, dataframes):
    fig = go.Figure()
    for i, (keyword, df) in enumerate(zip(keywords, dataframes)):
        if df.empty:
            continue
        color, fill = COLORS[i % len(COLORS)]
        vals = df["value"].astype(int)
        fig.add_trace(go.Scatter(
            x=df["date"], y=vals, name=keyword,
            mode="lines", line=dict(color=color, width=2.5),
            fill="tozeroy", fillcolor=fill,
            hovertemplate="%{x} — <b>%{y}</b><extra>" + keyword + "</extra>",
        ))
        pk = vals.idxmax()
        fig.add_trace(go.Scatter(
            x=[df.loc[pk, "date"]], y=[vals[pk]], mode="markers+text",
            marker=dict(color=color, size=11, symbol="star"),
            text=[f" Peak {vals[pk]}"], textposition="middle right",
            textfont=dict(color=color), showlegend=False, hoverinfo="skip",
        ))
    fig.update_layout(
        hovermode="x unified", height=360,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickangle=-40, tickfont=dict(size=10)),
        yaxis=dict(title="Interest (0-100)", gridcolor="rgba(180,180,180,0.15)"),
        legend=dict(orientation="h", y=1.05),
        margin=dict(l=50, r=20, t=40, b=50),
    )
    return fig

def build_stock_chart(tickers, stock_dfs):
    fig = go.Figure()
    for i, ticker in enumerate(tickers):
        df = stock_dfs.get(ticker)
        if df is None or df.empty:
            continue
        color, _ = COLORS[i % len(COLORS)]
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["price"].round(2), name=ticker,
            mode="lines", line=dict(color=color, width=2.5),
            hovertemplate="%{x} — <b>$%{y}</b><extra>" + ticker + "</extra>",
        ))
    fig.update_layout(
        hovermode="x unified", height=340,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickangle=-40, tickfont=dict(size=10)),
        yaxis=dict(title="Stock Price (USD)", gridcolor="rgba(180,180,180,0.15)"),
        legend=dict(orientation="h", y=1.05),
        margin=dict(l=50, r=20, t=40, b=50),
    )
    return fig

def build_revenue_chart(tickers, financials):
    fig = go.Figure()
    for i, ticker in enumerate(tickers):
        fin = financials.get(ticker, {})
        rev = fin.get("revenue_quarterly", {})
        if not rev:
            continue
        dates  = sorted(rev.keys())
        values = [rev[d] for d in dates]
        color, _ = COLORS[i % len(COLORS)]
        fig.add_trace(go.Bar(
            x=dates, y=values,
            name=f"{fin.get('company_name', ticker)} ($M)",
            marker_color=color, opacity=0.85,
        ))
    fig.update_layout(
        barmode="group", height=300,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickangle=-40, tickfont=dict(size=10)),
        yaxis=dict(title="Revenue ($M)", gridcolor="rgba(180,180,180,0.15)"),
        legend=dict(orientation="h", y=1.05),
        margin=dict(l=50, r=20, t=40, b=50),
    )
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# FINANCIAL COMPARISON TABLE
# ══════════════════════════════════════════════════════════════════════════════
def render_financial_comparison(ticker_map: dict, financials: dict):
    st.subheader("📊 Financial Metrics Comparison")
    metrics = [
        ("Current Price",    "current_price",   lambda v: f"${v:.2f}"),
        ("Market Cap",       "market_cap",       lambda v: f"${v/1e9:.1f}B"),
        ("TTM Revenue",      "revenue_ttm",      lambda v: f"${v/1e9:.1f}B"),
        ("Gross Margin",     "gross_margin",     lambda v: f"{v*100:.1f}%"),
        ("Operating Margin", "operating_margin", lambda v: f"{v*100:.1f}%"),
        ("P/E Ratio",        "pe_ratio",         lambda v: f"{v:.1f}x"),
        ("EPS",              "eps",              lambda v: f"${v:.2f}"),
        ("Return on Equity", "return_on_equity", lambda v: f"{v*100:.1f}%"),
        ("Debt / Equity",    "debt_to_equity",   lambda v: f"{v:.2f}"),
        ("Dividend Yield",   "dividend_yield",   lambda v: f"{v*100:.2f}%" if v else "N/A"),
        ("52W High",         "52w_high",         lambda v: f"${float(v):.2f}"),
        ("52W Low",          "52w_low",          lambda v: f"${float(v):.2f}"),
    ]
    rows = {}
    for label, key, fmt in metrics:
        row = {}
        for company, ticker in ticker_map.items():
            fin = financials.get(ticker, {})
            val = fin.get(key, 0)
            try:
                row[company] = fmt(val) if val else "N/A"
            except Exception:
                row[company] = "N/A"
        rows[label] = row
    df = pd.DataFrame(rows).T
    df.index.name = "Metric"
    st.dataframe(df, use_container_width=True)
    @st.fragment
    def metric_chart():
        st.subheader("📈 Key Metrics — Visual Comparison")
        metric_choice = st.selectbox(
            "Select metric to compare",
            ["Market Cap ($B)", "TTM Revenue ($B)", "Gross Margin (%)",
            "P/E Ratio", "Return on Equity (%)", "Operating Margin (%)"],
        )
        metric_map = {
            "Market Cap ($B)":      ("market_cap",       lambda v: v / 1e9),
            "TTM Revenue ($B)":     ("revenue_ttm",      lambda v: v / 1e9),
            "Gross Margin (%)":     ("gross_margin",     lambda v: v * 100),
            "P/E Ratio":            ("pe_ratio",         lambda v: v),
            "Return on Equity (%)": ("return_on_equity", lambda v: v * 100),
            "Operating Margin (%)": ("operating_margin", lambda v: v * 100),
        }
        key, transform = metric_map[metric_choice]
        bar_fig = go.Figure()
        for i, (company, ticker) in enumerate(ticker_map.items()):
            fin = financials.get(ticker, {})
            val = fin.get(key, 0)
            color, _ = COLORS[i % len(COLORS)]
            bar_fig.add_trace(go.Bar(
                x=[company], y=[transform(val) if val else 0],
                name=company, marker_color=color,
            ))
        bar_fig.update_layout(
            height=320, barmode="group",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(title=metric_choice, gridcolor="rgba(180,180,180,0.15)"),
            xaxis=dict(showgrid=False),
            showlegend=False,
            margin=dict(l=50, r=20, t=20, b=40),
        )
        st.plotly_chart(bar_fig, use_container_width=True)
    metric_chart()
# ══════════════════════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def render_dashboard(settings: dict):
    company      = settings["company_name"]
    competitors  = settings["competitors"]
    all_keywords = [company] + competitors

    # ── Resolve tickers ────────────────────────────────────────────────────────
    ticker_map = {}
    with st.spinner("Resolving tickers…"):
        t = resolve_ticker(company)
        if t:
            ticker_map[company] = t
        for comp in competitors:
            t = resolve_ticker(comp)
            if t:
                ticker_map[comp] = t

    if ticker_map:
        st.sidebar.success(
            "Tickers: " + ", ".join([f"{k} → `{v}`" for k, v in ticker_map.items()])
        )

    # ── Parallel data fetch ────────────────────────────────────────────────────
    with st.spinner("Gathering intelligence…"):
        with ThreadPoolExecutor(max_workers=16) as ex:
            trend_futures     = [(kw, ex.submit(fetch_trend, kw)) for kw in all_keywords]
            news_future       = ex.submit(fetch_news, company, 6)
            comp_news_futures = [(c,  ex.submit(fetch_news, c, 3)) for c in competitors]
            stock_futures     = [(t,  ex.submit(fetch_stock_price, t)) for t in ticker_map.values()]
            fin_futures       = [(t,  ex.submit(fetch_financials, t)) for t in ticker_map.values()]

            trend_dfs    = {kw: f.result() for kw, f in trend_futures}
            company_news = news_future.result()
            comp_news    = {c: f.result() for c, f in comp_news_futures}
            stock_dfs    = {t: f.result() for t, f in stock_futures}
            financials   = {t: f.result() for t, f in fin_futures}

    # ── Build context for orchestrator pipeline ────────────────────────────────
    company_fin    = financials.get(ticker_map.get(company, ""), {})
    comp_headlines = "\n".join([
        f"{c}: {' | '.join([a['title'] for a in articles[:3]])}"
        for c, articles in comp_news.items()
    ])
    trend_df      = trend_dfs.get(company, pd.DataFrame())
    trend_summary = (
        f"{company}: avg={trend_df['value'].mean():.1f}, peak={trend_df['value'].max()}"
        if not trend_df.empty else ""
    )
    comp_trends = "\n".join([
        f"{kw}: avg={df['value'].mean():.1f}, peak={df['value'].max()}"
        for kw, df in trend_dfs.items() if kw != company and not df.empty
    ])
    fin_summary = (
        f"Market Cap: ${company_fin.get('market_cap', 0)/1e9:.1f}B, "
        f"TTM Revenue: ${company_fin.get('revenue_ttm', 0)/1e9:.1f}B, "
        f"Gross Margin: {company_fin.get('gross_margin', 0)*100:.1f}%, "
        f"P/E: {company_fin.get('pe_ratio', 0):.1f}, "
        f"Price: ${company_fin.get('current_price', 0):.2f}"
    ) if company_fin else ""

    # ── Run MCP orchestrator pipeline ─────────────────────────────────────────
    context = {
        "company":     company,
        "competitors": competitors,
        "news": company_news,
        "trends":      f"{trend_summary}\n{comp_trends}",
        "financials":  fin_summary,
        "comp_news":   comp_headlines,
    }

    with st.spinner("Running AI agents via orchestrator…"):
        results = run_pipeline(context)

    news_out    = results.get("news", "")
    comp_out    = results.get("competitor", "")
    fin_out     = results.get("financial", "")
    brief       = results.get("brief", "")
    improvement = results.get("improvement", "")

    # Extract strategic recommendations section
    improve_out=improvement

    generated_at = datetime.now().strftime("%B %d, %Y %H:%M")

    # ── Page header ────────────────────────────────────────────────────────────
    st.title(f"🧠 {company} — Intelligence Dashboard")
    st.caption(f"Report generated · {generated_at}")

# ── PDF download ─────────────────────────────────────────────────────
    try:
        pdf_bytes = generate_pdf(
                company, competitors, brief, news_out, comp_out,
                fin_out, improve_out, financials, ticker_map, generated_at,
            )
        st.download_button(
                label="📄 Download Full Report (PDF)",
                data=pdf_bytes,
                file_name=f"{company.replace(' ', '_')}_Intelligence_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                type="primary",
            )
    except Exception as e:
            st.warning(f"PDF generation unavailable: {e}")

    st.divider()

    # ── Executive brief ────────────────────────────────────────────────────────
    st.subheader("📋 Executive Brief")
    st.info(brief)
    st.divider()

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📰 News & Sentiment",
        "⚔️ Competitor Analysis",
        "💰 Financials",
        "🎯 What to Improve",
        "📄 Report Forecasting",
        "🧭 Intelligence Navigator",   # ← new
    ])

    # ── Tab 1 — News ──────────────────────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"Latest News — {company}")
            for article in company_news:
                render_news_card(article)
        with col2:
            st.subheader("AI News Analysis")
            st.markdown(news_out)

    # ── Tab 2 — Competitors ───────────────────────────────────────────────────
    with tab2:
        st.subheader("📈 Search Interest vs Competitors")
        trend_list = [trend_dfs.get(kw, pd.DataFrame()) for kw in all_keywords]
        if any(not df.empty for df in trend_list):
            st.plotly_chart(
                build_trend_chart(all_keywords, trend_list),
                use_container_width=True,
            )
        else:
            st.info("Google Trends data unavailable (SerpAPI key not set).")

        if competitors:
            st.subheader("Competitor News")
            comp_tabs = st.tabs(competitors)
            for ctab, comp in zip(comp_tabs, competitors):
                with ctab:
                    for article in comp_news.get(comp, []):
                        render_news_card(article)

            st.subheader("AI Competitor Analysis")
            st.markdown(comp_out)

    # ── Tab 3 — Financials ────────────────────────────────────────────────────
    with tab3:
        if ticker_map:
            company_fin = financials.get(ticker_map.get(company, ""), {})
            if company_fin:
                cols = st.columns(4)
                kpis = [
                ("Current Price",  f"${company_fin.get('current_price', 0):.2f}", "", True),
                ("Market Cap",     f"${company_fin.get('market_cap', 0)/1e9:.1f}B", "", True),
                ("P/E Ratio",      f"{company_fin.get('pe_ratio', 0):.1f}x", "", True),
                ("Gross Margin",   f"{company_fin.get('gross_margin', 0)*100:.1f}%", "", True),
            ]
            for col, (label, val, delta, up) in zip(cols, kpis):
                with col:
                    render_metric_card(label, val, delta, up)
            all_tickers = list(ticker_map.values())

            st.subheader("📈 Stock Price (Last 12 Months)")
            st.plotly_chart(
                build_stock_chart(all_tickers, stock_dfs),
                use_container_width=True,
            )
            st.divider()
            
            render_financial_comparison(ticker_map, financials)
            st.divider()

            st.subheader("💵 Quarterly Revenue ($M)")
            st.plotly_chart(
                build_revenue_chart(all_tickers, financials),
                use_container_width=True,
            )

            st.subheader("AI Financial Analysis")
            sections = fin_out.split("RISKS:")

            growth_text = sections[0].replace("GROWTH SIGNALS:", "").strip()
            risk_text = sections[1].strip() if len(sections) > 1 else ""

            st.markdown("### 📈 Growth Signals")
            st.markdown(growth_text)

            st.markdown("### ⚠️ Risks")
            st.markdown(risk_text)
    # ── Tab 4 — What to Improve ───────────────────────────────────────────────
    with tab4:
        st.subheader(f"🎯 What {company} Should Improve")
        st.markdown(improve_out)

    with tab5:
        @st.fragment
        def forecast_tab():
            render_report_upload_section(
            default_ticker=ticker_map.get(company, ""),
            default_topic=company,
        )
        forecast_tab()
    with tab6:
        @st.fragment
        def run_intelli():
            render_intelligence_navigator(
                company, brief, news_out, comp_out,
                fin_out, improve_out, financials,
                ticker_map, competitors
            )
        run_intelli()


# ══════════════════════════════════════════════════════════════════════════════
# APP ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.get("logged_in"):
    show_login()
    st.stop()

settings = load_settings()

with st.sidebar:
    st.markdown(
        f"👤 **{st.session_state['user_id']}** "
        f"({'Admin' if is_admin() else 'Employee'})"
    )
    if st.button("Logout", use_container_width=True):
        for key in ["logged_in", "user_id", "role"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()

    if is_admin():
        st.title("⚙️ Admin Settings")
        st.caption("Set once — employees see the report on open.")
        st.divider()

        company_name = st.text_input(
            "Company name",
            value=settings.get("company_name", ""),
            placeholder="e.g. Nike",
        )
        st.caption("Stock ticker is resolved automatically from the company name.")

        st.markdown("**Competitors**")
        auto_comp = st.checkbox(
            "Auto-detect competitors (via orchestrator)",
            value=settings.get("auto_competitors", True),
        )
        manual_competitors = st.text_input(
            "Or enter manually (comma-separated)",
            value=", ".join(settings.get("competitors", [])),
            placeholder="e.g. Adidas, Puma, New Balance",
            disabled=auto_comp,
        )

        if st.button("💾 Save & Load Dashboard", type="primary", use_container_width=True):
            if not company_name.strip():
                st.error("Please enter a company name.")
            else:
                competitors = []
                if auto_comp:
                    with st.spinner("Detecting competitors via orchestrator…"):
                        try:
                            result = run_pipeline({
                                "company": company_name.strip(),
                                "task": "detect_competitors",
                            })
                            competitors = result.get("competitors", [])
                        except Exception:
                            competitors = []
                    if competitors:
                        st.success(f"Detected: {', '.join(competitors)}")
                    else:
                        st.warning("Could not auto-detect. Enter manually.")
                else:
                    competitors = [
                        c.strip() for c in manual_competitors.split(",") if c.strip()
                    ]

                save_settings({
                    "company_name":     company_name.strip(),
                    "company_ticker":   "",
                    "competitors":      competitors,
                    "auto_competitors": auto_comp,
                })
                st.rerun()

    if settings.get("company_name"):
        st.success(f"Tracking: **{settings['company_name']}**")
        if settings.get("competitors"):
            st.caption("vs " + ", ".join(settings["competitors"]))
        if st.button("🔄 Refresh Report", use_container_width=True):
            st.rerun()

# ── Render ─────────────────────────────────────────────────────────────────────
if not settings.get("company_name"):
    st.title("🧠 Company Intelligence Dashboard")
    st.divider()
    if is_admin():
        st.info("👈 Open the sidebar, enter your company name, and click Save & Load Dashboard.")
    else:
        st.info("The dashboard is being configured by your admin. Please check back shortly.")
else:
    render_dashboard(settings)