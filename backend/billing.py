import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class PaymentConfirmationRequest(BaseModel):
    """
    Model Pydantic v2 untuk validasi konfirmasi pembayaran klien.
    
    Ketentuan sesuai README.md:L194-L200:
    - client_id: wajib diisi dan harus terdaftar (validasi DB pada service layer).
    - invoice_no: format INV-YYYY-NNN.
    - nominal_transfer: integer positif (> 0).
    - bank_tujuan: BCA, MANDIRI, atau BRI.
    - nama_rekening_pengirim: minimal 3 karakter non-spasi.
    """
    client_id: str = Field(..., description="ID Klien yang wajib terdaftar")
    invoice_no: str = Field(..., description="Nomor invoice dengan format INV-YYYY-NNN")
    nominal_transfer: int = Field(..., gt=0, description="Nominal transfer berupa integer positif (> 0)")
    bank_tujuan: str = Field(..., description="Bank tujuan transfer: BCA, MANDIRI, atau BRI")
    nama_rekening_pengirim: str = Field(..., description="Nama rekening pengirim minimal 3 karakter non-spasi")

    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("client_id wajib diisi dan tidak boleh kosong.")
        return v.strip()

    @field_validator("invoice_no")
    @classmethod
    def validate_invoice_no(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("invoice_no wajib diisi.")
        v_clean = v.strip().upper()
        if not re.match(r"^INV-\d{4}-\d{3}$", v_clean):
            raise ValueError(f"Format invoice_no '{v}' tidak valid. Harus berformat INV-YYYY-NNN (contoh: INV-2026-001).")
        return v_clean

    @field_validator("nominal_transfer")
    @classmethod
    def validate_nominal_transfer(cls, v: Any) -> int:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError("nominal_transfer harus berupa bilangan bulat (integer).")
        if v <= 0:
            raise ValueError(f"Nominal transfer tidak valid ({v}). Nominal transfer harus lebih besar dari 0.")
        return v

    @field_validator("bank_tujuan")
    @classmethod
    def validate_bank_tujuan(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("bank_tujuan wajib diisi.")
        v_clean = v.strip().upper()
        if v_clean not in {"BCA", "MANDIRI", "BRI"}:
            raise ValueError(f"bank_tujuan '{v}' tidak valid. Bank tujuan yang didukung: BCA, MANDIRI, BRI.")
        return v_clean

    @field_validator("nama_rekening_pengirim")
    @classmethod
    def validate_nama_rekening_pengirim(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("nama_rekening_pengirim wajib diisi.")
        v_clean = v.strip()
        non_space = v_clean.replace(" ", "")
        if len(non_space) < 3:
            raise ValueError("nama_rekening_pengirim harus memiliki minimal 3 karakter non-spasi.")
        return v_clean


def validate_invoice_consistency(invoice: Dict[str, Any]) -> bool:
    """
    Memvalidasi konsistensi status pembayaran invoice terhadap nominal:
    1. payment_status == "unpaid": amount_paid == 0 dan total_amount > 0
    2. payment_status == "half_paid": total_amount > amount_paid dan amount_paid > 0
    3. payment_status == "paid": total_amount == amount_paid
    """
    status = invoice.get("payment_status")
    total = invoice.get("total_amount", 0)
    paid = invoice.get("amount_paid", 0)

    if status == "unpaid":
        return paid == 0 and total > 0
    elif status == "half_paid":
        return total > paid and paid > 0
    elif status == "paid":
        return total == paid
    return False


def process_client_billing(invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Memeriksa semua invoice milik klien:
    - Jika ada invoice yang tidak konsisten, kembalikan:
      {"valid": False, "invoice_no": invoice_no}
    - Jika semua konsisten, hitung total pembayaran dan total sisa tagihan:
      {"total_payment": total_payment, "total_outstanding_balance": total_outstanding_balance, "valid": True}
    """
    total_payment = 0
    total_outstanding_balance = 0

    for inv in invoices:
        invoice_no = inv.get("invoice_no")
        if not validate_invoice_consistency(inv):
            return {
                "valid": False,
                "invoice_no": invoice_no,
            }

        paid = inv.get("amount_paid", 0)
        total = inv.get("total_amount", 0)
        total_payment += paid
        total_outstanding_balance += (total - paid)

    return {
        "total_payment": total_payment,
        "total_outstanding_balance": total_outstanding_balance,
        "valid": True,
    }


