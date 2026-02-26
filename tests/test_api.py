from fastapi.testclient import TestClient

from app.main import app


def _register_and_token(client: TestClient, username: str = "student") -> str:
    response = client.post("/api/auth/register", json={"username": username, "password": "pass12345"})
    if response.status_code == 409:
        response = client.post("/api/auth/login", json={"username": username, "password": "pass12345"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _register_and_tokens(client: TestClient, username: str = "student") -> tuple[str, str]:
    response = client.post("/api/auth/register", json={"username": username, "password": "pass12345"})
    if response.status_code == 409:
        response = client.post("/api/auth/login", json={"username": username, "password": "pass12345"})
    assert response.status_code == 200
    body = response.json()
    return body["access_token"], body["refresh_token"]


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_create_trip_endpoint() -> None:
    payload = {
        "user_id": "student-1",
        "city": "Milan",
        "intent": "visit landmarks and museums",
    }
    with TestClient(app) as client:
        token = _register_and_token(client, "student-create")
        response = client.post("/api/trips", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "accepted"
        assert "correlation_id" in body


def test_trip_detail_and_alerts_endpoints() -> None:
    payload = {
        "user_id": "student-2",
        "city": "Rome",
        "intent": "culture and food",
        "budget_level": "medium",
        "mobility_mode": "public_transport",
        "interests": ["culture", "food"],
    }
    with TestClient(app) as client:
        token = _register_and_token(client, "student-detail")
        auth = {"Authorization": f"Bearer {token}"}
        client.post("/api/trips", json=payload, headers=auth)
        plans = client.get("/api/trips", headers=auth).json()["plans"]
        assert len(plans) >= 1
        trip_id = plans[-1]["trip_id"]

        trip_response = client.get(f"/api/trips/{trip_id}", headers=auth)
        assert trip_response.status_code == 200
        assert trip_response.json()["found"] is True

        alerts_response = client.get(f"/api/trips/{trip_id}/alerts", headers=auth)
        assert alerts_response.status_code == 200
        assert "alerts" in alerts_response.json()


def test_auth_required_for_trip_creation() -> None:
    payload = {
        "city": "Milan",
        "intent": "test",
    }
    with TestClient(app) as client:
        response = client.post("/api/trips", json=payload)
        assert response.status_code == 401


def test_refresh_and_logout_flow() -> None:
    with TestClient(app) as client:
        access, refresh = _register_and_tokens(client, "student-refresh")

        refresh_response = client.post("/api/auth/refresh", json={"refresh_token": refresh})
        assert refresh_response.status_code == 200
        rotated = refresh_response.json()
        assert rotated["access_token"]
        assert rotated["refresh_token"]
        assert rotated["refresh_token"] != refresh

        logout_response = client.post(
            "/api/auth/logout",
            json={"refresh_token": rotated["refresh_token"]},
            headers={"Authorization": f"Bearer {rotated['access_token']}"},
        )
        assert logout_response.status_code == 200

        reused = client.post("/api/auth/refresh", json={"refresh_token": rotated["refresh_token"]})
        assert reused.status_code == 401


def test_login_rate_limit() -> None:
    with TestClient(app) as client:
        client.post("/api/auth/register", json={"username": "student-limit", "password": "pass12345"})

        status_codes = []
        for _ in range(10):
            response = client.post("/api/auth/login", json={"username": "student-limit", "password": "wrong-pass"})
            status_codes.append(response.status_code)
        assert 429 in status_codes


def test_auth_audit_endpoint() -> None:
    with TestClient(app) as client:
        client.post("/api/auth/register", json={"username": "student-audit", "password": "pass12345"})
        client.post("/api/auth/login", json={"username": "student-audit", "password": "pass12345"})
        response = client.get("/api/ops/auth-audit")
        assert response.status_code == 200
        records = response.json()["records"]
        assert isinstance(records, list)
        assert any(item["event_type"] in {"register_success", "login_success"} for item in records)


def test_frontend_root_page() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Travel Agent Assistant" in response.text
