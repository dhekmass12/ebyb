import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi import HTTPException

import database
from main import get_conversation


@pytest.fixture
def temp_conversation():
    test_conv_id = "test-conv-123"
    test_client_id = "CLI-001"
    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE conversation_id = ?", (test_conv_id,))
        cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (test_conv_id,))
        cursor.execute(
            """
            INSERT INTO conversations (conversation_id, client_id, created_at, updated_at)
            VALUES (?, ?, '2026-01-01 10:00:00', '2026-01-01 10:05:00')
            """,
            (test_conv_id, test_client_id),
        )
        conn.commit()
    finally:
        conn.close()

    yield {
        "conversation_id": test_conv_id,
        "client_id": test_client_id,
        "created_at": "2026-01-01 10:00:00",
        "updated_at": "2026-01-01 10:05:00",
    }

    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE conversation_id = ?", (test_conv_id,))
        cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (test_conv_id,))
        conn.commit()
    finally:
        conn.close()


def test_get_conversation_by_id_found(temp_conversation):
    conv_id = temp_conversation["conversation_id"]
    conv = database.get_conversation_by_id(conv_id)
    assert conv is not None
    assert conv["conversation_id"] == conv_id
    assert conv["client_id"] == temp_conversation["client_id"]
    assert conv["created_at"] == temp_conversation["created_at"]
    assert conv["updated_at"] == temp_conversation["updated_at"]


def test_get_conversation_by_id_not_found():
    conv = database.get_conversation_by_id("non-existent-conv-id-999")
    assert conv is None


def test_get_conversation_endpoint_success(temp_conversation):
    conv_id = temp_conversation["conversation_id"]
    res = get_conversation(conv_id)
    assert res["conversation_id"] == conv_id
    assert res["client_id"] == temp_conversation["client_id"]
    assert res["created_at"] == "2026-01-01 10:00:00"
    assert res["updated_at"] == "2026-01-01 10:05:00"
    assert "messages" in res
    assert isinstance(res["messages"], list)


def test_get_conversation_with_messages_and_limit(temp_conversation):
    conv_id = temp_conversation["conversation_id"]
    database.add_chat_message(conv_id, 1, "user", "Pesan 1", "test")
    database.add_chat_message(conv_id, 2, "assistant", "Balasan 1", "test")
    database.add_chat_message(conv_id, 3, "user", "Pesan 2", "test")

    res = get_conversation(conv_id, limit=2)
    assert res["conversation_id"] == conv_id
    assert len(res["messages"]) == 2
    assert res["messages"][0]["message_text"] == "Pesan 1"
    assert res["messages"][1]["message_text"] == "Balasan 1"


def test_get_conversation_endpoint_not_found():
    with pytest.raises(HTTPException) as exc_info:
        get_conversation("non-existent-conv-id-999")
    assert exc_info.value.status_code == 404
    assert "tidak ditemukan" in exc_info.value.detail


def test_get_conversation_endpoint_with_client_id_validation(temp_conversation):
    conv_id = temp_conversation["conversation_id"]

    # 1. Matching client_id -> 200 OK
    res = get_conversation(conv_id, client_id="CLI-001")
    assert res["conversation_id"] == conv_id

    # 2. Non-existent client_id -> 404 Not Found
    with pytest.raises(HTTPException) as exc_404:
        get_conversation(conv_id, client_id="CLI-NONEXISTENT")
    assert exc_404.value.status_code == 404
    assert "tidak ditemukan" in exc_404.value.detail

    # 3. Mismatched client_id -> 403 Forbidden
    with pytest.raises(HTTPException) as exc_403:
        get_conversation(conv_id, client_id="CLI-002")
    assert exc_403.value.status_code == 403
    assert "Akses ditolak" in exc_403.value.detail

