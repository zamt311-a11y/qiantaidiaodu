import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("BOOTSTRAP_ADMIN_PHONE", "13800000000")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "admin123")
os.environ.setdefault("BOOTSTRAP_ADMIN_NAME", "管理员")


@pytest.fixture()
def client():
    db_path = Path(__file__).resolve().parents[1] / "test.db"
    if db_path.exists():
        db_path.unlink()

    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c

    from app.db.session import engine

    engine.dispose()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture()
def admin_token(client: TestClient) -> str:
    res = client.post("/api/auth/login", json={"phone": "13800000000", "password": "admin123"})
    assert res.status_code == 200
    return res.json()["access_token"]

