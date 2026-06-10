# Financial Research Agent

A conversational AI agent that fetches live market data, searches financial news, queries ingested documents (RAG), and delivers structured analysis reports — all through a chat interface.

Built with **LangChain**, **FastAPI**, **React**, and **100% free** APIs.

## Architecture

```
User → React UI → FastAPI → ReAct Agent
                              ├── Price + Indicators (yfinance + pandas-ta)
                              ├── Web Search (DuckDuckGo)
                              ├── RAG (ChromaDB + HF Embeddings)
                              └── LLM (Groq — llama3-70b)
```

## Features

| Tool | What it does | Free Service |
|---|---|---|
| Live price + RSI/SMA | Fetches price, RSI(14), SMA(20/50), volume | yfinance |
| Financial news search | Searches web for latest news | DuckDuckGo |
| Document RAG | Ingests PDFs, retrieves relevant chunks | ChromaDB + HF |
| Analysis report | Structured bullish/bearish verdict | Groq LLM |

## Tech Stack

- **LLM:** Groq (llama3-70b-8192) — fast, free inference
- **Agent:** LangChain ReAct with ConversationBufferWindowMemory
- **RAG:** ChromaDB (persistent) + sentence-transformers/all-MiniLM-L6-v2
- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** Vite + React + TypeScript
- **Deployment:** Render (free tier)

## Project Structure

```
backend/
├── app/
│   ├── agent/          # ReAct agent, tools, prompts
│   ├── rag/            # PDF ingestion + ChromaDB retriever
│   ├── api/            # FastAPI routes
│   ├── models/         # Pydantic schemas
│   └── main.py         # FastAPI entrypoint
├── chromadb_storage/   # Persistent vector store (gitignored)
├── data/documents/     # PDFs to ingest (gitignored)
├── requirements.txt
└── .env                # GROQ_API_KEY here
frontend/
├── src/
│   ├── api/client.ts   # Backend fetch wrapper
│   ├── components/     # ChatView, ReportCard
│   └── App.tsx
├── package.json
└── vite.config.ts
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 22+
- A free Groq API key from [console.groq.com](https://console.groq.com)

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
cp .env.example .env
# Edit .env — paste your GROQ_API_KEY

python -m app.main
# → http://localhost:8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### 3. Use It

Open http://localhost:5173 and try:

- `What's AAPL looking like today?`
- `Search for news about interest rate cuts`
- Upload a PDF trading strategy, then: `What does my strategy say about stop losses?`
- `Generate a full analysis report for MSFT`

## Deployment

Deploy on **Render** (free tier, no credit card needed):

1. **Backend:** Create a Web Service → point at `backend/` → set build command to `pip install -r requirements.txt` → start command to `uvicorn app.main:app --host 0.0.0.0 --port 10000` → add `GROQ_API_KEY` as env var → add a **Persistent Disk** (1 GB) mounted at `/app/chromadb_storage`
2. **Frontend:** Create a Static Site → point at `frontend/` → build command `npm install && npm run build` → publish directory `dist`

## License

MIT
