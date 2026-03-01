"""
Embed Legal Data Script
Run this script to embed all PDF UU files into Supabase pgvector.

Usage:
    cd d:\lexAI\ai-service
    python embed_legal_data.py

Make sure:
1. PDF files are in the 'legal_data' folder  
2. The 'legal_knowledge_base' table exists in Supabase
3. Your .env file is configured properly
"""
import asyncio
import os
import sys

# Add parent dir to path
sys.path.insert(0, os.path.dirname(__file__))

from services.legal_knowledge_service import embed_all_legal_pdfs, get_knowledge_stats


async def main():
    legal_data_dir = os.path.join(os.path.dirname(__file__), "legal_data")

    # Check folder exists
    if not os.path.exists(legal_data_dir):
        print(f"❌ Folder tidak ditemukan: {legal_data_dir}")
        print(f"   Buat folder dan taruh PDF UU di dalamnya.")
        return

    # Check PDF files
    pdfs = [f for f in os.listdir(legal_data_dir) if f.lower().endswith(".pdf")]
    if not pdfs:
        print(f"❌ Tidak ada file PDF di: {legal_data_dir}")
        print(f"   Download PDF UU dari https://peraturan.go.id dan taruh di folder tersebut.")
        return

    print(f"📚 Ditemukan {len(pdfs)} file PDF:")
    for f in pdfs:
        print(f"   - {f}")

    print(f"\n⏳ Memulai proses embedding...")
    print(f"   (Proses ini bisa memakan waktu beberapa menit)\n")

    try:
        results = await embed_all_legal_pdfs(legal_data_dir)

        print("\n" + "=" * 60)
        print("📊 HASIL EMBEDDING")
        print("=" * 60)

        for filename, result in results.items():
            if result["status"] == "success":
                print(f"✅ {filename} → {result['chunks']} chunks")
            else:
                print(f"❌ {filename} → Error: {result['error']}")

        # Show stats
        stats = get_knowledge_stats()
        print(f"\n📈 Total chunks di knowledge base: {stats['total_chunks']}")
        print(f"📁 Total sumber: {len(stats['sources'])}")
        print("\n✅ Selesai! Knowledge base siap digunakan untuk Legal Research.")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
