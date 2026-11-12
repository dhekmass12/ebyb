import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
import database
import gemini_tools


# ------------------------------------------------------------------------------
# Dynamic Enums from Database Columns
# ------------------------------------------------------------------------------
def test_dynamic_columns_fetch():
    client_cols = gemini_tools.get_client_columns()
    assert "company_name" in client_cols
    assert "phone_number" in client_cols
    assert "official_domain" in client_cols

    invoice_cols = gemini_tools.get_invoice_columns()
    assert "total_amount" in invoice_cols
    assert "amount_paid" in invoice_cols
    assert "outstanding_balance" in invoice_cols


def test_dynamic_tool_declarations_enum():
    declarations = gemini_tools.get_gemini_tool_declarations()
    # Tool 1 enum
    tool_1 = next(t for t in declarations if t["name"] == "get_client_info")
    tool_1_enum = tool_1["parameters"]["properties"]["jenis_informasi"]["items"]["enum"]
    assert "company_name" in tool_1_enum
    assert "phone_number" in tool_1_enum

    # Tool 2 enum
    tool_2 = next(t for t in declarations if t["name"] == "get_invoice_info")
    tool_2_enum = tool_2["parameters"]["properties"]["jenis_informasi"]["items"]["enum"]
    assert "total_amount" in tool_2_enum
    assert "outstanding_balance" in tool_2_enum


def test_tool_1_get_client_info_enum_columns():
    gemini_tools.set_current_client_id("CLI-001")
    # Panggilan menggunakan nama kolom tabel persis dari enum
    res = gemini_tools.get_client_info(jenis_informasi=["company_name", "phone_number"])
    assert res["status"] == "success"
    assert res["data"]["company_name"] == "PT Makmur Sentosa"
    assert res["data"]["phone_number"] == "6281234567801"


def test_tool_2_get_invoice_info_enum_columns():
    # Panggilan menggunakan nama kolom tabel persis dari enum
    res = gemini_tools.get_invoice_info(
        invoice_no="INV-2026-001",
        jenis_informasi=["total_amount", "outstanding_balance"]
    )
    assert res["status"] == "success"
    assert res["data"]["total_amount"] == 1600000
    assert res["data"]["outstanding_balance"] == 800000


# ------------------------------------------------------------------------------
# Tool 1: get_client_info (READ-ONLY)
# ------------------------------------------------------------------------------
def test_tool_1_get_client_info_phone():
    gemini_tools.set_current_client_id("CLI-001")
    res = gemini_tools.get_client_info(jenis_informasi="nomor kontak")
    assert res["status"] == "success"
    assert res["operation"] == "READ"
    assert res["client_id"] == "CLI-001"
    assert res["jenis_informasi"] == "nomor kontak"
    assert res["data"]["phone_number"] == "6281234567801"


def test_tool_1_get_client_info_company():
    gemini_tools.set_current_client_id("CLI-001")
    res = gemini_tools.get_client_info(jenis_informasi="nama perusahaan")
    assert res["status"] == "success"
    assert res["operation"] == "READ"
    assert res["data"]["company_name"] == "PT Makmur Sentosa"


def test_tool_1_get_client_info_all():
    gemini_tools.set_current_client_id("CLI-001")
    res = gemini_tools.get_client_info(jenis_informasi="semua")
    assert res["status"] == "success"
    assert res["operation"] == "READ"
    assert res["data"]["client_name"] == "Budi Santoso"
    assert res["data"]["company_name"] == "PT Makmur Sentosa"
    assert res["data"]["phone_number"] == "6281234567801"
    assert res["data"]["official_domain"] == "makmursentosa.com"


def test_tool_1_get_client_info_multiple_fields_list():
    gemini_tools.set_current_client_id("CLI-001")
    res = gemini_tools.get_client_info(jenis_informasi=["nama perusahaan", "nomor kontak"])
    assert res["status"] == "success"
    assert res["operation"] == "READ"
    assert res["data"]["company_name"] == "PT Makmur Sentosa"
    assert res["data"]["phone_number"] == "6281234567801"
    assert "nama perusahaan" in res["jenis_informasi"]
    assert "nomor kontak" in res["jenis_informasi"]


def test_tool_1_get_client_info_multiple_fields_string():
    gemini_tools.set_current_client_id("CLI-001")
    res = gemini_tools.get_client_info(jenis_informasi="nama perusahaan, nomor kontak")
    assert res["status"] == "success"
    assert res["data"]["company_name"] == "PT Makmur Sentosa"
    assert res["data"]["phone_number"] == "6281234567801"


def test_tool_1_get_client_info_not_found():
    gemini_tools.set_current_client_id("CLI-999")
    res = gemini_tools.get_client_info(jenis_informasi="nomor kontak")
    assert res["status"] == "error"
    assert res["operation"] == "READ"
    assert "tidak ditemukan" in res["message"]


def test_tool_1_get_client_info_unmatched_column_fallback():
    gemini_tools.set_current_client_id("CLI-001")
    res = gemini_tools.get_client_info(jenis_informasi=["alamat_rumah", "hobi_klien"])
    assert res["status"] == "not_found"
    assert res["operation"] == "READ"
    assert res["message"] == gemini_tools.DATABASE_FALLBACK_MSG
    assert "tidak tersedia" in res["message"]


# ------------------------------------------------------------------------------
# Tool 2: get_invoice_info (READ-ONLY)
# ------------------------------------------------------------------------------
def test_tool_2_get_invoice_info_success():
    res = gemini_tools.get_invoice_info(invoice_no="INV-2026-001", jenis_informasi="semua")
    assert res["status"] == "success"
    assert res["operation"] == "READ"
    assert res["data"]["invoice_no"] == "INV-2026-001"
    assert res["data"]["client_id"] == "CLI-001"
    assert res["data"]["total_amount"] == 1600000
    assert res["data"]["amount_paid"] == 800000
    assert res["data"]["outstanding_balance"] == 800000
    assert res["data"]["payment_status"] == "half_paid"


def test_tool_2_get_invoice_info_specific_fields():
    # Cek total tagihan
    res_total = gemini_tools.get_invoice_info(jenis_informasi="total tagihan", invoice_no="INV-2026-001")
    assert res_total["status"] == "success"
    assert res_total["jenis_informasi"] == "total tagihan"
    assert res_total["data"]["total_amount"] == 1600000

    # Cek total yang sudah dibayarkan
    res_paid = gemini_tools.get_invoice_info(jenis_informasi="total yang sudah dibayarkan", invoice_no="INV-2026-001")
    assert res_paid["status"] == "success"
    assert res_paid["jenis_informasi"] == "total yang sudah dibayarkan"
    assert res_paid["data"]["amount_paid"] == 800000

    # Cek sisa tagihan
    res_out = gemini_tools.get_invoice_info(jenis_informasi="sisa tagihan", invoice_no="INV-2026-001")
    assert res_out["status"] == "success"
    assert res_out["jenis_informasi"] == "sisa tagihan"
    assert res_out["data"]["outstanding_balance"] == 800000


def test_tool_2_get_invoice_info_multiple_fields_list():
    res = gemini_tools.get_invoice_info(
        invoice_no="INV-2026-001",
        jenis_informasi=["total tagihan", "sisa tagihan"]
    )
    assert res["status"] == "success"
    assert res["operation"] == "READ"
    assert res["data"]["total_amount"] == 1600000
    assert res["data"]["outstanding_balance"] == 800000
    assert "total tagihan" in res["jenis_informasi"]
    assert "sisa tagihan" in res["jenis_informasi"]


def test_tool_2_get_invoice_info_multiple_fields_string():
    res = gemini_tools.get_invoice_info(
        invoice_no="INV-2026-001",
        jenis_informasi="total tagihan dan sisa tagihan"
    )
    assert res["status"] == "success"
    assert res["data"]["total_amount"] == 1600000
    assert res["data"]["outstanding_balance"] == 800000


def test_tool_2_get_invoice_info_via_dispatcher():
    res = gemini_tools.execute_tool_call(
        "get_invoice_info",
        {"jenis_informasi": ["total tagihan", "sisa tagihan"], "invoice_no": "INV-2026-001"}
    )
    assert res["status"] == "success"
    assert res["data"]["total_amount"] == 1600000
    assert res["data"]["outstanding_balance"] == 800000


def test_tool_2_get_invoice_info_not_found():
    res = gemini_tools.get_invoice_info(invoice_no="INV-9999-999")
    assert res["status"] == "error"
    assert res["operation"] == "READ"
    assert "tidak ditemukan" in res["message"]


def test_tool_2_get_invoice_info_missing_invoice_no():
    res = gemini_tools.get_invoice_info(invoice_no="")
    assert res["status"] == "error"
    assert "wajib diisi" in res["message"]


def test_tool_2_get_invoice_info_unmatched_column_fallback():
    res = gemini_tools.get_invoice_info(invoice_no="INV-2026-001", jenis_informasi=["ongkos_kirim", "warna_kertas"])
    assert res["status"] == "not_found"
    assert res["operation"] == "READ"
    assert res["message"] == gemini_tools.DATABASE_FALLBACK_MSG
    assert "tidak tersedia" in res["message"]


# ------------------------------------------------------------------------------
# Tool 3: get_conversation_history (READ-ONLY)
# Tool 4: delete_conversation_history (DELETE-ONLY)
# ------------------------------------------------------------------------------
@pytest.fixture
def sample_conversation():
    conv_id = "test-gemini-conv-001"
    client_id = "CLI-001"
    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE conversation_id = ?", (conv_id,))
        cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (conv_id,))
        cursor.execute(
            "INSERT INTO conversations (conversation_id, client_id, created_at, updated_at) VALUES (?, ?, '2026-01-01', '2026-01-01')",
            (conv_id, client_id)
        )
        cursor.execute(
            """
            INSERT INTO chat_messages (conversation_id, turn_index, sender, message_text, created_at)
            VALUES (?, 1, 'user', 'Halo, berapa tagihan saya?', '2026-01-01 10:00:00'),
                   (?, 2, 'assistant', 'Tagihan Anda sebesar Rp1.600.000', '2026-01-01 10:00:05')
            """,
            (conv_id, conv_id)
        )
        conn.commit()
    finally:
        conn.close()

    yield conv_id

    # Cleanup jika masih tersisa
    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE conversation_id = ?", (conv_id,))
        cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (conv_id,))
        conn.commit()
    finally:
        conn.close()


def test_tool_3_get_conversation_history_no_params(sample_conversation):
    # Set context sesi percakapan aktif
    gemini_tools.set_current_conversation_id(sample_conversation)
    
    # Panggilan tanpa parameter apapun
    res = gemini_tools.get_conversation_history()
    assert res["status"] == "success"
    assert res["operation"] == "READ"
    assert res["conversation_id"] == sample_conversation
    assert res["total_messages"] == 2
    assert res["messages"][0]["sender"] == "user"
    assert "Halo, berapa tagihan saya?" in res["messages"][0]["message_text"]
    assert res["messages"][1]["sender"] == "assistant"


def test_tool_3_get_conversation_history_via_dispatcher(sample_conversation):
    gemini_tools.set_current_conversation_id(sample_conversation)
    # Dispatcher dipanggil dengan argumen kosong {} sebagaimana Gemini memanggil tool tanpa parameter
    res = gemini_tools.execute_tool_call("get_conversation_history", {})
    assert res["status"] == "success"
    assert res["total_messages"] == 2


def test_tool_4_delete_conversation_history_no_params(sample_conversation):
    # Set context sesi percakapan aktif
    gemini_tools.set_current_conversation_id(sample_conversation)
    
    # Lakukan delete tanpa parameter apapun
    res = gemini_tools.delete_conversation_history()
    assert res["status"] == "success"
    assert res["operation"] == "DELETE"
    assert "berhasil dihapus" in res["message"]

    # Verifikasi data sudah tidak ada
    check = database.get_conversation_by_id(sample_conversation)
    assert check is None
    messages = database.get_conversation_messages(sample_conversation)
    assert len(messages) == 0


def test_tool_4_delete_conversation_history_via_dispatcher(sample_conversation):
    gemini_tools.set_current_conversation_id(sample_conversation)
    # Dispatcher dipanggil dengan argumen kosong {}
    res = gemini_tools.execute_tool_call("delete_conversation_history", {})
    assert res["status"] == "success"
    assert res["operation"] == "DELETE"


def test_tool_4_delete_conversation_history_not_found():
    gemini_tools.set_current_conversation_id(None)
    res = gemini_tools.delete_conversation_history()
    assert res["status"] == "error"
    assert res["operation"] == "DELETE"


# ------------------------------------------------------------------------------
# Tool 5: request_domain_activation (POLICY GATE - Tanpa Parameter)
# ------------------------------------------------------------------------------
def test_tool_5_domain_activation_unpaid_no_params():
    # CLI-001 has unpaid balance (half_paid: Rp800.000 unpaid)
    gemini_tools.set_current_client_id("CLI-001")
    res = gemini_tools.request_domain_activation()
    assert res["status"] == "rejected"
    assert res["can_activate"] is False
    assert res["outstanding_balance"] == 800000
    assert "belum dapat diproses" in res["message"]
    assert "Rp800,000" in res["message"]


def test_tool_5_domain_activation_paid_no_params():
    # CLI-002 has paid balance (paid: 600000 / 600000)
    gemini_tools.set_current_client_id("CLI-002")
    res = gemini_tools.request_domain_activation()
    assert res["status"] == "approved"
    assert res["can_activate"] is True
    assert "berhasil diajukan" in res["message"]
    assert "1x24 jam" in res["message"]


def test_tool_5_domain_activation_via_dispatcher():
    gemini_tools.set_current_client_id("CLI-002")
    res = gemini_tools.execute_tool_call("request_domain_activation", {})
    assert res["status"] == "approved"
    assert res["can_activate"] is True


def test_tool_5_domain_activation_inconsistent_invoice():
    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invoices WHERE invoice_no = 'INV-TEST-INCONSISTENT'")
        cursor.execute("DELETE FROM clients WHERE client_id = 'CLI-INCONSISTENT'")
        cursor.execute(
            """
            INSERT INTO clients (client_id, client_name, phone_number, official_domain, created_at)
            VALUES ('CLI-INCONSISTENT', 'Klien Inconsistent', '62899999999', 'inconsistent.com', '2026-01-01 10:00:00')
            """
        )
        cursor.execute(
            """
            INSERT INTO invoices (invoice_no, client_id, service_type, package_name, total_amount, amount_paid, payment_status, due_date)
            VALUES ('INV-TEST-INCONSISTENT', 'CLI-INCONSISTENT', 'website', 'Custom Web', 1000000, 500000, 'paid', '2026-02-01')
            """
        )
        conn.commit()

        gemini_tools.set_current_client_id("CLI-INCONSISTENT")
        res = gemini_tools.request_domain_activation()
        assert res["status"] == "rejected"
        assert res["can_activate"] is False
        assert "tidak konsisten" in res["message"].lower() or "ketidakkonsistenan" in res["message"].lower()
        assert "INV-TEST-INCONSISTENT" in res["message"]
        assert res.get("invoice_no") == "INV-TEST-INCONSISTENT"
    finally:
        cursor.execute("DELETE FROM invoices WHERE invoice_no = 'INV-TEST-INCONSISTENT'")
        cursor.execute("DELETE FROM clients WHERE client_id = 'CLI-INCONSISTENT'")
        conn.commit()
        conn.close()


# ------------------------------------------------------------------------------
# Tool 6: confirm_payment (Tanpa Parameter client_id)
# ------------------------------------------------------------------------------
def test_tool_6_confirm_payment_valid_half_paid():
    gemini_tools.set_current_client_id("CLI-001")
    try:
        res = gemini_tools.confirm_payment(
            nominal_transfer=200000,
            invoice_no="INV-2026-001",
            bank_tujuan="BCA",
            nama_rekening_pengirim="Budi Santoso"
        )
        assert res["status"] == "success"
        assert res["client_id"] == "CLI-001"
        assert res["nominal_transfer"] == 200000
        assert res["new_amount_paid"] == 1000000
        assert res["payment_status"] == "half_paid"
        assert "berhasil dikonfirmasi" in res["message"].lower()

        # Cek update di database
        inv = database.get_invoice_by_no("INV-2026-001")
        assert inv["amount_paid"] == 1000000
        assert inv["payment_status"] == "half_paid"
    finally:
        database.update_invoice_payment("INV-2026-001", 800000, "half_paid")


def test_tool_6_confirm_payment_valid_full_paid():
    gemini_tools.set_current_client_id("CLI-001")
    try:
        res = gemini_tools.confirm_payment(
            nominal_transfer=800000,
            invoice_no="INV-2026-001",
            bank_tujuan="MANDIRI",
            nama_rekening_pengirim="Budi Santoso"
        )
        assert res["status"] == "success"
        assert res["new_amount_paid"] == 1600000
        assert res["payment_status"] == "paid"
        assert "berhasil dikonfirmasi" in res["message"].lower()

        # Cek update di database
        inv = database.get_invoice_by_no("INV-2026-001")
        assert inv["amount_paid"] == 1600000
        assert inv["payment_status"] == "paid"
    finally:
        database.update_invoice_payment("INV-2026-001", 800000, "half_paid")


def test_tool_6_confirm_payment_via_dispatcher():
    gemini_tools.set_current_client_id("CLI-001")
    try:
        res = gemini_tools.execute_tool_call(
            "confirm_payment",
            {
                "nominal_transfer": 100000,
                "invoice_no": "INV-2026-001",
                "bank_tujuan": "BRI",
                "nama_rekening_pengirim": "Budi Santoso"
            }
        )
        assert res["status"] == "success"
        assert res["new_amount_paid"] == 900000
        assert res["payment_status"] == "half_paid"
    finally:
        database.update_invoice_payment("INV-2026-001", 800000, "half_paid")


def test_tool_6_confirm_payment_invalid_nominal():
    gemini_tools.set_current_client_id("CLI-001")
    res = gemini_tools.confirm_payment(nominal_transfer=0, invoice_no="INV-2026-001")
    assert res["status"] == "failed"
    assert "gagal mengubah status pembayaran" in res["message"].lower()
    assert "verifikasi informasi" in res["message"].lower()

    res_neg = gemini_tools.confirm_payment(nominal_transfer=-10000, invoice_no="INV-2026-001")
    assert res_neg["status"] == "failed"
    assert "gagal mengubah status pembayaran" in res_neg["message"].lower()
    assert "verifikasi informasi" in res_neg["message"].lower()


def test_tool_6_confirm_payment_missing_required_fields_fails():
    gemini_tools.set_current_client_id("CLI-001")
    # Missing bank and sender name
    res = gemini_tools.confirm_payment(nominal_transfer=50000, invoice_no="INV-2026-001")
    assert res["status"] == "failed"
    assert "gagal mengubah status pembayaran" in res["message"].lower()
    assert "verifikasi informasi" in res["message"].lower()


# ------------------------------------------------------------------------------
# Tool 7: ask_general_knowledge (READ-ONLY - Tanpa Parameter)
# ------------------------------------------------------------------------------
def test_tool_7_general_knowledge_found_no_params():
    gemini_tools.set_current_user_message("Berapa biaya paket seo?")
    res = gemini_tools.ask_general_knowledge()
    assert res["status"] == "found"
    assert res["operation"] == "READ"
    assert "SEO" in res["title"]
    assert "Rp600.000" in res["content"]


def test_tool_7_general_knowledge_not_found_no_params():
    gemini_tools.set_current_user_message("Apakah tersedia layanan sewa drone?")
    res = gemini_tools.ask_general_knowledge()
    assert res["status"] == "not_found"
    assert res["operation"] == "READ"
    assert "Mohon maaf kak, informasi tersebut belum tersedia di sistem kami." in res["message"]


def test_tool_7_general_knowledge_via_dispatcher():
    gemini_tools.set_current_user_message("Berapa biaya paket seo?")
    res = gemini_tools.execute_tool_call("ask_general_knowledge", {})
    assert res["status"] == "found"
    assert res["operation"] == "READ"


# ------------------------------------------------------------------------------
# Tool 8: handle_ignored_instruction (REJECT-ONLY, dev.env:L43)
# ------------------------------------------------------------------------------
def test_tool_8_handle_ignored_instruction():
    res = gemini_tools.handle_ignored_instruction()
    assert res["status"] == "ignored"
    assert res["operation"] == "REJECT"
    assert "tidak dapat" in res["message"].lower()


def test_tool_8_handle_ignored_instruction_via_dispatcher():
    res = gemini_tools.execute_tool_call("handle_ignored_instruction", {})
    assert res["status"] == "ignored"
    assert res["operation"] == "REJECT"
    assert "tidak dapat" in res["message"].lower()


# ------------------------------------------------------------------------------
# Dispatcher: execute_tool_call
# ------------------------------------------------------------------------------
def test_execute_tool_call():
    gemini_tools.set_current_client_id("CLI-001")
    res = gemini_tools.execute_tool_call("get_client_info", {"jenis_informasi": "nama perusahaan"})
    assert res["status"] == "success"
    assert res["data"]["company_name"] == "PT Makmur Sentosa"

    unknown = gemini_tools.execute_tool_call("unknown_tool", {})
    assert unknown["status"] == "error"


def test_execute_tool_call_client_info_fallback():
    gemini_tools.set_current_client_id("CLI-001")
    res = gemini_tools.execute_tool_call("get_client_info", {"jenis_informasi": ["alamat_rumah"]})
    assert res["status"] == "not_found"
    assert res["message"] == gemini_tools.DATABASE_FALLBACK_MSG


def test_execute_tool_call_invoice_info_fallback():
    res = gemini_tools.execute_tool_call("get_invoice_info", {"invoice_no": "INV-2026-001", "jenis_informasi": ["berat_barang"]})
    assert res["status"] == "not_found"
    assert res["message"] == gemini_tools.DATABASE_FALLBACK_MSG


# ------------------------------------------------------------------------------
# Dev.env & External Configuration
# ------------------------------------------------------------------------------
def test_gemini_config_loaded_from_env():
    config = gemini_tools.get_gemini_config()
    assert "gemini_api_key" in config
    assert "gemini_model" in config
    assert config["gemini_model"] == "gemini-2.0-flash"
    assert "current_client_id" in config
    assert config["domain_activation_sla"] == "1x24 jam"
    assert "BCA" in config["allowed_payment_banks"]
    assert config["finance_verification_status"] == "submitted_for_verification"
    assert config["chat_history_limit"] == 20
    assert "Mohon maaf" in config["general_knowledge_fallback_msg"]


# ------------------------------------------------------------------------------
# Session Validation Tests: Error to re-login if no active client ID
# ------------------------------------------------------------------------------
def test_tool_1_get_client_info_no_session_error():
    gemini_tools.set_current_client_id(None)
    res = gemini_tools.get_client_info()
    assert res["status"] == "error"
    assert res["operation"] == "READ"
    assert "login kembali" in res["message"].lower()


def test_tool_5_domain_activation_no_session_error():
    gemini_tools.set_current_client_id(None)
    res = gemini_tools.request_domain_activation()
    assert res["status"] == "error"
    assert "login kembali" in res["message"].lower()


def test_tool_6_confirm_payment_no_session_error():
    gemini_tools.set_current_client_id(None)
    res = gemini_tools.confirm_payment(nominal_transfer=100000)
    assert res["status"] in ["error", "failed"]
    assert "gagal mengubah status pembayaran" in res["message"].lower()
    assert "login kembali" in res["message"].lower()


def test_contextvars_concurrency_isolation():
    """Memverifikasi bahwa dua context berbeda terisolasi dan tidak saling menimpa client_id."""
    import contextvars

    ctx1 = contextvars.copy_context()
    ctx2 = contextvars.copy_context()

    def set_and_check(client_id, expected_name):
        gemini_tools.set_current_client_id(client_id)
        res = gemini_tools.get_client_info(jenis_informasi=["client_name"])
        assert res["status"] == "success"
        assert res["data"]["client_name"] == expected_name
        assert gemini_tools.get_current_client_id() == client_id

    # Jalankan di context 1
    ctx1.run(set_and_check, "CLI-001", "Budi Santoso")
    # Jalankan di context 2
    ctx2.run(set_and_check, "CLI-002", "Rani Wijaya")

    # Verifikasi context 1 tetap CLI-001 dan context 2 tetap CLI-002
    assert ctx1[gemini_tools._current_client_id] == "CLI-001"
    assert ctx2[gemini_tools._current_client_id] == "CLI-002"



