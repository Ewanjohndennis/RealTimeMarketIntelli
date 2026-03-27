# 📊 Real-Time Industry Insight & Strategic Intelligence System

> **Infosys Springboard – Artificial Intelligence Internship Project**

An AI-powered, multi-agent strategic intelligence platform that delivers real-time market analysis, financial insights, and industry trend monitoring. Built with a LangChain-powered agentic architecture, RAG (Retrieval-Augmented Generation), and live data integrations to help businesses make data-driven decisions.

---

## 🚀 Features

- **Real-Time Market Data** — Live stock prices and financial metrics via `yfinance` and `TwelveData`
- **AI-Powered Analysis** — LLM-driven insight generation using openai/gpt-oss-20b model from HuggingFace
- **Multi-Agent Architecture** — Specialized agents for market research, financial analysis, and strategic synthesis
- **RAG Knowledge Base** — FAISS vector store with `sentence-transformers` for contextual document retrieval
- **Web Intelligence** — Live web search via Google News RSS, SerpAPI (`google-search-results`) and Wikipedia integration
- **Interactive Dashboard** — Streamlit-based UI with Plotly and Matplotlib visualizations
- **Report Generation** — Automated PDF report export with ReportLab
- **Persistent Storage** — MongoDB for data persistence and history tracking
- **MCP Integration** — Model Context Protocol support for extended tool connectivity

---

## 🏗️ Project Structure

```
RealTimeMarketIntelli/
│
├── agents/                  # AI agent definitions (market, financial, strategy agents)
├── data/
│   └── knowledge/           # Knowledge base documents for RAG ingestion
├── tools/                   # Custom tool implementations (search, finance, scraping)
├── vector_store/            # FAISS vector store indexes and embeddings
├── project/                 # Core application logic and orchestration
├── requirements.txt         # Python dependencies
├── package.json             # Node.js dependencies (MongoDB driver)
└── .gitignore
```

---

## 🧠 Architecture Overview

The system follows a multi-agent RAG pipeline:

```
User Query
    │
    ▼
Orchestrator Agent
    │
    ├──► Market Data Agent  ──► yfinance / TwelveData
    ├──► Research Agent     ──► Google News RSS, SerpAPI / Wikipedia
    ├──► RAG Agent          ──► FAISS Vector Store + HuggingFace Embeddings
    └──► Synthesis Agent    ──► HuggingFace Model
                │
                ▼
        Streamlit Dashboard  ──►  PDF Report
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend / UI** | Streamlit, Plotly, Matplotlib |
| **AI / LLM** | Groq, Anthropic Claude, HuggingFace |
| **Agents / Chains** | LangChain, LangChain-Community |
| **Vector Store** | FAISS, Sentence Transformers |
| **Market Data** | yfinance, TwelveData |
| **Web Search** | Google News RSS, SerpAPI (google-search-results), Wikipedia |
| **Database** | MongoDB (PyMongo) |
| **Report Export** | ReportLab |
| **Protocol** | MCP (Model Context Protocol) |
| **Environment** | python-dotenv |

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.9+
- Node.js 18+ (for MongoDB JS driver, optional)
- API keys for: Groq, Anthropic, SerpAPI, TwelveData

### 1. Clone the Repository

```bash
git clone https://github.com/Ewanjohndennis/RealTimeMarketIntelli.git
cd RealTimeMarketIntelli
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Node Dependencies (optional)

```bash
npm install
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```env
SERPAPI_API_KEY=your_serpapi_api_key
TWELVEDATA_API_KEY=your_twelvedata_api_key
MONGODB_URI=your_mongodb_connection_string
```

### 6. Run the Application

```bash
streamlit run project/app.py
```

> ⚠️ Replace `project/app.py` with the actual entry point file name if different.

---

## 📦 Dependencies

All Python dependencies are listed in [`requirements.txt`](./requirements.txt):

```
streamlit          # Web UI framework
plotly             # Interactive charts
pandas             # Data manipulation
yfinance           # Yahoo Finance market data
huggingface_hub    # HuggingFace model hub
google-search-results  # SerpAPI web search
python-dotenv      # Environment variable management
matplotlib         # Data visualization
groq               # Groq LLM API
reportlab          # PDF report generation
pymongo            # MongoDB client
openai             # OpenAI-compatible API client
twelvedata         # Real-time financial data API
requests           # HTTP requests
mcp                # Model Context Protocol
faiss-cpu          # Vector similarity search
sentence-transformers  # Text embeddings
langchain          # LLM agent framework
wikipedia          # Wikipedia data access
langchain-community    # Community LangChain integrations
langchain-huggingface  # HuggingFace LangChain integration
langchain-text-splitters  # Document chunking
```

---

## 🔑 API Keys Required

| Service | Purpose | Get Key |
|---|---|---|
| SerpAPI | Real-time web search | [serpapi.com](https://serpapi.com) |
| TwelveData | Financial market data | [twelvedata.com](https://twelvedata.com) |
| MongoDB | Data persistence | [mongodb.com](https://www.mongodb.com/cloud/atlas) |

---

## 📸 Usage

1. Launch the Streamlit app and open the dashboard in your browser (`http://localhost:8501`)
2. Enter a company name, industry, or topic in the query field
3. The system dispatches relevant agents to gather real-time data and knowledge base context
4. View AI-generated insights, trend analysis, and financial summaries on the dashboard
5. Export a full strategic intelligence report as a PDF

---

## 🎓 Internship Context

This project was developed as part of the **Infosys Springboard Artificial Intelligence Internship**. It demonstrates practical application of:

- Multi-agent AI system design
- Retrieval-Augmented Generation (RAG)
- Real-time data pipeline integration
- LLM orchestration with LangChain
- Full-stack AI application development with Streamlit

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Feel free to open a pull request or raise an issue.

---

## 📄 License

This project is developed for educational purposes as part of the Infosys Springboard AI Internship program.

---

## 👤 Author

**Ewan John Dennis**
[GitHub](https://github.com/Ewanjohndennis)
