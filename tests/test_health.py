from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_cors_preflight_for_deployed_frontend() -> None:
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "https://orderflow-frontend-lkno.onrender.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "https://orderflow-frontend-lkno.onrender.com"
    )
    assert "GET" in response.headers["access-control-allow-methods"]


def test_cors_preflight_for_local_frontend() -> None:
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_unconfigured_origin() -> None:
    response = client.get(
        "/health",
        headers={"Origin": "https://not-orderflow.example"},
    )
    assert "access-control-allow-origin" not in response.headers
