import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi import HTTPException
from main import ClientLoginRequest, get_client, get_client_invoices, get_clients, get_invoices, login


def test_auth_login_success():
    req = ClientLoginRequest(client_id="CLI-001", password="anypassword")
    res = login(req)
    assert res["success"] is True
    assert res["client"]["client_id"] == "CLI-001"
    assert res["client"]["client_name"] == "Budi Santoso"


def test_auth_login_not_found():
    req = ClientLoginRequest(client_id="CLI-999", password="123")
    with pytest.raises(HTTPException) as exc_info:
        login(req)
    assert exc_info.value.status_code == 404
    assert "tidak ditemukan" in exc_info.value.detail


def test_auth_login_empty_client_id():
    req = ClientLoginRequest(client_id="   ", password="")
    with pytest.raises(HTTPException) as exc_info:
        login(req)
    assert exc_info.value.status_code == 400


def test_get_all_clients():
    clients = get_clients()
    assert len(clients) >= 3
    client_ids = [c["client_id"] for c in clients]
    assert "CLI-001" in client_ids
    assert "CLI-002" in client_ids
    assert "CLI-003" in client_ids


def test_get_client_detail():
    client = get_client("CLI-002")
    assert client["client_id"] == "CLI-002"
    assert client["client_name"] == "Rani Wijaya"


def test_get_client_invoices():
    invoices = get_client_invoices("CLI-001")
    assert len(invoices) >= 1
    assert invoices[0]["invoice_no"] == "INV-2026-001"
    assert invoices[0]["client_id"] == "CLI-001"
    assert invoices[0]["total_amount"] == 1600000
    assert invoices[0]["amount_paid"] == 800000
    assert invoices[0]["outstanding_balance"] == 800000


def test_get_invoices_with_filter():
    invoices = get_invoices(client_id="CLI-003")
    assert len(invoices) >= 1
    assert invoices[0]["invoice_no"] == "INV-2026-003"
    assert invoices[0]["payment_status"] == "unpaid"
