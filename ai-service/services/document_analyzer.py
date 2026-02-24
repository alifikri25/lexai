"""
Document Analyzer Service
Uses Groq LLaMA 3 to analyze legal documents — extract clauses, detect risks, generate summary
"""
import json
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from config import settings


def get_llm():
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.LLM_MODEL,
        temperature=0.1,
        max_tokens=4096,
    )


ANALYSIS_PROMPT = """Kamu adalah AI ahli hukum Indonesia yang sangat berpengalaman. 
Tugasmu adalah menganalisis dokumen hukum berikut secara menyeluruh.

DOKUMEN:
{document_text}

Berikan analisis dalam format JSON yang VALID dengan struktur berikut:
{{
  "summary": "Ringkasan dokumen dalam 3-5 paragraf bahasa Indonesia yang mudah dipahami",
  "clauses": [
    {{
      "number": 1,
      "title": "Judul/Nama Klausul",
      "text": "Kutipan teks klausul dari dokumen (max 200 kata)",
      "risk_level": "high/medium/low",
      "explanation": "Penjelasan risiko klausul ini dalam bahasa sederhana"
    }}
  ],
  "risk_score": 50
}}

PANDUAN RISK LEVEL:
- "high" (MERAH): Klausul yang sangat merugikan salah satu pihak, tidak adil, berpotensi melanggar hukum, penalti berlebihan, pembatasan hak yang tidak wajar
- "medium" (KUNING): Klausul yang ambigu, perlu klarifikasi, standar tapi perlu perhatian khusus  
- "low" (HIJAU): Klausul standar, adil untuk semua pihak, sesuai praktik hukum yang baik

RISK SCORE: Angka 0-100 yang menunjukkan tingkat risiko keseluruhan dokumen (0=aman, 100=sangat berisiko)

PENTING:
- Analisis SEMUA klausul penting dalam dokumen
- Gunakan bahasa Indonesia yang mudah dipahami oleh non-praktisi hukum
- Berikan penjelasan yang spesifik dan actionable
- Pastikan output adalah JSON yang valid, tanpa teks tambahan di luar JSON
"""


async def analyze_document(text: str) -> dict:
    """Analyze a legal document using Groq LLaMA 3."""
    llm = get_llm()
    
    # Truncate text if too long (Groq has token limits)
    max_chars = 12000
    truncated_text = text[:max_chars] if len(text) > max_chars else text
    
    prompt = ChatPromptTemplate.from_template(ANALYSIS_PROMPT)
    chain = prompt | llm
    
    response = await chain.ainvoke({"document_text": truncated_text})
    
    # Parse the JSON response
    response_text = response.content.strip()
    
    # Try to extract JSON from the response
    try:
        # Try direct JSON parse
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            result = json.loads(response_text[start_idx:end_idx])
        else:
            # Fallback
            result = {
                "summary": "Gagal menganalisis dokumen. Silakan coba lagi.",
                "clauses": [],
                "risk_score": 0,
            }
    
    return {
        "summary": result.get("summary", ""),
        "clauses": result.get("clauses", []),
        "risk_score": result.get("risk_score", 0),
    }
