from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str


class AnalysisReport(BaseModel):
    asset: str = Field(description="Ticker or asset name")
    direction: str = Field(description="bullish, bearish, or neutral")
    confidence: str = Field(description="high, medium, or low")
    key_levels: list[float] = Field(description="Support and resistance levels")
    technical_summary: str = Field(description="Technical analysis summary")
    fundamental_summary: str = Field(description="News/fundamental context")
    risk_factors: list[str] = Field(description="Key risks")
    conclusion: str = Field(description="Overall verdict")


class IngestionResponse(BaseModel):
    status: str
    chunks_ingested: int
    filename: str
