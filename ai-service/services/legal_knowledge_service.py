"""
Legal Knowledge Service
Parse UU PDFs, chunk, and embed into Supabase pgvector for RAG-based legal research
"""
import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from supabase import create_client
from config import settings
from services.document_parser import parse_pdf


# Reuse embedding model from rag_pipeline
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def get_supabase():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 200) -> list:
    """Split text into overlapping chunks optimized for legal text."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


def parse_embedding(embedding_data):
    """Parse embedding from various formats."""
    if isinstance(embedding_data, list):
        return np.array(embedding_data, dtype=np.float32)
    elif isinstance(embedding_data, str):
        cleaned = embedding_data.strip()
        if cleaned.startswith("[") and cleaned.endswith("]"):
            values = json.loads(cleaned)
            return np.array(values, dtype=np.float32)
    return None


async def embed_legal_pdf(file_path: str, source_name: str) -> int:
    """Parse a legal PDF, chunk it, create embeddings, and store in Supabase.
    
    Args:
        file_path: absolute path to the PDF file
        source_name: name of the regulation (e.g. "UU No. 13 Tahun 2003")
    
    Returns:
        Number of chunks created
    """
    model = get_embedding_model()
    supabase = get_supabase()

    # Read PDF file
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    # Parse PDF
    result = parse_pdf(file_bytes)
    text = result["text"]

    if not text.strip():
        raise ValueError(f"PDF kosong atau tidak bisa dibaca: {file_path}")

    # Delete existing chunks for this source (re-embed)
    supabase.table("legal_knowledge_base").delete().eq("source_name", source_name).execute()

    # Chunk text
    chunks = chunk_text(text)

    # Embed and store
    file_name = os.path.basename(file_path)
    for i, chunk in enumerate(chunks):
        embedding = model.encode(chunk).tolist()

        supabase.table("legal_knowledge_base").insert({
            "source_name": source_name,
            "source_file": file_name,
            "chunk_text": chunk,
            "chunk_index": i,
            "embedding": embedding,
        }).execute()

    return len(chunks)


async def embed_all_legal_pdfs(legal_data_dir: str = None) -> dict:
    """Embed all PDFs in the legal_data directory.
    
    Expected filename format: "UU No. 13 Tahun 2003 - Ketenagakerjaan.pdf"
    The source_name will be extracted from the filename (without .pdf).
    
    Returns:
        dict with results per file
    """
    if legal_data_dir is None:
        legal_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "legal_data")

    if not os.path.exists(legal_data_dir):
        raise ValueError(f"Folder tidak ditemukan: {legal_data_dir}")

    results = {}
    pdf_files = [f for f in os.listdir(legal_data_dir) if f.lower().endswith(".pdf")]

    if not pdf_files:
        raise ValueError(f"Tidak ada file PDF di folder: {legal_data_dir}")

    for pdf_file in pdf_files:
        file_path = os.path.join(legal_data_dir, pdf_file)
        source_name = pdf_file.replace(".pdf", "").replace(".PDF", "")

        try:
            num_chunks = await embed_legal_pdf(file_path, source_name)
            results[pdf_file] = {"status": "success", "chunks": num_chunks}
        except Exception as e:
            results[pdf_file] = {"status": "error", "error": str(e)}

    return results


async def search_legal_knowledge(query: str, top_k: int = 8) -> list:
    """Search legal knowledge base using vector similarity.
    
    Args:
        query: user's legal question
        top_k: number of most relevant chunks to return
    
    Returns:
        list of relevant chunks with source info and similarity score
    """
    model = get_embedding_model()
    supabase = get_supabase()

    # Create query embedding
    query_embedding = model.encode(query)
    query_vec = np.array(query_embedding, dtype=np.float32)

    # Fetch all chunks from legal knowledge base
    result = supabase.table("legal_knowledge_base")\
        .select("source_name, source_file, chunk_text, chunk_index, embedding")\
        .execute()

    if not result.data:
        return []

    # Compute cosine similarity
    scored_chunks = []
    for chunk in result.data:
        if chunk.get("embedding"):
            chunk_vec = parse_embedding(chunk["embedding"])
            if chunk_vec is not None:
                similarity = float(np.dot(query_vec, chunk_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec) + 1e-8
                ))
                scored_chunks.append({
                    "text": chunk["chunk_text"],
                    "source": chunk["source_name"],
                    "file": chunk.get("source_file", ""),
                    "index": chunk["chunk_index"],
                    "score": similarity,
                })

    # Sort by similarity and return top_k
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]


def get_knowledge_stats() -> dict:
    """Get stats about the legal knowledge base."""
    supabase = get_supabase()

    result = supabase.table("legal_knowledge_base")\
        .select("source_name, source_file")\
        .execute()

    if not result.data:
        return {"total_chunks": 0, "sources": []}

    sources = {}
    for row in result.data:
        name = row["source_name"]
        if name not in sources:
            sources[name] = {"name": name, "file": row.get("source_file", ""), "chunks": 0}
        sources[name]["chunks"] += 1

    return {
        "total_chunks": len(result.data),
        "sources": list(sources.values()),
    }
