"""
Contract Drafter Service
Generate draft kontrak hukum Indonesia dari template menggunakan Groq LLaMA 3
"""
import json
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from config import settings


# ── Contract Templates ──────────────────────────────────────────────
CONTRACT_TEMPLATES = [
    {
        "id": "perjanjian-kerja",
        "name": "Perjanjian Kerja",
        "icon": "👔",
        "description": "Kontrak kerja antara perusahaan dan karyawan sesuai UU Ketenagakerjaan No. 13/2003",
        "fields": [
            {"key": "company_name", "label": "Nama Perusahaan", "type": "text", "required": True},
            {"key": "company_address", "label": "Alamat Perusahaan", "type": "text", "required": True},
            {"key": "company_rep", "label": "Nama Perwakilan Perusahaan", "type": "text", "required": True},
            {"key": "company_rep_position", "label": "Jabatan Perwakilan", "type": "text", "required": True},
            {"key": "employee_name", "label": "Nama Karyawan", "type": "text", "required": True},
            {"key": "employee_address", "label": "Alamat Karyawan", "type": "text", "required": True},
            {"key": "employee_nik", "label": "NIK Karyawan", "type": "text", "required": True},
            {"key": "position", "label": "Jabatan/Posisi", "type": "text", "required": True},
            {"key": "salary", "label": "Gaji Bulanan (Rp)", "type": "text", "required": True},
            {"key": "start_date", "label": "Tanggal Mulai Kerja", "type": "text", "required": True},
            {"key": "contract_duration", "label": "Durasi Kontrak (bulan)", "type": "text", "required": False},
            {"key": "probation_period", "label": "Masa Percobaan (bulan)", "type": "text", "required": False},
            {"key": "work_hours", "label": "Jam Kerja per Minggu", "type": "text", "required": False},
            {"key": "additional_terms", "label": "Ketentuan Tambahan", "type": "textarea", "required": False},
        ],
    },
    {
        "id": "perjanjian-sewa",
        "name": "Perjanjian Sewa Menyewa",
        "icon": "🏠",
        "description": "Kontrak sewa properti (rumah, ruko, apartemen) sesuai KUHPerdata Pasal 1548-1600",
        "fields": [
            {"key": "landlord_name", "label": "Nama Pemilik", "type": "text", "required": True},
            {"key": "landlord_address", "label": "Alamat Pemilik", "type": "text", "required": True},
            {"key": "landlord_nik", "label": "NIK Pemilik", "type": "text", "required": True},
            {"key": "tenant_name", "label": "Nama Penyewa", "type": "text", "required": True},
            {"key": "tenant_address", "label": "Alamat Penyewa", "type": "text", "required": True},
            {"key": "tenant_nik", "label": "NIK Penyewa", "type": "text", "required": True},
            {"key": "property_type", "label": "Jenis Properti", "type": "text", "required": True},
            {"key": "property_address", "label": "Alamat Properti", "type": "text", "required": True},
            {"key": "rental_price", "label": "Harga Sewa (Rp/bulan atau /tahun)", "type": "text", "required": True},
            {"key": "rental_duration", "label": "Durasi Sewa", "type": "text", "required": True},
            {"key": "start_date", "label": "Tanggal Mulai Sewa", "type": "text", "required": True},
            {"key": "deposit", "label": "Uang Deposit/Jaminan (Rp)", "type": "text", "required": False},
            {"key": "additional_terms", "label": "Ketentuan Tambahan", "type": "textarea", "required": False},
        ],
    },
    {
        "id": "perjanjian-jual-beli",
        "name": "Perjanjian Jual Beli",
        "icon": "🤝",
        "description": "Kontrak jual beli barang/properti sesuai KUHPerdata Pasal 1457-1540",
        "fields": [
            {"key": "seller_name", "label": "Nama Penjual", "type": "text", "required": True},
            {"key": "seller_address", "label": "Alamat Penjual", "type": "text", "required": True},
            {"key": "seller_nik", "label": "NIK Penjual", "type": "text", "required": True},
            {"key": "buyer_name", "label": "Nama Pembeli", "type": "text", "required": True},
            {"key": "buyer_address", "label": "Alamat Pembeli", "type": "text", "required": True},
            {"key": "buyer_nik", "label": "NIK Pembeli", "type": "text", "required": True},
            {"key": "object_description", "label": "Deskripsi Objek Jual Beli", "type": "textarea", "required": True},
            {"key": "price", "label": "Harga Jual (Rp)", "type": "text", "required": True},
            {"key": "payment_method", "label": "Metode Pembayaran", "type": "text", "required": True},
            {"key": "delivery_date", "label": "Tanggal Serah Terima", "type": "text", "required": False},
            {"key": "warranty", "label": "Garansi/Jaminan", "type": "text", "required": False},
            {"key": "additional_terms", "label": "Ketentuan Tambahan", "type": "textarea", "required": False},
        ],
    },
    {
        "id": "nda",
        "name": "Non-Disclosure Agreement (NDA)",
        "icon": "🔒",
        "description": "Perjanjian kerahasiaan informasi antara dua pihak",
        "fields": [
            {"key": "discloser_name", "label": "Nama Pihak Pengungkap", "type": "text", "required": True},
            {"key": "discloser_address", "label": "Alamat Pihak Pengungkap", "type": "text", "required": True},
            {"key": "receiver_name", "label": "Nama Pihak Penerima", "type": "text", "required": True},
            {"key": "receiver_address", "label": "Alamat Pihak Penerima", "type": "text", "required": True},
            {"key": "confidential_info", "label": "Deskripsi Informasi Rahasia", "type": "textarea", "required": True},
            {"key": "purpose", "label": "Tujuan Pengungkapan", "type": "text", "required": True},
            {"key": "duration", "label": "Durasi Kerahasiaan", "type": "text", "required": True},
            {"key": "penalty", "label": "Sanksi Pelanggaran", "type": "text", "required": False},
            {"key": "additional_terms", "label": "Ketentuan Tambahan", "type": "textarea", "required": False},
        ],
    },
    {
        "id": "perjanjian-kerjasama",
        "name": "Perjanjian Kerjasama",
        "icon": "📋",
        "description": "Kontrak kerjasama bisnis (MoU/PKS) antara dua pihak atau lebih",
        "fields": [
            {"key": "party1_name", "label": "Nama Pihak Pertama", "type": "text", "required": True},
            {"key": "party1_address", "label": "Alamat Pihak Pertama", "type": "text", "required": True},
            {"key": "party1_rep", "label": "Perwakilan Pihak Pertama", "type": "text", "required": True},
            {"key": "party2_name", "label": "Nama Pihak Kedua", "type": "text", "required": True},
            {"key": "party2_address", "label": "Alamat Pihak Kedua", "type": "text", "required": True},
            {"key": "party2_rep", "label": "Perwakilan Pihak Kedua", "type": "text", "required": True},
            {"key": "cooperation_scope", "label": "Ruang Lingkup Kerjasama", "type": "textarea", "required": True},
            {"key": "rights_obligations", "label": "Hak dan Kewajiban", "type": "textarea", "required": True},
            {"key": "duration", "label": "Durasi Kerjasama", "type": "text", "required": True},
            {"key": "profit_sharing", "label": "Pembagian Keuntungan", "type": "text", "required": False},
            {"key": "termination_clause", "label": "Klausul Pemutusan", "type": "textarea", "required": False},
            {"key": "additional_terms", "label": "Ketentuan Tambahan", "type": "textarea", "required": False},
        ],
    },
]


def get_llm():
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.LLM_MODEL,
        temperature=0.2,
        max_tokens=4096,
    )


def get_templates():
    """Return list of available contract templates (without field details for listing)."""
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "icon": t["icon"],
            "description": t["description"],
        }
        for t in CONTRACT_TEMPLATES
    ]


def get_template_detail(template_id: str):
    """Return full template detail including fields."""
    for t in CONTRACT_TEMPLATES:
        if t["id"] == template_id:
            return t
    return None


DRAFT_PROMPT = """Kamu adalah AI ahli hukum Indonesia yang berpengalaman dalam menyusun kontrak.
Tugasmu adalah membuat draft kontrak yang lengkap, profesional, dan sesuai hukum Indonesia.

JENIS KONTRAK: {contract_type}
DESKRIPSI: {contract_description}

DATA YANG DIBERIKAN USER:
{form_data}

INSTRUKSI:
1. Buat draft kontrak LENGKAP dalam bahasa Indonesia yang formal dan profesional
2. Gunakan format kontrak standar Indonesia dengan:
   - Judul kontrak
   - Nomor kontrak (gunakan placeholder: ____/___/____) 
   - Tanggal pembuatan
   - Identitas para pihak (PIHAK PERTAMA dan PIHAK KEDUA)
   - Pasal-pasal yang terstruktur dan bernomor
   - Klausul standar: ruang lingkup, hak & kewajiban, jangka waktu, pembayaran, force majeure, penyelesaian sengketa, dll
   - Bagian tanda tangan
3. Pastikan sesuai dengan peraturan perundang-undangan Indonesia yang berlaku
4. Jika ada data yang kosong, gunakan placeholder [.....] 
5. Gunakan bahasa hukum yang benar tapi tetap mudah dipahami
6. Sertakan pasal tentang penyelesaian sengketa melalui musyawarah dan pengadilan negeri
7. Sertakan referensi UU yang relevan di bagian yang sesuai

Buat draft kontrak yang lengkap dan siap pakai:"""


async def generate_contract_draft(template_id: str, form_data: dict) -> dict:
    """Generate a contract draft using LLM based on template and form data."""
    template = get_template_detail(template_id)
    if not template:
        raise ValueError(f"Template tidak ditemukan: {template_id}")

    llm = get_llm()

    # Format form data for the prompt
    form_text = "\n".join([
        f"- {field['label']}: {form_data.get(field['key'], '[belum diisi]')}"
        for field in template["fields"]
        if form_data.get(field["key"])
    ])

    prompt = ChatPromptTemplate.from_template(DRAFT_PROMPT)
    chain = prompt | llm

    response = await chain.ainvoke({
        "contract_type": template["name"],
        "contract_description": template["description"],
        "form_data": form_text,
    })

    return {
        "template_id": template_id,
        "template_name": template["name"],
        "draft_content": response.content,
        "form_data": form_data,
    }
