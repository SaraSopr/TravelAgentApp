from fastapi.testclient import TestClient

from app.main import app


def test_ops_endpoints_available() -> None:
    with TestClient(app) as client:
        plans_response = client.get("/api/ops/plans")
        assert plans_response.status_code == 200
        assert "plans" in plans_response.json()

        events_response = client.get("/api/ops/events")
        assert events_response.status_code == 200
        assert "events" in events_response.json()

        dlq_response = client.get("/api/ops/dlq")
        assert dlq_response.status_code == 200
        body = dlq_response.json()
        assert "backend" in body
        assert "events" in body
