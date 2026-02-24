from pydantic import BaseModel
from typing import List, Optional


class ParseRequest(BaseModel):
    file_base64: str
    file_type: str  # "pdf" or "docx"
    file_name: str


class ParseResponse(BaseModel):
    text: str
    pages: int
    file_name: str


class AnalyzeRequest(BaseModel):
    text: str
    document_id: str


class Clause(BaseModel):
    number: int
    title: str
    text: str
    risk_level: str  # "high", "medium", "low"
    explanation: str


class AnalyzeResponse(BaseModel):
    summary: str
    clauses: List[Clause]
    risk_score: int  # 0-100


class EmbedRequest(BaseModel):
    text: str
    document_id: str


class ChatRequest(BaseModel):
    message: str
    document_id: str
    chat_history: Optional[List[dict]] = []


class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = []


class ExportRequest(BaseModel):
    document_id: str
    title: str
    summary: str
    clauses: List[dict]
    risk_score: int
