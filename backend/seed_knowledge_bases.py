"""
Script Seeder untuk Knowledge Bases dengan Embedding Vector Gemini API (768 Dimensi).
Format input teks embedding:
\"\"\"
Keyword: {keyword_triggers}
Judul: {title}
Konten: {content}
\"\"\"
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List
import httpx
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

for env_candidate in [BASE_DIR / "dev.env", ROOT_DIR / "dev.env", BASE_DIR / ".env", ROOT_DIR / ".env"]:
    if env_candidate.exists():
        load_dotenv(dotenv_path=env_candidate, override=False)
        break

DB_PATH = BASE_DIR / "database" / "database.db"

RAW_KNOWLEDGE_DATA: List[Dict[str, str]] = [
    {
        "category": "rekening",
        "keyword_triggers": "rekening, transfer, bayar, bca, mandiri, bri",
        "title": "Rekening Pembayaran",
        "content": (
            "Data rekening pembayaran resmi untuk keperluan simulasi:\n"
            "BCA: 111-222-333 a.n. PT Contoh Digital.\n"
            "Gunakan hanya data simulasi ini."
        )
    },
    {
        "category": "layanan",
        "keyword_triggers": "seo, paket seo, ranking google, search engine",
        "title": "Informasi Layanan SEO",
        "content": (
            "Paket SEO Domestik: Rp600.000 per bulan.\n"
            "Paket SEO Internasional: Rp2.200.000 per bulan.\n"
            "Laporan posisi kata kunci diberikan setiap akhir bulan."
        )
    },
    {
        "category": "kebijakan",
        "keyword_triggers": "revisi, edit web, perbaikan, ganti foto",
        "title": "Kebijakan Revisi",
        "content": (
            "Setiap pembuatan website mendapatkan maksimal\n"
            "3 kali revisi gratis dalam waktu 1 bulan setelah pelunasan.\n"
            "Revisi berikutnya dapat dikenakan biaya tambahan."
        )
    },
    {
        "category": "operasional",
        "keyword_triggers": "sambung domain, online, go live, domain resmi",
        "title": "Kebijakan Aktivasi Layanan",
        "content": (
            "Aktivasi domain utama hanya dapat diproses\n"
            "jika tagihan terkait telah berstatus lunas.\n"
            "Estimasi proses aktivasi adalah 1x24 jam."
        )
    }
]


def format_embedding_text(keyword_triggers: str, title: str, content: str) -> str:
    """Format teks terstruktur untuk embedding sesuai spesifikasi."""
    return f"Keyword: {keyword_triggers}\nJudul: {title}\nKonten: {content}"


def generate_embedding(text: str, api_key: str, model: str = "text-embedding-004", dimension: int = 768) -> List[float]:
    """Menghasilkan vector embedding 768 dimensi via Gemini REST API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}"
    payload = {
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": dimension
    }
    with httpx.Client(timeout=30.0) as client:
        res = client.post(url, json=payload)
        if res.status_code != 200:
            raise RuntimeError(f"Gemini API Error [{res.status_code}]: {res.text}")
        data = res.json()
        vector = data.get("embedding", {}).get("values", [])
        if len(vector) != dimension:
            raise ValueError(f"Dimensi tidak sesuai: diharapkan {dimension}, diperoleh {len(vector)}")
        return vector


def seed_database():
    """Mengisi tabel knowledge_bases dengan data simulasi dan embedding vector 768-D."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[WARN] GEMINI_API_KEY tidak ditemukan di environment. Melewati pemanggilan API.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Pastikan tabel memiliki skema dengan kolom embedding
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_bases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            keyword_triggers TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding FLOAT[768] NOT NULL
        )
        """
    )

    print("--- Memulai proses embedding dan seeding knowledge base ---")
    for idx, item in enumerate(RAW_KNOWLEDGE_DATA, 1):
        formatted_prompt = format_embedding_text(
            keyword_triggers=item["keyword_triggers"],
            title=item["title"],
            content=item["content"]
        )
        print(f"[{idx}/{len(RAW_KNOWLEDGE_DATA)}] Meng-embed '{item['title']}'...")
        vector = generate_embedding(formatted_prompt, api_key=api_key, dimension=768)
        vector_json = json.dumps(vector)

        cursor.execute(
            """
            INSERT OR REPLACE INTO knowledge_bases (id, category, keyword_triggers, title, content, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (idx, item["category"], item["keyword_triggers"], item["title"], item["content"], vector_json)
        )
        print(f" -> Berhasil disimpan dengan {len(vector)} dimensi.")

    conn.commit()
    conn.close()
    print("--- Seeding selesai dengan sukses! ---")


if __name__ == "__main__":
    seed_database()

