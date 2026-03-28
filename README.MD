# 🧠 Real-Time Industry Insight & Strategic Intelligence System

> **Infosys Springboard – Artificial Intelligence Internship Project**

An AI-powered, multi-agent strategic intelligence platform that delivers real-time market analysis, competitive intelligence, financial insights, and actionable recommendations. Configured once by an admin — every employee sees a live, auto-refreshing intelligence dashboard for their company.

---

## 🚀 Features

- 🔐 **Role-Based Authentication** — Admin and Employee login with session state management
- ⚙️ **Admin Control Panel** — Set target company and competitors via sidebar; config persisted in MongoDB Atlas so all users share the same state
- 🤖 **Auto Competitor Detection** — Orchestrator automatically identifies top competitors via LLM if not set manually
- 📰 **News Intelligence** — Google News RSS feed with AI-driven opportunity and risk extraction per company
- ⚔️ **Competitor Analysis** — Per-competitor news tabs, Google Trends search interest comparison, and AI competitive analysis
- 💰 **Financial Dashboard** — 12-month stock price chart, quarterly revenue bars, and a 12-metric comparison table (Market Cap, P/E, Gross Margin, ROE, EPS, and more) via `yfinance`
- 🎯 **Strategic Recommendations** — AI-generated improvement plan in `[Action] → [Impact]` format
- 📋 **Executive Brief** — 5-point C-suite summary synthesized from all agent outputs
- 📈 **LSTM Forecasting** — 2-layer stacked LSTM model (PyTorch) for stock price prediction
- 📄 **PDF Export** — Full intelligence report download via ReportLab
- ⚡ **Parallel Execution** — Data fetching and AI agents both run concurrently via `ThreadPoolExecutor`
- 🎨 **Premium UI** — Custom dark theme with gold accents injected via Streamlit CSS

---

## 🏗️ Project Structure

```
RealTimeMarketIntelli/
│
├── agents/
│   ├── news_agent.py          # Extracts opportunities & risks from headlines
│   ├── competitor_agent.py    # Competitive positioning + detect_competitors()
│   ├── financial_agent.py     # Growth signals and risk from financial data
│   ├── chief_agent.py         # Synthesizes all reports into executive brief
│   ├── improvement_agent.py   # Strategic recommendations
│   └── forecasting_agent.py   # LSTM-based stock price forecasting
│
├── project/
│   ├── app.py                 # Main Streamlit application
│   ├── orchestrator.py        # Pipeline coordinator (parallel agent execution)
│   ├── llm.py                 # HuggingFace InferenceClient wrapper
│   └── pdf_generator.py       # ReportLab PDF export
│
├── tools/
│   └── rag_tools.py           # RAG knowledge base search
│
├── data/
│   └── knowledge/             # Domain knowledge documents for RAG
│
├── vector_store/              # Embedded vector indexes
├── requirements.txt
└── .gitignore
```

---

## 🧠 Architecture

```
                        ┌──────────────────────────┐
                        │      Streamlit UI         │
                        │  Role-based · Wide layout │
                        └────────────┬─────────────┘
                                     │
                             ┌───────▼────────┐
                             │  Orchestrator  │
                             │  run_pipeline  │
                             └───────┬────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │   PARALLEL     │   EXECUTION     │
                    ▼                ▼                 ▼
             news_agent      competitor_agent   financial_agent
            (RSS + RAG)      (Trends + RAG)    (yfinance + RAG)
                    │                │                 │
                    └────────────────┼─────────────────┘
                                     │ combined output
                              ┌──────┴──────┐
                              │  PARALLEL   │
                    ┌─────────▼──┐     ┌────▼────────────┐
                    │ chief_agent│     │improvement_agent │
                    │ (brief)    │     │(recommendations) │
                    └────────────┘     └─────────────────┘
                                     │
                        ┌────────────▼────────────┐
                        │     Streamlit Dashboard  │
                        │  News · Competitors ·    │
                        │  Financials · Strategy · │
                        │  Forecasting · PDF       │
                        └─────────────────────────┘
```

**RAG flow:** Each agent receives pre-fetched knowledge from `search_company_knowledge()` — called once in the orchestrator and shared across all agents to avoid redundant vector store queries.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend / UI** | Streamlit, Plotly, custom CSS theme |
| **LLM** | Groq (`llama-3.3-70b-versatile` or similar) via `groq` SDK |
| **Agent Framework** | Custom multi-agent orchestrator with `ThreadPoolExecutor` |
| **RAG** | Sentence Transformers + custom vector store |
| **News** | Google News RSS (`feedparser`), SerpAPI fallback |
| **Market Data** | `yfinance` with custom `requests.Session` (User-Agent fix) |
| **Trends** | SerpAPI Google Trends |
| **Forecasting** | PyTorch LSTM (2-layer stacked) |
| **Database** | MongoDB Atlas (shared config via `_id = "global_company_config"`) |
| **PDF Export** | ReportLab |
| **Environment** | python-dotenv |

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.9+
- MongoDB Atlas account
- HuggingFace account (free tier works)
- SerpAPI key (optional — used for Trends and news fallback)

### 1. Clone the Repository

```bash
git clone https://github.com/Ewanjohndennis/RealTimeMarketIntelli.git
cd RealTimeMarketIntelli
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key
SERP_API_KEY=your_serpapi_key
MONGO_URI=your_mongodb_atlas_connection_string
```

> `NEWS_API_KEY` is optional — the system uses Google News RSS as the primary source and SerpAPI as fallback.

### 5. Run the Application

```bash
streamlit run project/app.py
```

Open `http://localhost:8501` in your browser.

---

## 🔑 Default Login Credentials

| Role | User ID | Password |
|---|---|---|
| Admin | `admin` | `admin` |
| Employee | `employee` | `1234` |

> Admin users can set the target company and competitors from the sidebar. Employees see the generated dashboard automatically.

---

## 📸 Usage Flow

1. **Login** as admin at `http://localhost:8501`
2. **Open the sidebar** and enter your target company (e.g. `Apple`)
3. Toggle **Auto-detect competitors** or enter them manually
4. Click **Save & Load Dashboard** — config is saved to MongoDB
5. The system fetches news, trends, and financial data in parallel, then runs the AI agent pipeline
6. View results across 5 tabs: **News & Sentiment**, **Competitor Analysis**, **Financials**, **What to Improve**, **Forecasting**
7. Click **Download Full Report (PDF)** to export

---

## 🤖 Agent Pipeline

| Agent | Input | Output |
|---|---|---|
| `news_agent` | Company news articles + RAG knowledge | Opportunities & risks from headlines |
| `competitor_agent` | Competitors list + Google Trends + RAG | Competitive positioning analysis |
| `financial_agent` | yfinance summary + RAG | Growth signals and financial risks |
| `chief_agent` | Combined agent outputs + RAG | 5-point executive brief |
| `improvement_agent` | Combined agent outputs | 5 strategic recommendations |
| `forecasting_agent` | Historical stock data | LSTM price forecast |

---

## 🔑 API Keys

| Service | Purpose | Link |
|---|---|---|
| HuggingFace | LLM inference (`openai/gpt-oss-20b`) | [huggingface.co](https://huggingface.co) |
| SerpAPI | Google Trends + news fallback | [serpapi.com](https://serpapi.com) |
| MongoDB Atlas | Shared config persistence | [mongodb.com/atlas](https://www.mongodb.com/cloud/atlas) |

---

## 🔄 LLM Backend History

This project has been through more LLM providers than most projects have hot meals.

The current backend is Groq (`llama-3.3-70b-versatile`) — but when the free tier limit hits, the codebase has a well-documented history of emergency provider swaps:

| Provider | Status | Reason for Switch |
|---|---|---|
| Groq | ✅ Current | Fast inference, generous free tier |
| HuggingFace | 🪦 Retired | Rate limit hit |
| OpenRouter | 🪦 Retired | Ran out of credits |
| Azure OpenAI | 🪦 Original | Trial expired |

> If the app suddenly stops working, assume the token limit was hit and check which provider is next in the rotation. A new API key is usually 15 minutes away.

The `project/llm.py` file is essentially a graveyard of commented-out provider configs, each one a timestamp of a deadline that was closer than the rate limit.

## 🎓 Internship Context

This project was developed as part of the **Infosys Springboard Artificial Intelligence Internship**. It demonstrates practical application of:

- Multi-agent AI system design and orchestration
- Retrieval-Augmented Generation (RAG)
- Real-time parallel data pipeline architecture
- LLM prompt engineering and token optimization
- Full-stack AI application development with Streamlit
- Time-series forecasting with LSTM (PyTorch)
- Cloud database integration (MongoDB Atlas)

---

## 👤 Author

**Ewan John Dennis**
B.Tech Computer Science Engineering · Model Engineering College, Thrikkakara
[GitHub](https://github.com/Ewanjohndennis)

---

## 📄 License

Developed for educational purposes as part of the Infosys Springboard AI Internship program.