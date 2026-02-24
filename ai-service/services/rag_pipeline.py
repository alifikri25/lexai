"""
RAG Pipeline Service
Embeddings + Vector Search using sentence-transformers and Supabase pgvector
"""
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from supabase import create_client
from config import settings

# Initialize embedding model (loaded once)
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def get_supabase():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list:
    """Split text into overlapping chunks."""
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP
    
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
    """Parse embedding from various formats (string, list, etc)."""
    if isinstance(embedding_data, list):
        return np.array(embedding_data, dtype=np.float32)
    elif isinstance(embedding_data, str):
        # pgvector returns embeddings as string like "[0.1,0.2,...]"
        cleaned = embedding_data.strip()
        if cleaned.startswith("[") and cleaned.endswith("]"):
            values = json.loads(cleaned)
            return np.array(values, dtype=np.float32)
    return None


async def create_embeddings(text: str, document_id: str) -> int:
    """Create embeddings for document chunks and store in Supabase pgvector."""
    model = get_embedding_model()
    supabase = get_supabase()
    
    # Split text into chunks
    chunks = chunk_text(text)
    
    # Delete existing chunks for this document
    supabase.table("document_chunks").delete().eq("document_id", document_id).execute()
    
    # Create embeddings and store
    for i, chunk in enumerate(chunks):
        embedding = model.encode(chunk).tolist()
        
        supabase.table("document_chunks").insert({
            "document_id": document_id,
            "chunk_text": chunk,
            "chunk_index": i,
            "embedding": embedding,
        }).execute()
    
    return len(chunks)


async def search_similar_chunks(query: str, document_id: str, top_k: int = 5) -> list:
    """Search for similar chunks using vector similarity."""
    model = get_embedding_model()
    supabase = get_supabase()
    
    # Create query embedding
    query_embedding = model.encode(query)
    query_vec = np.array(query_embedding, dtype=np.float32)
    
    # Fetch all chunks for this document
    result = supabase.table("document_chunks")\
        .select("chunk_text, chunk_index, embedding")\
        .eq("document_id", document_id)\
        .execute()
    
    if not result.data:
        return []
    
    # Compute cosine similarity
    scored_chunks = []
    for chunk in result.data:
        if chunk.get("embedding"):
            chunk_vec = parse_embedding(chunk["embedding"])
            if chunk_vec is not None:
                similarity = np.dot(query_vec, chunk_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec) + 1e-8
                )
                scored_chunks.append({
                    "text": chunk["chunk_text"],
                    "index": chunk["chunk_index"],
                    "score": float(similarity),
                })
    
    # Sort by similarity and return top_k
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]
