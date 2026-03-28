from fastapi.testclient import TestClient

from src.database import Base, engine
from src.main import app


def test_task_match_and_rating_flow() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)

    employer_register = client.post("/api/auth/register", json={"username": "employer", "password": "pass1234"})
    worker_register = client.post("/api/auth/register", json={"username": "worker", "password": "pass1234"})
    assert employer_register.status_code == 200
    assert worker_register.status_code == 200

    employer_token = client.post("/api/auth/login", json={"username": "employer", "password": "pass1234"}).json()["data"][
        "access_token"
    ]
    worker_token = client.post("/api/auth/login", json={"username": "worker", "password": "pass1234"}).json()["data"][
        "access_token"
    ]
    employer_headers = {"Authorization": f"Bearer {employer_token}"}
    worker_headers = {"Authorization": f"Bearer {worker_token}"}

    create_task_resp = client.post(
        "/api/tasks",
        json={"title": "demo-task", "description": "do something", "reward_points": 100},
        headers=employer_headers,
    )
    assert create_task_resp.status_code == 200
    task_id = create_task_resp.json()["data"]["id"]

    accept_resp = client.post(f"/api/tasks/{task_id}/accept", headers=worker_headers)
    assert accept_resp.status_code == 200
    assert accept_resp.json()["data"]["status"] == "IN_PROGRESS"

    submit_resp = client.post(
        f"/api/tasks/{task_id}/submit",
        json={"result_payload": "{\"result\": \"ok\"}"},
        headers=worker_headers,
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["data"]["status"] == "SUBMITTED"

    rate_resp = client.post(
        f"/api/tasks/{task_id}/rate",
        json={"rating": 9, "comment": "great"},
        headers=employer_headers,
    )
    assert rate_resp.status_code == 200
    assert rate_resp.json()["data"]["status"] == "COMPLETED"

    summary_resp = client.get("/api/agents/me/reputation-summary", headers=worker_headers)
    assert summary_resp.status_code == 200
    assert summary_resp.json()["data"]["total_completed_tasks"] == 1
    assert summary_resp.json()["data"]["average_rating"] == 9.0
