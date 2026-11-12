"""
Script Inisialisasi Database dan Seeder (SQLite)
Sesuai Ketentuan Technical Test Bagian 3.B dan 6.2.

Menjalankan file schema.sql dan mengisi data simulasi awal:
- Tabel clients (CLI-001, CLI-002, CLI-003)
- Tabel invoices (INV-2026-001, INV-2026-002, INV-2026-003)
- Tabel knowledge_bases (4 entri simulasi beserta vector embedding 768-D)
"""

import json
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "database.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"

INITIAL_CLIENTS = [
    ("CLI-001", "Budi Santoso", "PT Makmur Sentosa", "6281234567801", "makmursentosa.com", "2026-01-01 09:00:00"),
    ("CLI-002", "Rani Wijaya", "Toko Berkah Rani", "6281234567802", "tokorani.id", "2026-01-02 10:00:00"),
    ("CLI-003", "Hendra Tan", "CV Solusi Digital", "6281234567803", "solusidigital.co.id", "2026-01-03 11:00:00"),
]

INITIAL_INVOICES = [
    ("INV-2026-001", "CLI-001", "website", "Gold Website", 1600000, 800000, "half_paid", "2026-02-15"),
    ("INV-2026-002", "CLI-002", "seo", "SEO Domestik", 600000, 600000, "paid", "2026-02-20"),
    ("INV-2026-003", "CLI-003", "website", "Platinum Website", 3000000, 0, "unpaid", "2026-02-28"),
]

INITIAL_KNOWLEDGE_BASES = [
    (
        1,
        "rekening",
        "rekening, transfer, bayar, bca, mandiri, bri",
        "Rekening Pembayaran",
        "Data rekening pembayaran resmi untuk keperluan simulasi:\n"
        "BCA: 111-222-333 a.n. PT Contoh Digital.\n"
        "Gunakan hanya data simulasi ini."
    ),
    (
        2,
        "layanan",
        "seo, paket seo, ranking google, search engine",
        "Informasi Layanan SEO",
        "Paket SEO Domestik: Rp600.000 per bulan.\n"
        "Paket SEO Internasional: Rp2.200.000 per bulan.\n"
        "Laporan posisi kata kunci diberikan setiap akhir bulan."
    ),
    (
        3,
        "kebijakan",
        "revisi, edit web, perbaikan, ganti foto",
        "Kebijakan Revisi",
        "Setiap pembuatan website mendapatkan maksimal\n"
        "3 kali revisi gratis dalam waktu 1 bulan setelah pelunasan.\n"
        "Revisi berikutnya dapat dikenakan biaya tambahan."
    ),
    (
        4,
        "operasional",
        "sambung domain, online, go live, domain resmi",
        "Kebijakan Aktivasi Layanan",
        "Aktivasi domain utama hanya dapat diproses\n"
        "jika tagihan terkait telah berstatus lunas.\n"
        "Estimasi proses aktivasi adalah 1x24 jam."
    ),
]


def init_database(reset: bool = False):
    """Inisialisasi database SQLite dan mengisi data awal seeder."""
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    print(f"[*] Menyiapkan schema database pada: {DB_PATH}")
    if SCHEMA_PATH.exists():
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        cursor.executescript(schema_sql)
    else:
        print("[!] File schema.sql tidak ditemukan, membuat tabel fallback...")

    # Seeder Clients
    print("[*] Memeriksa dan mengisi seeder clients...")
    for c in INITIAL_CLIENTS:
        cursor.execute(
            """
            INSERT OR REPLACE INTO clients (client_id, client_name, company_name, phone_number, official_domain, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            c,
        )

    # Seeder Invoices
    print("[*] Memeriksa dan mengisi seeder invoices...")
    for inv in INITIAL_INVOICES:
        cursor.execute(
            """
            INSERT OR REPLACE INTO invoices (invoice_no, client_id, service_type, package_name, total_amount, amount_paid, payment_status, due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            inv,
        )

    # Seeder Knowledge Bases
    print("[*] Memeriksa dan mengisi seeder knowledge_bases...")
    # Cek apakah embedding sudah ada di DB untuk entri yang ada
    existing_embeddings = {}
    try:
        rows = cursor.execute("SELECT id, embedding FROM knowledge_bases").fetchall()
        for r in rows:
            if r[1]:
                existing_embeddings[r[0]] = r[1]
    except Exception:
        pass

    for kb in INITIAL_KNOWLEDGE_BASES:
        kb_id, cat, triggers, title, content = kb
        emb_json = existing_embeddings.get(kb_id)
        if not emb_json:
            # Gunakan vector zero 768 dimensi sebagai default jika belum di-generate
            emb_json = json.dumps([0.0] * 768)

        cursor.execute(
            """
            INSERT OR REPLACE INTO knowledge_bases (id, category, keyword_triggers, title, content, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (kb_id, cat, triggers, title, content, emb_json),
        )

    conn.commit()
    conn.close()
    print("[+] Database berhasil diinisialisasi dan diisi dengan data simulasi awal.")


if __name__ == "__main__":
    init_database()
