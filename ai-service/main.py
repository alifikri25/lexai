"""
LexAI AI Service — FastAPI Entry Point
Provides document parsing, analysis, RAG chat, PDF export,
contract drafting, and legal research endpoints.
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
    ContractDraftRequest, ContractDraftResponse,
    ContractExportRequest,
    LegalResearchRequest, LegalResearchResponse,
)
from services.document_parser import parse_document
from services.document_analyzer import analyze_document
from services.rag_pipeline import create_embeddings
from services.chat_service import chat_with_document
from services.export_service import create_analysis_pdf
from services.contract_drafter import get_templates, get_template_detail, generate_contract_draft
from services.contract_export import export_contract_docx, export_contract_pdf
from services.legal_research import legal_research_chat
from services.legal_knowledge_service import embed_legal_pdf, embed_all_legal_pdfs, get_knowledge_stats

app = FastAPI(
    title="LexAI AI Service",
    description="AI Service untuk analisis dokumen hukum Indonesia",
    version="2.0.0",
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


# ── Contract Drafting Endpoints ──────────────────────────────────────

@app.get("/api/contracts/templates")
async def list_templates():
    """Get list of available contract templates."""
    return {"templates": get_templates()}


@app.get("/api/contracts/templates/{template_id}")
async def get_template(template_id: str):
    """Get full detail of a contract template including form fields."""
    template = get_template_detail(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template tidak ditemukan")
    return {"template": template}


@app.post("/api/contracts/draft", response_model=ContractDraftResponse)
async def draft_contract(request: ContractDraftRequest):
    """Generate contract draft from template and form data."""
    try:
        result = await generate_contract_draft(
            template_id=request.template_id,
            form_data=request.form_data,
        )
        return ContractDraftResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membuat draft kontrak: {str(e)}")


@app.post("/api/contracts/export")
async def export_contract(request: ContractExportRequest):
    """Export contract draft to Word or PDF."""
    try:
        if request.format.lower() == "docx":
            file_bytes = export_contract_docx(request.title, request.content)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"LexAI_Kontrak_{request.title}.docx"
        elif request.format.lower() == "pdf":
            file_bytes = export_contract_pdf(request.title, request.content)
            media_type = "application/pdf"
            filename = f"LexAI_Kontrak_{request.title}.pdf"
        else:
            raise HTTPException(status_code=400, detail="Format harus 'pdf' atau 'docx'")

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengexport kontrak: {str(e)}")


# ── Legal Research Endpoints ─────────────────────────────────────────

@app.post("/api/legal-research", response_model=LegalResearchResponse)
async def legal_research(request: LegalResearchRequest):
    """Legal research Q&A based on Indonesian law (RAG-enhanced)."""
    try:
        result = await legal_research_chat(
            message=request.message,
            chat_history=request.chat_history,
        )
        return LegalResearchResponse(
            response=result["response"],
            references=result.get("references", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses riset hukum: {str(e)}")


@app.get("/api/legal-research/knowledge-stats")
async def knowledge_stats():
    """Get stats about the legal knowledge base."""
    return get_knowledge_stats()


@app.post("/api/legal-research/embed-all")
async def embed_all_legal_docs():
    """Embed all PDF files in the legal_data folder into the knowledge base."""
    try:
        results = await embed_all_legal_pdfs()
        return {"message": "Embedding selesai", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal embedding: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
