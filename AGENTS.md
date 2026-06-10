# AGENTS.md — Financial Research Agent

LangChain-based conversational agent. FastAPI backend, Vite+React frontend, ReAct agent with 4 tools, RAG over PDFs.

## Dev commands

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt  # after any dep change
python -m app.main              # uvicorn on :8000

# Frontend
cd frontend
npm install                      # after any dep change
npm run dev                      # vite on :5173, proxies /api to :8000
npm run build                    # tsc + vite build
```

## Project structure

```
backend/app/
├── agent/          # agent.py (ReAct setup), tools.py (4 tools), prompt.py
├── rag/            # ingest.py (PDF → ChromaDB), retriever.py (query ChromaDB)
├── api/routes.py   # POST /api/chat, POST /api/ingest, GET /api/health
├── models/schemas.py  # ChatRequest/Response, AnalysisReport, IngestionResponse
└── main.py         # FastAPI app + CORS
frontend/src/
├── api/client.ts   # chat() + ingest() fetch wrappers
└── components/     # ChatView (markdown-rendered chat), App.tsx (state + file upload)
```

## Architecture

```
React → /api/chat → FastAPI → ReAct Agent
  ├── Tool: yfinance + pandas-ta (price, RSI, SMA)
  ├── Tool: DuckDuckGo search (news)
  ├── Tool: ChromaDB retriever (RAG on uploaded PDFs)
  └── LLM: Groq llama3-70b-8192
```

## Key constraints

- **100% free**: Groq API key, HuggingFace embeddings (local), ChromaDB (local), yfinance, DuckDuckGo
- **No OpenAI, no Pinecone, no paid services**
- `backend/.env` must contain `GROQ_API_KEY=gsk_...` (gitignored)
- ChromaDB data lives in `backend/chromadb_storage/` (gitignored)
- PDF uploads: max 10 MB, `.pdf` only
- CORS: locked to `localhost:5173` and `localhost:4173`

## RAG pipeline

1. POST `/api/ingest` with a PDF file
2. Text split into 500-char chunks (50 overlap)
3. Embedded with `sentence-transformers/all-MiniLM-L6-v2`
4. Stored in local ChromaDB (persistent)
5. Retriever returns top-3 chunks per query

## Deployment (Render)

- Backend: Web Service, persistent disk at `/app/chromadb_storage`, env `GROQ_API_KEY`
- Frontend: Static Site, build command `npm install && npm run build`, publish `dist`

## Tests

None yet. No test runner configured.
