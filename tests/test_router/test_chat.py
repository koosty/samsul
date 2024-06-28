from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_read_chat_completions():
    response = client.get("/chat/completions")
    assert response.status_code == 200
    assert response.json() == 'chat'