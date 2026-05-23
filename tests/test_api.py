"""
Tests for the FastAPI server.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.server import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "DebugAI" in response.json()["message"]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_parse_only():
    response = client.post("/parse", json={
        "error_text": "ModuleNotFoundError: No module named 'requests'"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "Python"
    assert data["error_type"] == "ModuleNotFound"


def test_parse_javascript_error():
    response = client.post("/parse", json={
        "error_text": "TypeError: Cannot read properties of undefined (reading 'length')\n    at App (index.js:5:10)"
    })
    assert response.status_code == 200
    data = response.json()
    assert "JavaScript" in data["language"]


@patch("src.api.server.LLMClient")
def test_analyze_mocked(mock_llm_cls):
    mock_llm = MagicMock()
    mock_llm.analyze.return_value = {
        "explanation": "The module 'requests' is not installed.",
        "root_cause": "Missing dependency.",
        "fix_commands": [{"command": "pip install requests", "explanation": "Installs requests"}],
        "prevention": "Add to requirements.txt",
        "references": [{"title": "requests docs", "url": "https://docs.python-requests.org"}],
    }
    mock_llm_cls.return_value = mock_llm

    response = client.post("/analyze", json={
        "error_text": "ModuleNotFoundError: No module named 'requests'",
        "provider": "openai",
        "model": "gpt-4o-mini",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["error_type"] == "ModuleNotFound"
    assert data["language"] == "Python"
    assert len(data["fix_commands"]) >= 1
    assert data["fix_commands"][0]["command"] == "pip install requests"
