"""
Modul Chatbot Engine untuk Sistem Layanan Digital.

Mengimplementasikan alur pemrosesan percakapan:
User Input -> Intent Detection -> Policy Check -> Knowledge Retrieval -> Response Generation -> Save Conversation

Menangani seluruh skenario pengujian TC-01 hingga TC-10:
- TC-01: Informasi layanan (Knowledge Base SEO)
- TC-02: Informasi pembayaran (Knowledge Base Rekening)
- TC-03: Policy Gate Aktivasi Domain Belum Lunas
- TC-04: Policy Gate Aktivasi Domain Sudah Lunas
- TC-05: Pencegahan manipulasi & antrean klaim verifikasi pembayaran
- TC-06: Pencegahan prompt injection & manipulasi status tagihan
- TC-07: General fallback untuk informasi di luar knowledge base
- TC-08: Isolasi percakapan antar klien
- TC-09: Validasi data nominal pembayaran (0 / negatif)
- TC-10: Pengelolaan sesi percakapan
"""

import os
import re
import uuid
from typing import Any, Dict, Optional

import database
import gemini_tools


def extract_nominal(text: str) -> Optional[int]:
    """
    Mengekstrak nominal angka uang dari teks pengguna.
    Mendukung format:
    - 'Rp3.000.000', '3.000.000', '50000'
    - 'nominal 0', 'transfer -50000'
    """
    # 1. Cek nominal negatif atau nol secara eksplisit setelah kata kunci
    m_neg = re.search(r'(?:nominal|transfer|bayar|sebesar|sejumlah)\s*(-?\d+)\b', text, re.IGNORECASE)
    if m_neg:
        val = int(m_neg.group(1))
        if val <= 0:
            return val

    # 2. Cek nominal positif dengan prefix mata uang atau kata kunci
    m = re.search(
        r'(?:rp\.?\s*|\bsebesar\s*|\bnominal\s*|\btransfer\s*|\bbayar\s*)([0-9]{1,3}(?:[.,][0-9]{3})+|[0-9]+)',
        text,
        re.IGNORECASE
    )
    if m:
        num_str = m.group(1).replace(".", "").replace(",", "")
        try:
            return int(num_str)
        except ValueError:
            return None
    return None


def extract_invoice_no(text: str) -> Optional[str]:
    """Mengekstrak nomor invoice dengan format INV-YYYY-NNN."""
    m = re.search(r'\b(INV-\d{4}-\d{3})\b', text, re.IGNORECASE)
    return m.group(1).upper() if m else None


def extract_bank(text: str) -> Optional[str]:
    """Mengekstrak bank tujuan transfer resmi (BCA, MANDIRI, BRI)."""
    m = re.search(r'\b(BCA|MANDIRI|BRI)\b', text, re.IGNORECASE)
    return m.group(1).upper() if m else None


def extract_sender_name(text: str) -> Optional[str]:
    """Mengekstrak nama rekening pengirim jika dicantumkan dalam teks percakapan."""
    patterns = [
        r'(?:atas\s*nama|a\.?n\.?|a/n)\s+([A-Za-z\s]{3,30})',
        r'(?:rekening\s*(?:pengirim)?)\s+([A-Za-z\s]{3,30})',
        r'(?:dari\s*rekening)\s+([A-Za-z\s]{3,30})',
        r'(?:pengirim)\s+([A-Za-z\s]{3,30})',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            raw_name = m.group(1).strip()
            clean_name = re.split(
                r'\b(?:ke|untuk|sebesar|nominal|bank|bca|mandiri|bri|inv|tagihan)\b',
                raw_name,
                flags=re.IGNORECASE
            )[0].strip()
            if len(clean_name.replace(" ", "")) >= 3:
                return clean_name
    return None


def detect_intent_and_generate_response(client_id: str, message: str) -> tuple[str, str]:
    """
    Mendeteksi intent pengguna menggunakan Gemini Tool Calling (Function Calling),
    menjalankan policy gate yang relevan, dan menghasilkan jawaban chatbot yang faktual dan aman.
    
    Returns:
        tuple[detected_intent: str, response_text: str]
    """
    # --------------------------------------------------------------------------
    # Pemanggilan Gemini Tool Calling (Function Calling)
    # Memakai skema deklaratif tools dari GEMINI_TOOL_DECLARATIONS
    # --------------------------------------------------------------------------
    tool_call_res = gemini_tools.call_gemini_tool_calling(message)

    if tool_call_res and tool_call_res.get("type") == "function_call":
        tool_name = tool_call_res.get("name")
        tool_args = tool_call_res.get("args", {}) or {}

        # 1. Tool 5: request_domain_activation (TC-03 & TC-04)
        if tool_name == "request_domain_activation":
            result = gemini_tools.execute_tool_call("request_domain_activation", tool_args)
            return ("domain_activation", result.get("message", ""))

        # 2. Tool 8: handle_ignored_instruction (Prompt injection & instruksi diabaikan, dev.env:L43)
        elif tool_name == "handle_ignored_instruction":
            result = gemini_tools.execute_tool_call("handle_ignored_instruction", tool_args)
            return ("ignored_instruction", result.get("message", gemini_tools.IGNORED_INSTRUCTION_FALLBACK_MSG))

        # 2. Tool 6: confirm_payment (TC-05 & TC-09)
        elif tool_name == "confirm_payment":
            nominal = tool_args.get("nominal_transfer")
            if nominal is None:
                nominal = extract_nominal(message)
            inv_no = tool_args.get("invoice_no") or extract_invoice_no(message)
            bank = tool_args.get("bank_tujuan") or extract_bank(message)
            sender = tool_args.get("nama_rekening_pengirim") or extract_sender_name(message)

            if nominal is not None:
                # Validasi nominal lewat confirm_payment
                res = gemini_tools.confirm_payment(
                    nominal_transfer=nominal,
                    invoice_no=inv_no,
                    bank_tujuan=bank,
                    nama_rekening_pengirim=sender,
                    client_id=client_id
                )
                if nominal <= 0:
                    return ("payment_validation_error", res.get("message", "Nominal transfer tidak valid."))
                # TC-05: Konfirmasi pembayaran masuk antrean verifikasi tanpa manipulasi status database
                return (
                    "payment_confirmation",
                    f"Konfirmasi pembayaran sejumlah Rp{nominal:,} telah kami terima dan masuk ke sistem antrean verifikasi. "
                    "Tim finance kami akan segera melakukan pengecekan mutasi bank. Status tagihan akan diperbarui setelah verifikasi berhasil."
                )
            else:
                return (
                    "payment_confirmation_need_info",
                    "Terima kasih atas konfirmasi pembayaran Anda. Mohon sertakan nominal transfer, nomor invoice, "
                    "serta bank tujuan transfer (BCA/MANDIRI/BRI) agar pengajuan dapat diverifikasi oleh sistem."
                )

        # 3. Tool 1: get_client_info (Profil Klien)
        elif tool_name == "get_client_info":
            info_fields = tool_args.get("jenis_informasi", "semua")
            res = gemini_tools.get_client_info(jenis_informasi=info_fields, client_id=client_id)
            if res.get("status") == "success":
                data = res.get("data", {})
                return (
                    "client_info",
                    f"Berikut data profil Anda:\n"
                    f"- Nama Klien: {data.get('client_name')}\n"
                    f"- Perusahaan: {data.get('company_name') or '-'}\n"
                    f"- Nomor Telepon: {data.get('phone_number')}\n"
                    f"- Domain Resmi: {data.get('official_domain') or '-'}"
                )

        # 4. Tool 2: get_invoice_info (Tagihan / Billing)
        elif tool_name == "get_invoice_info":
            invoices = database.get_invoices_by_client_id(client_id)
            if not invoices:
                return (
                    "billing_info",
                    f"Tidak ditemukan invoice aktif untuk Client ID '{client_id}' di sistem kami."
                )
            lines = ["Berikut rincian tagihan Anda:"]
            total_outstanding = 0
            for inv in invoices:
                inv_no = inv.get("invoice_no")
                pkg = inv.get("package_name")
                tot = inv.get("total_amount", 0)
                paid = inv.get("amount_paid", 0)
                status = inv.get("payment_status")
                sisa = max(0, tot - paid)
                total_outstanding += sisa
                lines.append(
                    f"- Invoice {inv_no} ({pkg}): Total Rp{tot:,}, Sudah dibayar: Rp{paid:,}, "
                    f"Sisa: Rp{sisa:,} (Status: {status})"
                )
            lines.append(f"\nTotal sisa tagihan Anda saat ini adalah Rp{total_outstanding:,}.")
            return ("billing_info", "\n".join(lines))

        # 5. Tool 4: delete_conversation_history
        elif tool_name == "delete_conversation_history":
            result = gemini_tools.execute_tool_call("delete_conversation_history", {})
            return ("delete_conversation", result.get("message", ""))

        # 6. Tool 3: get_conversation_history
        elif tool_name == "get_conversation_history":
            result = gemini_tools.execute_tool_call("get_conversation_history", {})
            return ("conversation_history", f"Ditemukan {result.get('total_messages', 0)} riwayat pesan percakapan.")

        # 7. Tool 7: ask_general_knowledge (TC-01, TC-02, TC-07)
        elif tool_name == "ask_general_knowledge":
            kb_res = gemini_tools.ask_general_knowledge(query=message)
            if kb_res.get("status") == "found":
                return ("knowledge_retrieval", kb_res.get("content", ""))
            return ("general_fallback", kb_res.get("message", gemini_tools.GENERAL_KNOWLEDGE_FALLBACK_MSG))

    # Jika model mengembalikan jawaban teks langsung
    if tool_call_res and tool_call_res.get("type") == "text":
        text = tool_call_res.get("text", "").strip()
        if text:
            return ("general_knowledge", text)

    # General Fallback jika tidak ada informasi yang relevan
    kb_res = gemini_tools.ask_general_knowledge(query=message)
    if kb_res.get("status") == "found":
        return ("knowledge_retrieval", kb_res.get("content", ""))
    return ("general_fallback", kb_res.get("message", gemini_tools.GENERAL_KNOWLEDGE_FALLBACK_MSG))


def process_chat_message(
    client_id: str,
    message: str,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Eksekusi alur lengkap chat engine:
    1. Validasi keberadaan klien (404 jika tidak ditemukan)
    2. Validasi isi pesan (400 jika kosong)
    3. Validasi & isolasi sesi percakapan (periksa tabel conversation, buat jika belum ada, 403 jika milik klien lain)
    4. Set context session di gemini_tools
    5. Jalankan intent detection, policy check, & retrieval (mengikuti tool yang digunakan)
    6. Simpan pesan pengguna ke tabel chat_messages dengan detected_intent sesuai tool
    7. Simpan balasan assistant ke tabel chat_messages
    8. Kembalikan response terstruktur
    """
    client_id_clean = client_id.strip() if client_id else ""
    if not client_id_clean:
        raise ValueError("Client ID wajib disertakan dan tidak boleh kosong.")

    # 1. Validasi klien di database (HTTP 404 jika tidak ditemukan)
    client = database.get_client_by_id(client_id_clean)
    if not client:
        raise LookupError(f"Client '{client_id_clean}' tidak ditemukan di sistem.")

    # 2. Validasi pesan pengguna (HTTP 400 jika kosong)
    message_clean = message.strip() if message else ""
    if not message_clean:
        raise ValueError("Pesan tidak boleh kosong.")

    # 3. Pengelolaan & Isolasi Percakapan (README.md L236-L241, Kriteria 1)
    # Memeriksa apakah conversation_id sudah ada di tabel "conversations"/"conversation".
    # Jika belum ada di tabel, sesi baru akan dibuat secara otomatis.
    if conversation_id and conversation_id.strip():
        active_conv_id = conversation_id.strip()
        existing_conv = database.get_conversation_by_id(active_conv_id)
        if existing_conv:
            # Isolasi: Percakapan tidak boleh diakses oleh client_id lain (HTTP 403 Forbidden)
            if existing_conv.get("client_id") != client_id_clean:
                raise PermissionError(
                    f"Akses ditolak: Percakapan '{active_conv_id}' bukan milik klien '{client_id_clean}'."
                )
        else:
            # Jika conversation_id dikirim (misal dari local storage) tapi belum tercatat di DB, daftarkan sesi baru
            database.create_conversation(active_conv_id, client_id_clean)
    else:
        # Jika conversation_id tidak dikirim, generate ID percakapan baru
        active_conv_id = f"conv-{uuid.uuid4().hex[:10]}"
        database.create_conversation(active_conv_id, client_id_clean)

    # 4. Set konteks aktif pada modul gemini_tools
    gemini_tools.set_current_client_id(client_id_clean)
    gemini_tools.set_current_conversation_id(active_conv_id)
    gemini_tools.set_current_user_message(message_clean)

    # 5. Intent Detection, Policy Check, & Response Generation
    # Intent yang terdeteksi mengikuti nama tool yang digunakan
    detected_intent, bot_reply = detect_intent_and_generate_response(client_id_clean, message_clean)

    # 6. Simpan pesan pengguna ke database tabel chat_messages berdasarkan conversation_id di local storage.
    # Kolom detected_intent mencatat intent yang terdeteksi sesuai tool yang digunakan.
    user_turn = database.get_next_turn_index(active_conv_id)
    database.add_chat_message(
        conversation_id=active_conv_id,
        turn_index=user_turn,
        sender="user",
        message_text=message_clean,
        detected_intent=detected_intent
    )

    # 7. Simpan balasan respons dari chatbot ke database tabel chat_messages
    assistant_turn = database.get_next_turn_index(active_conv_id)
    database.add_chat_message(
        conversation_id=active_conv_id,
        turn_index=assistant_turn,
        sender="assistant",
        message_text=bot_reply,
        detected_intent=detected_intent
    )

    return {
        "conversation_id": active_conv_id,
        "client_id": client_id_clean,
        "response": bot_reply,
        "turn_index": assistant_turn,
        "detected_intent": detected_intent
    }
