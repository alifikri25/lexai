"""
LexAI AI Service — FastAPI Entry Point
Provides document parsing, analysis, RAG chat, and PDF export endpoints.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import uvicorn

from models.schemas import (
    ParseRequest, ParseResponse,
    AnalyzeRequest, AnalyzeResponse,
    EmbedRequest,
    ChatRequest, ChatResponse,
    ExportRequest,
)
from services.document_parser import parse_document
from services.document_analyzer import analyze_document
from services.rag_pipeline import create_embeddings
from services.chat_service import chat_with_document
from services.export_service import create_analysis_pdf

app = FastAPI(
    title="LexAI AI Service",
    description="AI Service untuk analisis dokumen hukum Indonesia",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "lexai-ai-service"}


@app.post("/api/parse", response_model=ParseResponse)
async def parse_doc(request: ParseRequest):
    """Parse PDF/DOCX document and extract text."""
    try:
        result = parse_document(request.file_base64, request.file_type)
        return ParseResponse(
            text=result["text"],
            pages=result["pages"],
            file_name=request.file_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal parsing dokumen: {str(e)}")


@app.post("/api/analyze")
async def analyze_doc(request: AnalyzeRequest):
    """Analyze legal document — extract clauses, detect risks, summarize."""
    try:
        result = await analyze_document(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis dokumen: {str(e)}")


@app.post("/api/embed")
async def embed_doc(request: EmbedRequest):
    """Create embeddings for document chunks and store in pgvector."""
    try:
        num_chunks = await create_embeddings(request.text, request.document_id)
        return {"message": f"Berhasil membuat {num_chunks} embeddings", "chunks": num_chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membuat embeddings: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat about a document using RAG."""
    try:
        result = await chat_with_document(
            message=request.message,
            document_id=request.document_id,
            chat_history=request.chat_history,
        )
        return ChatResponse(
            response=result["response"],
            sources=result.get("sources", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses chat: {str(e)}")


@app.post("/api/export-pdf")
async def export_pdf(request: ExportRequest):
    """Generate PDF report from analysis results."""
    try:
        pdf_bytes = create_analysis_pdf(
            title=request.title,
            summary=request.summary,
            clauses=request.clauses,
            risk_score=request.risk_score,
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=LexAI_Analisis_{request.document_id}.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membuat PDF: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
