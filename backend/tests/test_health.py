import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import database
from main import health_check


def test_health_check_success():
    res = health_check()
    assert res == {
        "status": "healthy",
        "server": "running",
        "database": "connected",
    }


def test_health_check_db_failure(monkeypatch):
    monkeypatch.setattr(database, "check_db_health", lambda: (False, "Connection error"))
    res = health_check()
    assert res.status_code == 503
    body = json.loads(res.body.decode("utf-8"))
    assert body["status"] == "unhealthy"
    assert body["server"] == "running"
    assert body["database"] == "disconnected"
    assert body["details"] == "Connection error"
