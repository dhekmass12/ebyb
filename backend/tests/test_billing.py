import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi import HTTPException
from billing import PaymentConfirmationRequest, process_client_billing, validate_invoice_consistency
from main import get_billing_info


def test_billing_cli_001_half_paid():
    # CLI-001: INV-2026-001, total=1600000, amount_paid=800000, status='half_paid'
    res = get_billing_info("CLI-001")
    assert res == {
        "total_payment": 800000,
        "total_outstanding_balance": 800000,
        "valid": True,
    }


def test_billing_cli_002_paid():
    # CLI-002: INV-2026-002, total=600000, amount_paid=600000, status='paid'
    res = get_billing_info("CLI-002")
    assert res == {
        "total_payment": 600000,
        "total_outstanding_balance": 0,
        "valid": True,
    }


def test_billing_cli_003_unpaid():
    # CLI-003: INV-2026-003, total=3000000, amount_paid=0, status='unpaid'
    res = get_billing_info("CLI-003")
    assert res == {
        "total_payment": 0,
        "total_outstanding_balance": 3000000,
        "valid": True,
    }


def test_billing_client_not_found():
    with pytest.raises(HTTPException) as exc_info:
        get_billing_info("CLI-999")
    assert exc_info.value.status_code == 404


def test_rule_1_unpaid_violations():
    # unpaid tapi amount_paid > 0
    inv1 = {"invoice_no": "INV-TEST-1", "payment_status": "unpaid", "total_amount": 100000, "amount_paid": 50000}
    assert validate_invoice_consistency(inv1) is False
    res = process_client_billing([inv1])
    assert res == {"valid": False, "invoice_no": "INV-TEST-1"}

    # unpaid tapi total_amount <= 0
    inv2 = {"invoice_no": "INV-TEST-2", "payment_status": "unpaid", "total_amount": 0, "amount_paid": 0}
    assert validate_invoice_consistency(inv2) is False
    res = process_client_billing([inv2])
    assert res == {"valid": False, "invoice_no": "INV-TEST-2"}


def test_rule_2_half_paid_violations():
    # half_paid tapi amount_paid == 0
    inv1 = {"invoice_no": "INV-TEST-3", "payment_status": "half_paid", "total_amount": 100000, "amount_paid": 0}
    assert validate_invoice_consistency(inv1) is False
    res = process_client_billing([inv1])
    assert res == {"valid": False, "invoice_no": "INV-TEST-3"}

    # half_paid tapi total_amount <= amount_paid
    inv2 = {"invoice_no": "INV-TEST-4", "payment_status": "half_paid", "total_amount": 100000, "amount_paid": 100000}
    assert validate_invoice_consistency(inv2) is False
    res = process_client_billing([inv2])
    assert res == {"valid": False, "invoice_no": "INV-TEST-4"}


def test_rule_3_paid_violations():
    # paid tapi total_amount != amount_paid
    inv1 = {"invoice_no": "INV-TEST-5", "payment_status": "paid", "total_amount": 100000, "amount_paid": 50000}
    assert validate_invoice_consistency(inv1) is False
    res = process_client_billing([inv1])
    assert res == {"valid": False, "invoice_no": "INV-TEST-5"}


def test_multiple_invoices_aggregation():
    invoices = [
        {"invoice_no": "INV-A", "payment_status": "paid", "total_amount": 50000, "amount_paid": 50000},
        {"invoice_no": "INV-B", "payment_status": "half_paid", "total_amount": 100000, "amount_paid": 30000},
        {"invoice_no": "INV-C", "payment_status": "unpaid", "total_amount": 20000, "amount_paid": 0},
    ]
    res = process_client_billing(invoices)
    assert res == {
        "total_payment": 80000,  # 50000 + 30000 + 0
        "total_outstanding_balance": 90000,  # 0 + 70000 + 20000
        "valid": True,
    }


# ==============================================================================
# Model PaymentConfirmationRequest Validation Tests (README.md:L194-L200)
# ==============================================================================

def test_payment_confirmation_request_valid():
    req = PaymentConfirmationRequest(
        client_id="CLI-001",
        invoice_no="INV-2026-001",
        nominal_transfer=500000,
        bank_tujuan="BCA",
        nama_rekening_pengirim="Budi Santoso"
    )
    assert req.client_id == "CLI-001"
    assert req.invoice_no == "INV-2026-001"
    assert req.nominal_transfer == 500000
    assert req.bank_tujuan == "BCA"
    assert req.nama_rekening_pengirim == "Budi Santoso"


def test_payment_confirmation_request_invalid_client_id():
    with pytest.raises(ValueError):
        PaymentConfirmationRequest(
            client_id="   ",
            invoice_no="INV-2026-001",
            nominal_transfer=500000,
            bank_tujuan="BCA",
            nama_rekening_pengirim="Budi"
        )


def test_payment_confirmation_request_invalid_invoice_no():
    # Format harus INV-YYYY-NNN
    invalid_invoices = ["INV-2026", "INV2026001", "INVOICE-001", "INV-202-001", "INV-2026-01"]
    for inv_no in invalid_invoices:
        with pytest.raises(ValueError):
            PaymentConfirmationRequest(
                client_id="CLI-001",
                invoice_no=inv_no,
                nominal_transfer=500000,
                bank_tujuan="BCA",
                nama_rekening_pengirim="Budi"
            )


def test_payment_confirmation_request_invalid_nominal():
    # 0 atau negatif
    for nom in [0, -1000, -1]:
        with pytest.raises(ValueError):
            PaymentConfirmationRequest(
                client_id="CLI-001",
                invoice_no="INV-2026-001",
                nominal_transfer=nom,
                bank_tujuan="BCA",
                nama_rekening_pengirim="Budi"
            )


def test_payment_confirmation_request_invalid_bank():
    # Bukan BCA, MANDIRI, BRI
    for bank in ["BNI", "CIMB", "DANAMON", "GOPAY"]:
        with pytest.raises(ValueError):
            PaymentConfirmationRequest(
                client_id="CLI-001",
                invoice_no="INV-2026-001",
                nominal_transfer=500000,
                bank_tujuan=bank,
                nama_rekening_pengirim="Budi"
            )


def test_payment_confirmation_request_invalid_sender_name():
    # Kurang dari 3 karakter non-spasi
    for name in ["", "  ", "ab", "a ", " a "]:
        with pytest.raises(ValueError):
            PaymentConfirmationRequest(
                client_id="CLI-001",
                invoice_no="INV-2026-001",
                nominal_transfer=500000,
                bank_tujuan="BCA",
                nama_rekening_pengirim=name
            )

