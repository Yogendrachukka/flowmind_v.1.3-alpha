import pytest
from fastapi.testclient import TestClient

from flowmind.server import app

client = TestClient(app)

def test_chat_completions_no_keys():
    response = client.post("/v1/chat/completions", json={
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "hello"}]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert "no keys configured" in data["choices"][0]["message"]["content"]

def test_anthropic_messages_no_keys():
    response = client.post("/v1/messages", json={
        "model": "claude-3-sonnet",
        "messages": [{"role": "user", "content": "hello"}],
        "system": "you are a bot"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "assistant"
    assert "no keys configured" in data["content"][0]["text"]
