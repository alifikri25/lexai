# LexAI — AI Copilot untuk Praktisi Hukum Indonesia

![LexAI](https://img.shields.io/badge/LexAI-AI%20Legal%20Assistant-6c5ce7?style=for-the-badge)

AI Copilot yang membantu praktisi hukum Indonesia menganalisis dokumen hukum secara otomatis.

## ✨ Fitur

- 🔐 **Auth System** — Register & Login dengan Supabase Auth
- 📄 **Document Analyzer** — Upload PDF/DOCX, AI ekstrak klausul & deteksi risiko otomatis
- 💬 **Legal Chat** — Tanya jawab AI tentang isi dokumen (RAG-powered)
- 📋 **Riwayat Dokumen** — Simpan & buka ulang hasil analisis
- 📥 **Export PDF** — Ekspor hasil analisis ke laporan PDF profesional

## 🏗️ Tech Stack

| Layer | Teknologi |
|-------|-----------|
| Frontend | Next.js 14 + TailwindCSS |
| Backend | Node.js + Express |
| AI Service | Python + FastAPI + LangChain |
| LLM | Groq API (LLaMA 3.3 70B) |
| Database | PostgreSQL (Supabase) |
| Vector DB | pgvector (Supabase) |
| Storage | Supabase Storage |
| Auth | Supabase Auth |

## 🚀 Setup & Run

### Prerequisites
- Node.js 18+
- Python 3.10+
- Akun Supabase (gratis)
- Akun Groq (gratis)

### 1. Setup Database (Supabase)
1. Buka [Supabase Dashboard](https://supabase.com/dashboard)
2. Buka project LexAI → **SQL Editor**
3. Copy-paste isi file `supabase_schema.sql` → **Run**
4. Buka **Storage** → Create bucket "documents" (public: OFF)

### 2. Setup Environment
Edit file `.env` di root project, masukkan Groq API key:
```
GROQ_API_KEY=gsk_your_key_here
```

### 3. Run Backend
```bash
cd backend
npm install
npm run dev
```

### 4. Run AI Service
```bash
cd ai-service
pip install -r requirements.txt
python main.py
```

### 5. Run Frontend
```bash
cd frontend
npm install
npm run dev
```

### 6. Buka Aplikasi
Buka `http://localhost:3000` di browser.

## 📁 Struktur Project

```
lexai/
├── frontend/          # Next.js 14 + TailwindCSS
├── backend/           # Node.js + Express
├── ai-service/        # Python + FastAPI + LangChain
├── supabase_schema.sql
├── docker-compose.yml
└── .env
```

## 📄 License
MIT — Dibuat untuk proyek skripsi.
