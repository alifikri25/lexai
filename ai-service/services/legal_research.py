"""
Legal Research Service (RAG-enhanced)
Tanya jawab berbasis Undang-Undang Indonesia dengan RAG dari knowledge base
dan referensi peraturan.go.id
"""
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from config import settings
from services.legal_knowledge_service import search_legal_knowledge


def get_llm():
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.LLM_MODEL,
        temperature=0.2,
        max_tokens=4096,
    )


LEGAL_RESEARCH_PROMPT = """Kamu adalah LexAI Legal Research Assistant, asisten riset hukum AI yang sangat ahli dalam hukum Indonesia.
Tugasmu adalah menjawab pertanyaan hukum berdasarkan konteks peraturan perundang-undangan yang diberikan.

KONTEKS PERATURAN (dari knowledge base):
{legal_context}

PANDUAN:
1. Jawab pertanyaan dengan AKURAT berdasarkan konteks peraturan di atas
2. Jika konteks relevan tersedia, kutip langsung dari konteks tersebut
3. Selalu sebutkan dasar hukum yang relevan (UU, PP, Perpres, Perda, dll) beserta nomor dan tahunnya
4. Untuk referensi peraturan, gunakan link https://peraturan.go.id sebagai sumber
5. Jelaskan dengan bahasa Indonesia yang mudah dipahami oleh non-praktisi hukum
6. Jika pertanyaan ambigu, minta klarifikasi
7. Jika konteks tidak mencukupi, sampaikan bahwa jawaban berdasarkan pengetahuan umum dan perlu verifikasi lebih lanjut
8. Berikan analisis yang komprehensif tapi terstruktur
9. Gunakan format yang jelas: gunakan numbering, bullet points, dan sub-heading

SUMBER REFERENSI UTAMA:
- Peraturan.go.id (JDIH Kemenkumham): https://peraturan.go.id
- JDIH Sekretariat Negara: https://jdih.setneg.go.id
- JDIH Mahkamah Agung: https://jdih.mahkamahagung.go.id

RIWAYAT PERCAKAPAN:
{chat_history}

PERTANYAAN USER:
{question}

FORMAT JAWABAN:
Berikan jawaban yang LENGKAP dan DETAIL dengan:
1. Ringkasan jawaban singkat (2-3 kalimat)
2. Penjelasan detail yang komprehensif dengan dasar hukum (kutip pasal-pasal spesifik dari konteks jika tersedia)
3. Analisis mendalam — jelaskan implikasi, konsekuensi, dan penerapan praktisnya
4. Referensi peraturan yang relevan (dengan link ke peraturan.go.id)
5. Catatan penting, disclaimer, atau saran tindak lanjut

PENTING: Berikan jawaban yang PANJANG dan MENYELURUH. Jangan ringkas. User membutuhkan jawaban yang komprehensif dan bisa dijadikan referensi.

JAWABAN:"""


async def legal_research_chat(
    message: str,
    chat_history: list = None,
) -> dict:
    """Process a legal research question using RAG from legal knowledge base."""
    llm = get_llm()

    # Search relevant chunks from legal knowledge base
    relevant_chunks = await search_legal_knowledge(message, top_k=8)

    # Format legal context from retrieved chunks
    if relevant_chunks:
        context_parts = []
        seen_sources = set()
        for i, chunk in enumerate(relevant_chunks):
            source = chunk.get("source", "Unknown")
            context_parts.append(
                f"[Sumber: {source}]\n{chunk['text']}"
            )
            seen_sources.add(source)
        legal_context = "\n\n---\n\n".join(context_parts)
        sources_list = list(seen_sources)
    else:
        legal_context = "(Tidak ada konteks spesifik dari knowledge base. Jawab berdasarkan pengetahuan umum hukum Indonesia.)"
        sources_list = []

    # Format chat history
    history_text = ""
    if chat_history:
        for msg in chat_history[-8:]:
            role = "User" if msg.get("role") == "user" else "LexAI"
            history_text += f"{role}: {msg.get('content', '')}\n"

    prompt = ChatPromptTemplate.from_template(LEGAL_RESEARCH_PROMPT)
    chain = prompt | llm

    response = await chain.ainvoke({
        "legal_context": legal_context,
        "chat_history": history_text,
        "question": message,
    })

    # Build references from chunks + extracted from response
    references = []
    added_sources = set()

    # Add references from RAG sources
    for chunk in relevant_chunks:
        source = chunk.get("source", "")
        if source and source not in added_sources:
            added_sources.add(source)
            references.append({
                "title": source,
                "source": "Knowledge Base (peraturan.go.id)",
                "url": "https://peraturan.go.id",
            })

    # Also extract any additional references from LLM response
    extra_refs = extract_references(response.content)
    for ref in extra_refs:
        if ref["title"] not in added_sources:
            added_sources.add(ref["title"])
            references.append(ref)

    return {
        "response": response.content,
        "references": references[:10],
        "rag_sources": sources_list,
    }


def extract_references(text: str) -> list:
    """Extract legal references from response text."""
    import re
    references = []

    patterns = [
        r'(UU(?:\s+(?:No\.?|Nomor))?\s*\d+\s*(?:Tahun\s*\d{4})?[^.;\n]*)',
        r'(PP(?:\s+(?:No\.?|Nomor))?\s*\d+\s*(?:Tahun\s*\d{4})?[^.;\n]*)',
        r'(Perpres(?:\s+(?:No\.?|Nomor))?\s*\d+\s*(?:Tahun\s*\d{4})?[^.;\n]*)',
        r'(Permen[A-Za-z]*(?:\s+(?:No\.?|Nomor))?\s*\d+\s*(?:Tahun\s*\d{4})?[^.;\n]*)',
        r'(KUH(?:Perdata|Pidana|AP)[^.;\n]*)',
        r'(Perda(?:\s+(?:No\.?|Nomor))?\s*\d+\s*(?:Tahun\s*\d{4})?[^.;\n]*)',
    ]

    seen = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean = match.strip().rstrip(",").strip()
            if clean and len(clean) > 5 and clean not in seen:
                seen.add(clean)
                references.append({
                    "title": clean[:120],
                    "source": "peraturan.go.id",
                    "url": "https://peraturan.go.id",
                })

    return references[:10]
