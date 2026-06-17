import os
import re
import json
import tempfile
from datetime import datetime, timezone
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from app.models.schemas import ChatRequest, ChatResponse, IngestionResponse
from app.models.database import get_db, Message as MessageModel, Session as SessionModel, User as UserModel
from app.agent.agent import build_agent
from app.api.auth import get_current_user

router = APIRouter()

_agents: dict[str, any] = {}


def get_agent(session_id: str, user_id: int, initial_messages: list[tuple[str, str]] | None = None):
    key = f"{user_id}:{session_id}"
    if key not in _agents:
        _agents[key] = build_agent(session_id, initial_messages)
    return _agents[key]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session_obj = db.query(SessionModel).filter(
        SessionModel.id == req.session_id,
        SessionModel.user_id == current_user.id,
    ).first()
    if not session_obj:
        raise HTTPException(404, "Session not found")

    db_message = MessageModel(session_id=req.session_id, role="user", content=req.message)
    db.add(db_message)
    db.commit()

    if session_obj.title == "New Chat":
        session_obj.title = (req.message[:50] + "...") if len(req.message) > 50 else req.message
    session_obj.updated_at = datetime.now(timezone.utc)
    db.commit()

    loaded = db.query(MessageModel).filter(
        MessageModel.session_id == req.session_id,
    ).order_by(MessageModel.timestamp.desc()).limit(10).all()
    loaded.reverse()
    initial = [(m.role, m.content) for m in loaded]

    agent = get_agent(req.session_id, current_user.id, initial)
    result = agent.invoke({"input": req.message})

    response_text = result["output"]

    for step in result.get("intermediate_steps", []):
        action, output = step
        if hasattr(action, "tool") and "fetch_price_history" in action.tool:
            marker_match = re.search(r'\[CHART_REQUEST:\{[^}]+\}\]', output)
            if marker_match and marker_match.group(0) not in response_text:
                response_text += "\n\n" + marker_match.group(0)
            break

    db.add(MessageModel(session_id=req.session_id, role="assistant", content=response_text))
    db.commit()

    return ChatResponse(response=response_text)


@router.post("/ingest", response_model=IngestionResponse)
async def ingest(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File exceeds 10 MB limit")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
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


@router.get("/chart")
async def chart(ticker: str = Query(...), period: str = Query("6mo")):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            raise HTTPException(404, f"No data found for ticker '{ticker}'")

        close = hist["Close"]
        rsi = ta.rsi(close, length=14)
        sma20 = ta.sma(close, length=20)
        sma50 = ta.sma(close, length=50)
        macd = ta.macd(close)
        bb = ta.bbands(close, length=20, std=2)

        data = []
        for i in range(len(hist)):
            row: dict = {
                "date": hist.index[i].isoformat(),
                "open": round(float(hist.iloc[i]["Open"]), 2),
                "high": round(float(hist.iloc[i]["High"]), 2),
                "low": round(float(hist.iloc[i]["Low"]), 2),
                "close": round(float(hist.iloc[i]["Close"]), 2),
                "volume": int(hist.iloc[i]["Volume"]),
            }
            rv = rsi.iloc[i]
            row["rsi"] = round(float(rv), 2) if pd.notna(rv) else None
            sv20 = sma20.iloc[i]
            row["sma20"] = round(float(sv20), 2) if pd.notna(sv20) else None
            sv50 = sma50.iloc[i]
            row["sma50"] = round(float(sv50), 2) if pd.notna(sv50) else None
            if macd is not None and i < len(macd):
                row["macd"] = round(float(macd.iloc[i, 0]), 2) if pd.notna(macd.iloc[i, 0]) else None
                row["macd_signal"] = round(float(macd.iloc[i, 1]), 2) if pd.notna(macd.iloc[i, 1]) else None
                row["macd_hist"] = round(float(macd.iloc[i, 2]), 2) if pd.notna(macd.iloc[i, 2]) else None
            if bb is not None and i < len(bb):
                row["bb_upper"] = round(float(bb.iloc[i, 0]), 2) if pd.notna(bb.iloc[i, 0]) else None
                row["bb_middle"] = round(float(bb.iloc[i, 1]), 2) if pd.notna(bb.iloc[i, 1]) else None
                row["bb_lower"] = round(float(bb.iloc[i, 2]), 2) if pd.notna(bb.iloc[i, 2]) else None
            data.append(row)

        name = stock.info.get("longName", ticker)

        def clean(obj):
            if isinstance(obj, dict):
                return {k: clean(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [clean(v) for v in obj]
            if isinstance(obj, float) and obj != obj:
                return None
            return obj

        return clean({
            "type": "chart_data",
            "ticker": ticker,
            "name": name,
            "period": period,
            "data": data,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error fetching chart data: {e}")


@router.get("/health")
async def health():
    return {"status": "ok"}
