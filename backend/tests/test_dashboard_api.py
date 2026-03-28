from fastapi.testclient import TestClient

from src.database import Base, engine
from src.main import app


def _register_and_login(client: TestClient, username: str, password: str) -> str:
    register_resp = client.post("/api/auth/register", json={"username": username, "password": password})
    assert register_resp.status_code == 200
    token_resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert token_resp.status_code == 200
    return token_resp.json()["data"]["access_token"]


def _complete_task(
    client: TestClient,
    employer_token: str,
    worker_token: str,
    title: str,
    reward_points: int,
    rating: int,
) -> None:
    employer_headers = {"Authorization": f"Bearer {employer_token}"}
    worker_headers = {"Authorization": f"Bearer {worker_token}"}

    create_resp = client.post(
        "/api/tasks",
        json={"title": title, "description": "dashboard-test", "reward_points": reward_points},
        headers=employer_headers,
    )
    assert create_resp.status_code == 200
    task_id = create_resp.json()["data"]["id"]

    accept_resp = client.post(f"/api/tasks/{task_id}/accept", headers=worker_headers)
    assert accept_resp.status_code == 200
    submit_resp = client.post(
        f"/api/tasks/{task_id}/submit",
        json={"result_payload": "{\"ok\": true}"},
        headers=worker_headers,
    )
    assert submit_resp.status_code == 200
    rate_resp = client.post(
        f"/api/tasks/{task_id}/rate",
        json={"rating": rating, "comment": "done"},
        headers=employer_headers,
    )
    assert rate_resp.status_code == 200


def test_dashboard_overview_and_leaderboards() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)

    employer_token = _register_and_login(client, "emp001", "pass1234")
    worker_a_token = _register_and_login(client, "worker001", "pass1234")
    worker_b_token = _register_and_login(client, "worker002", "pass1234")

    _complete_task(client, employer_token, worker_a_token, "task-1", 100, 10)
    _complete_task(client, employer_token, worker_a_token, "task-2", 80, 8)
    _complete_task(client, employer_token, worker_b_token, "task-3", 60, 9)

    overview_resp = client.get("/api/dashboard/overview")
    assert overview_resp.status_code == 200
    overview_data = overview_resp.json()["data"]
    assert overview_data["total_agents"] == 3
    assert overview_data["total_tasks"] == 3
    assert overview_data["total_completed_tasks"] == 3
    assert overview_data["total_transferred_points"] == 240
    assert overview_data["total_points_supply"] == 3000

    points_board_resp = client.get("/api/dashboard/leaderboards/agent-points?limit=3")
    assert points_board_resp.status_code == 200
    points_board = points_board_resp.json()["data"]
    assert len(points_board) == 3
    assert points_board[0]["username"] == "worker001"
    assert points_board[0]["points"] == 1180
    assert points_board[-1]["username"] == "emp001"
    assert points_board[-1]["points"] == 760

    rating_board_resp = client.get("/api/dashboard/leaderboards/agent-ratings?limit=3")
    assert rating_board_resp.status_code == 200
    rating_board = rating_board_resp.json()["data"]
    assert len(rating_board) == 2
    assert rating_board[0]["username"] == "worker001"
    assert rating_board[0]["average_rating"] == 9.0
    assert rating_board[0]["completed_tasks"] == 2
    assert rating_board[1]["username"] == "worker002"
    assert rating_board[1]["average_rating"] == 9.0
    assert rating_board[1]["completed_tasks"] == 1

    deals_board_resp = client.get("/api/dashboard/leaderboards/agent-deals?limit=3")
    assert deals_board_resp.status_code == 200
    deals_board = deals_board_resp.json()["data"]
    assert len(deals_board) == 2
    assert deals_board[0]["username"] == "worker001"
    assert deals_board[0]["completed_tasks"] == 2
    assert deals_board[0]["total_earned_points"] == 180
