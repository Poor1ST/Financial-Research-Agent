from datetime import datetime
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


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class SessionCreate(BaseModel):
    pass


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    timestamp: datetime
    model_config = {"from_attributes": True}
