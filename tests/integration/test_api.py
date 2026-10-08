import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_calculate_contract(client):
    response = client.post("/api/calculate", json={"a": 6, "b": 7, "operation": "multiply"})
    assert response.status_code == 200
    assert response.json() == {"result": 42}


@pytest.mark.parametrize("changes,field", [
    ({"a": True}, "a"), ({"a": "6"}, "a"), ({"a": None}, "a"),
    ({"a": 1_000_001}, "a"), ({"b": -1_000_001}, "b"),
    ({"operation": "power"}, "operation"), ({"extra": 1}, "extra"),
])
def test_rejects_invalid_request(client, changes, field):
    data = {"a": 6, "b": 7, "operation": "multiply"} | changes
    response = client.post("/api/calculate", json=data)
    assert response.status_code == 422
    assert any(error["loc"][-1] == field for error in response.json()["detail"])


def test_missing_operand(client):
    response = client.post("/api/calculate", json={"a": 6, "operation": "add"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "b"]


@pytest.mark.parametrize("value", ["NaN", "Infinity", "1e999"])
def test_non_finite_input_returns_validation_error_not_server_error(client, value):
    response = client.post(
        "/api/calculate", content='{"a":' + value + ',"b":1,"operation":"add"}',
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "a"]


@pytest.mark.parametrize("b,code", [(0, "division_by_zero"), (-0.0, "division_by_zero"), (5e-324, "non_finite_result")])
def test_arithmetic_errors(client, b, code):
    response = client.post("/api/calculate", json={"a": 1, "b": b, "operation": "divide"})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == code


def test_health_identifies_release(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_COMMIT", "a" * 40)
    monkeypatch.setenv("APP_BUILT_AT", "2026-09-17T18:00:00Z")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok", "environment": "test", "commit": "a" * 40,
        "built_at": "2026-09-17T18:00:00Z",
    }


@pytest.mark.parametrize("path,view", [("/", "home"), ("/calculator", "calculator")])
def test_page_routes(client, path, view):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["cache-control"] == "no-store"
    assert f'data-page="{view}"' in response.text
    assert "__PAGE__" not in response.text
