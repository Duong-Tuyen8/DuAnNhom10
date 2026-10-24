from fastapi.testclient import TestClient
from app.main import app
import os

client = TestClient(app)


def get_token():
    """Login as chu_nhiem and return a bearer token."""
    r = client.post("/auth/login", json={"username": "chunhiem", "password": "123456"})
    return r.json()["access_token"]


def auth(token=None):
    return {"Authorization": f"Bearer {token or get_token()}"}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def _register_payload(username, role="thanh_vien"):
    return {
        "username": username,
        "password": "pass123",
        "role": role,
        "full_name": "Nguyễn Văn Test",
        "date_of_birth": "2003-05-12",
        "gender": "Nam",
        "class_name": "CNTT-K15A",
        "department": "Công nghệ thông tin",
    }


def test_register_and_login():
    # Register
    rr = client.post("/auth/register", json=_register_payload("test_user1"))
    assert rr.status_code in (200, 201, 400)  # 400 if exists
    # Login
    r = client.post("/auth/login", json={"username": "test_user1", "password": "pass123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_register_wrong_role():
    r = client.post("/auth/register", json=_register_payload("bad", role="super_admin"))
    assert r.status_code == 400


def test_register_missing_profile_rejected():
    """Thiếu hồ sơ bắt buộc (họ tên/ngày sinh/giới tính/lớp/khoa) phải bị từ chối."""
    r = client.post("/auth/register", json={"username": "thieu_hoso", "password": "pass123"})
    assert r.status_code == 422
    bad_gender = _register_payload("sai_gioitinh")
    bad_gender["gender"] = "Unknown"
    r2 = client.post("/auth/register", json=bad_gender)
    assert r2.status_code == 422


def test_login_wrong_password():
    r = client.post("/auth/login", json={"username": "chunhiem", "password": "wrongpw"})
    assert r.status_code == 401


def test_create_and_list_committees():
    r = client.post("/committees", json={"name": "Ban IT", "description": "Technical"}, headers=auth())
    assert r.status_code in (200, 201)
    lst = client.get("/committees", headers=auth())
    assert lst.status_code == 200
    names = [c["name"] for c in lst.json()]
    assert "Ban IT" in names


def test_without_auth_rejected():
    r = client.get("/committees")
    assert r.status_code in (401, 403)