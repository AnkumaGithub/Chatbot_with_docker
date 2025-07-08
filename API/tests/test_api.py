import asyncio

import pytest
from fastapi.testclient import TestClient
from src.api import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_text_cached(client, mocker):
    mocker.patch("api.find_similar_prompt", return_value={"response": "cached response"})

    response = client.post("/generate", json={"prompt": "test"})
    assert response.status_code == 200
    assert response.json() == "cached response"


def test_generate_text_timeout(client, mocker):
    mocker.patch("api.find_similar_prompt", return_value=None)
    mocker.patch("asyncio.wait_for", side_effect=asyncio.TimeoutError)

    response = client.post("/generate", json={"prompt": "test"})
    assert response.status_code == 200
    assert "timeout" in response.json().get("error", "")