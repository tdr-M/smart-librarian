from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_recommend():
    r = client.post("/recommend", json={"query": "magic and friendship"})
    assert r.status_code == 200
    body = r.json()
    assert "title" in body
    assert "candidates" in body
