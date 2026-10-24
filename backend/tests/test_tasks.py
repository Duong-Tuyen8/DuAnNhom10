from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_user_token(username, password):
    r = client.post("/auth/login", json={"username": username, "password": password})
    return r.json()["access_token"]


def auth_admin():
    return {"Authorization": f"Bearer {get_user_token('chunhiem', '123456')}"}


def test_create_and_list_tasks():
    members = client.get("/members", headers=auth_admin()).json()
    member_id = members[0]["id"]

    r = client.post("/tasks", headers=auth_admin(), json={
        "title": "Thiết kế poster",
        "description": "Design event poster",
        "assignee_id": member_id,
        "priority": "high",
        "status": "todo",
    })
    assert r.status_code == 201
    task = r.json()
    assert task["title"] == "Thiết kế poster"

    lst = client.get("/tasks", headers=auth_admin())
    assert lst.status_code == 200
    ids = [t["id"] for t in lst.json()]
    assert task["id"] in ids


def test_task_status_update_by_member():
    # Create task as admin
    tasks = client.get("/tasks", headers=auth_admin()).json()
    task_id = tasks[0]["id"]

    # Member updates status (allowed)
    token = get_user_token("thanhvien", "123456")
    h = {"Authorization": f"Bearer {token}"}
    upd = client.put(f"/tasks/{task_id}", headers=h, json={"status": "in_progress"})
    assert upd.status_code == 200
    assert upd.json()["status"] == "in_progress"

    # Member CANNOT reassign
    forbidden = client.put(f"/tasks/{task_id}", headers=h, json={"assignee_id": 1})
    assert forbidden.status_code == 403


def test_task_delete():
    r = client.post("/tasks", headers=auth_admin(), json={"title": "Temp task"})
    tid = r.json()["id"]
    d = client.delete(f"/tasks/{tid}", headers=auth_admin())
    assert d.status_code == 204