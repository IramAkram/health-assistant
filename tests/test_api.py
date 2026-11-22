"""End-to-end API tests (needs: pip install -r requirements.txt)."""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_health.db"
os.environ["OPENAI_API_KEY"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_full_flow():
    with TestClient(app) as c:
        email = "tester@example.com"
        c.post("/api/auth/register", json={"email": email, "full_name": "Test User", "password": "Passw0rd!x",
                                           "date_of_birth": "1995-01-01", "height_cm": 170})
        token = c.post("/api/auth/login", data={"username": email, "password": "Passw0rd!x"}).json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        r = c.post("/api/records", json={"systolic": 185, "diastolic": 122, "glucose": 110, "weight_kg": 80}, headers=h)
        assert r.status_code == 201 and r.json()["alerts"][0]["severity"] == "critical"
        assert c.post("/api/records", json={}, headers=h).status_code == 422
        assert c.get("/api/dashboard?period=weekly", headers=h).json()["summary"]["record_count"] == 1
        assert c.get("/api/risk/diabetes", headers=h).status_code == 200
        chat = c.post("/api/assistant/chat", json={"message": "summarise my trends"}, headers=h).json()
        assert chat["mode"] == "demo"
        assert c.get("/api/reports/pdf?days=7", headers=h).content.startswith(b"%PDF")
        assert c.get("/api/admin/stats", headers=h).status_code == 403   # normal user is not admin
        assert c.get("/api/records").status_code == 401                  # no token
