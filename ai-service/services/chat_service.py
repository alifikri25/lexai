"""
Chat Service
Legal chat assistant using RAG + Groq LLaMA 3
"""
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from config import settings
from services.rag_pipeline import search_similar_chunks


def get_llm():
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.LLM_MODEL,
        temperature=0.3,
        max_tokens=2048,
    )


CHAT_PROMPT = """Kamu adalah LexAI, asisten hukum AI yang ahli dalam hukum Indonesia.
Kamu sedang membantu user memahami dokumen hukum yang telah mereka upload.

KONTEKS DOKUMEN (bagian yang relevan):
{context}

RIWAYAT PERCAKAPAN:
{chat_history}

PERTANYAAN USER:
{question}

INSTRUKSI:
1. Jawab pertanyaan berdasarkan konteks dokumen yang diberikan
2. Gunakan bahasa Indonesia yang mudah dipahami
3. Jika pertanyaan tidak bisa dijawab dari konteks, katakan bahwa informasi tersebut tidak ditemukan dalam dokumen
4. Jika ditanya tentang risiko, berikan analisis yang detail dan praktis
5. Berikan saran tindakan yang konkret jika diperlukan
6. Jangan mengada-ada — hanya jawab berdasarkan apa yang ada di dokumen

JAWABAN:"""


async def chat_with_document(
    message: str,
    document_id: str,
    chat_history: list = None,
) -> dict:
    """Chat about a document using RAG."""
    llm = get_llm()
    
    # Search for relevant chunks
    relevant_chunks = await search_similar_chunks(message, document_id, top_k=5)
    
    # Build context from chunks
    context = "\n\n".join([
        f"[Bagian {c['index'] + 1}]: {c['text']}"
        for c in relevant_chunks
    ]) if relevant_chunks else "Tidak ada konteks dokumen yang ditemukan."
    
    # Format chat history
    history_text = ""
    if chat_history:
        for msg in chat_history[-6:]:  # Last 6 messages
            role = "User" if msg.get("role") == "user" else "LexAI"
            history_text += f"{role}: {msg.get('content', '')}\n"
    
    prompt = ChatPromptTemplate.from_template(CHAT_PROMPT)
    chain = prompt | llm
    
    response = await chain.ainvoke({
        "context": context,
        "chat_history": history_text,
        "question": message,
    })
    
    sources = [c["text"][:100] + "..." for c in relevant_chunks[:3]]
    
    return {
        "response": response.content,
        "sources": sources,
    }
