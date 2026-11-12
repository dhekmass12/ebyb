import datetime
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Path ke file database SQLite
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Muat variabel environment dari dev.env jika ada
for env_candidate in [BASE_DIR / "dev.env", ROOT_DIR / "dev.env", BASE_DIR / ".env", ROOT_DIR / ".env"]:
    if env_candidate.exists():
        load_dotenv(dotenv_path=env_candidate, override=False)
        break

DEFAULT_DB_PATH = BASE_DIR / "database" / "database.db"
env_db_path = os.getenv("DATABASE_PATH")
if env_db_path:
    p = Path(env_db_path)
    if not p.is_absolute():
        if (ROOT_DIR / p).exists():
            DB_PATH = ROOT_DIR / p
        elif (BASE_DIR / p).exists():
            DB_PATH = BASE_DIR / p
        else:
            DB_PATH = ROOT_DIR / p
    else:
        DB_PATH = p
else:
    DB_PATH = DEFAULT_DB_PATH


def get_db_connection() -> sqlite3.Connection:
    """Membuka koneksi ke SQLite database dengan mengaktifkan Foreign Key constraint."""
    conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def ensure_compatibility_views() -> None:
    """
    Memastikan view 'conversation' dan 'chat_messagess' serta trigger-nya tersedia
    pada database SQLite untuk menjamin kompatibilitas alias tabel.
    """
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
        try:
            cursor = conn.cursor()
            cursor.execute("CREATE VIEW IF NOT EXISTS conversation AS SELECT * FROM conversations;")
            cursor.execute("CREATE VIEW IF NOT EXISTS chat_messagess AS SELECT * FROM chat_messages;")
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS trg_insert_conversation
                INSTEAD OF INSERT ON conversation
                BEGIN
                    INSERT INTO conversations (conversation_id, client_id, created_at, updated_at)
                    VALUES (NEW.conversation_id, NEW.client_id, NEW.created_at, NEW.updated_at);
                END;
                """
            )
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS trg_insert_chat_messagess
                INSTEAD OF INSERT ON chat_messagess
                BEGIN
                    INSERT INTO chat_messages (conversation_id, turn_index, sender, message_text, detected_intent, created_at)
                    VALUES (NEW.conversation_id, NEW.turn_index, NEW.sender, NEW.message_text, NEW.detected_intent, NEW.created_at);
                END;
                """
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


ensure_compatibility_views()


def check_db_health() -> Tuple[bool, str]:
    """
    Memeriksa ketersediaan dan kesiapan database SQLite.
    Mengembalikan tuple (status_sukses, pesan).
    """
    if not DB_PATH.exists():
        return False, f"File database tidak ditemukan di {DB_PATH}"

    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            if row and row[0] == 1:
                return True, "connected"
            return False, "Query pemeriksaan database tidak mengembalikan hasil yang valid"
        finally:
            conn.close()
    except Exception as exc:
        return False, f"Koneksi database gagal: {str(exc)}"


def get_client_and_invoices(client_id: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Mengambil data keberadaan klien dan daftar invoices berdasarkan client_id.
    Mengembalikan (client_exists: bool, invoices: list[dict]).
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM clients WHERE client_id = ?", (client_id,))
        client_exists = cursor.fetchone() is not None

        cursor.execute(
            """
            SELECT invoice_no, client_id, service_type, package_name,
                   total_amount, amount_paid, payment_status, due_date
            FROM invoices
            WHERE client_id = ?
            """,
            (client_id,),
        )
        rows = cursor.fetchall()
        invoices = [dict(row) for row in rows]
        return client_exists, invoices
    finally:
        conn.close()


def get_all_clients() -> List[Dict[str, Any]]:
    """Mengambil seluruh data clients dari database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT client_id, client_name, company_name, phone_number, official_domain, created_at
            FROM clients
            ORDER BY client_id ASC
            """
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_client_by_id(client_id: str) -> Optional[Dict[str, Any]]:
    """Mengambil satu data client berdasarkan client_id."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT client_id, client_name, company_name, phone_number, official_domain, created_at
            FROM clients
            WHERE client_id = ?
            """,
            (client_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_invoices_by_client_id(client_id: str) -> List[Dict[str, Any]]:
    """Mengambil daftar invoices untuk client_id tertentu."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT invoice_no, client_id, service_type, package_name,
                   total_amount, amount_paid, payment_status, due_date
            FROM invoices
            WHERE client_id = ?
            ORDER BY invoice_no ASC
            """,
            (client_id,),
        )
        rows = cursor.fetchall()
        invoices = []
        for row in rows:
            inv = dict(row)
            inv["outstanding_balance"] = max(0, inv["total_amount"] - inv["amount_paid"])
            invoices.append(inv)
        return invoices
    finally:
        conn.close()


def get_all_invoices() -> List[Dict[str, Any]]:
    """Mengambil semua daftar invoices."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT invoice_no, client_id, service_type, package_name,
                   total_amount, amount_paid, payment_status, due_date
            FROM invoices
            ORDER BY invoice_no ASC
            """
        )
        rows = cursor.fetchall()
        invoices = []
        for row in rows:
            inv = dict(row)
            inv["outstanding_balance"] = max(0, inv["total_amount"] - inv["amount_paid"])
            invoices.append(inv)
        return invoices
    finally:
        conn.close()


def get_all_knowledge_bases(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Mengambil seluruh data knowledge base mentah dari database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if category and isinstance(category, str):
            cursor.execute(
                """
                SELECT id, category, keyword_triggers, title, content
                FROM knowledge_bases
                WHERE category = ?
                ORDER BY id ASC
                """,
                (category,),
            )
        else:
            cursor.execute(
                """
                SELECT id, category, keyword_triggers, title, content
                FROM knowledge_bases
                ORDER BY id ASC
                """
            )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_knowledge_bases_with_embeddings() -> List[Dict[str, Any]]:
    """Mengambil seluruh entri knowledge base beserta array vector embedding-nya."""
    import json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, category, keyword_triggers, title, content, embedding
            FROM knowledge_bases
            ORDER BY id ASC
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            entry = dict(row)
            emb_raw = entry.get("embedding")
            if emb_raw:
                try:
                    entry["embedding_vector"] = json.loads(emb_raw)
                except Exception:
                    entry["embedding_vector"] = []
            else:
                entry["embedding_vector"] = []
            result.append(entry)
        return result
    finally:
        conn.close()


def get_conversation_by_id(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Mengambil data mentah percakapan dari tabel conversations berdasarkan conversation_id."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT conversation_id, client_id, created_at, updated_at
            FROM conversations
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_invoice_by_no(invoice_no: str) -> Optional[Dict[str, Any]]:
    """Mengambil rincian satu invoice berdasarkan invoice_no."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT invoice_no, client_id, service_type, package_name,
                   total_amount, amount_paid, payment_status, due_date
            FROM invoices
            WHERE invoice_no = ?
            """,
            (invoice_no,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        inv = dict(row)
        inv["outstanding_balance"] = max(0, inv["total_amount"] - inv["amount_paid"])
        return inv
    finally:
        conn.close()


def get_conversation_messages(conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Mengambil daftar riwayat pesan pada percakapan tertentu."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, conversation_id, turn_index, sender, message_text, detected_intent, created_at
            FROM chat_messages
            WHERE conversation_id = ?
            ORDER BY turn_index ASC
            LIMIT ?
            """,
            (conversation_id, limit),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_conversation_by_id(conversation_id: str) -> bool:
    """Menghapus data sesi percakapan beserta seluruh pesan chat terkait."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE conversation_id = ?", (conversation_id,))
        cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count > 0
    finally:
        conn.close()


def create_conversation(conversation_id: str, client_id: str) -> Dict[str, Any]:
    """Membuat sesi percakapan baru di tabel conversations."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO conversations (conversation_id, client_id, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (conversation_id, client_id, now, now),
        )
        conn.commit()
        return {
            "conversation_id": conversation_id,
            "client_id": client_id,
            "created_at": now,
            "updated_at": now,
        }
    finally:
        conn.close()


def get_next_turn_index(conversation_id: str) -> int:
    """Mendapatkan nilai turn_index berikutnya untuk suatu conversation_id."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COALESCE(MAX(turn_index), 0) + 1 FROM chat_messages WHERE conversation_id = ?",
            (conversation_id,),
        )
        row = cursor.fetchone()
        return row[0] if row else 1
    finally:
        conn.close()


def add_chat_message(
    conversation_id: str,
    turn_index: int,
    sender: str,
    message_text: str,
    detected_intent: Optional[str] = None,
) -> int:
    """Menyimpan pesan chat baru ke tabel chat_messages dan memperbarui waktu percakapan."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_messages (conversation_id, turn_index, sender, message_text, detected_intent, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (conversation_id, turn_index, sender, message_text, detected_intent, now),
        )
        cursor.execute(
            "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
            (now, conversation_id),
        )
        message_id = cursor.lastrowid or 0
        conn.commit()
        return message_id
    finally:
        conn.close()


def add_knowledge_base(
    category: str,
    keyword_triggers: str,
    title: str,
    content: str,
    embedding: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Menambahkan entri knowledge base baru ke dalam database SQLite.
    Mengembalikan dict data knowledge base yang berhasil disimpan.
    """
    import json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if not embedding:
            embedding = json.dumps([0.0] * 768)

        cursor.execute(
            """
            INSERT INTO knowledge_bases (category, keyword_triggers, title, content, embedding)
            VALUES (?, ?, ?, ?, ?)
            """,
            (category, keyword_triggers, title, content, embedding),
        )
        new_id = cursor.lastrowid
        conn.commit()
        return {
            "id": new_id,
            "category": category,
            "keyword_triggers": keyword_triggers,
            "title": title,
            "content": content,
        }
    finally:
        conn.close()


def get_table_columns(table_name: str) -> List[str]:
    """Mengambil daftar nama kolom dari tabel SQLite secara dinamis."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        rows = cursor.fetchall()
        return [row[1] for row in rows]
    except Exception:
        return []
    finally:
        conn.close()


def update_invoice_payment(invoice_no: str, new_amount_paid: int, new_payment_status: str) -> bool:
    """
    Memperbarui kolom amount_paid dan payment_status pada tabel invoices berdasarkan invoice_no.
    Mengembalikan True jika baris berhasil diperbarui, False jika invoice_no tidak ditemukan.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE invoices
            SET amount_paid = ?, payment_status = ?
            WHERE invoice_no = ?
            """,
            (new_amount_paid, new_payment_status, invoice_no),
        )
        updated = cursor.rowcount > 0
        conn.commit()
        return updated
    finally:
        conn.close()




