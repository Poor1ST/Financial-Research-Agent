import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, IngestionResponse
from app.agent.agent import build_agent

router = APIRouter()

# session -> agent executor cache
_agents: dict[str, any] = {}


def get_agent(session_id: str):
    if session_id not in _agents:
        _agents[session_id] = build_agent(session_id)
    return _agents[session_id]


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    agent = get_agent(req.session_id)
    result = agent.invoke({"input": req.message})
    return ChatResponse(response=result["output"])


@router.post("/ingest", response_model=IngestionResponse)
async def ingest(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            os.unlink(tmp.name)
            raise HTTPException(400, "File exceeds 10 MB limit")
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from app.rag.ingest import ingest_pdf
        count = ingest_pdf(tmp_path)
        return IngestionResponse(
            status="ok",
            chunks_ingested=count,
            filename=file.filename,
        )
    finally:
        os.unlink(tmp_path)


@router.get("/health")
async def health():
    return {"status": "ok"}
