"""Test luồng đăng ký / đăng nhập / social login / phân quyền vai trò."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(username, password):
    return client.post("/auth/login", json={"username": username, "password": password})


def token_of(username, password="123456"):
    return login(username, password).json()["access_token"]


def auth(username="chunhiem", password="123456"):
    return {"Authorization": f"Bearer {token_of(username, password)}"}


# ---------------------------------------------------------------------------
# Đăng ký: bỏ chọn vai trò — mọi tài khoản mới đều là Thành viên
# ---------------------------------------------------------------------------

def test_register_defaults_to_member():
    resp = client.post(
        "/auth/register",
        json={
            "username": "sv_moi_1",
            "password": "pass123",
            "email": "svmoi1@ictu.edu.vn",
            "full_name": "Sinh Viên Mới Một",
            "date_of_birth": "2004-03-10",
            "gender": "Nữ",
            "class_name": "CNTT-K16A",
            "department": "Công nghệ thông tin",
        },
    )
    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    assert body["role"] == "thanh_vien"
    assert body["auth_provider"] == "local"


def test_register_rejects_self_chosen_admin_role():
    """Người dùng không được tự chọn vai trò Chủ nhiệm / Trưởng ban."""
    for role in ("chu_nhiem", "truong_ban"):
        resp = client.post(
            "/auth/register",
            json={
                "username": f"hack_{role}",
                "password": "pass123",
                "role": role,
                "full_name": "Hack Role",
                "date_of_birth": "2003-01-01",
                "gender": "Nam",
                "class_name": "CNTT-K15A",
                "department": "Công nghệ thông tin",
            },
        )
        assert resp.status_code == 400, resp.text


def test_register_accepts_explicit_member_role():
    resp = client.post(
        "/auth/register",
        json={
            "username": "sv_moi_2",
            "password": "pass123",
            "role": "thanh_vien",
            "full_name": "Sinh Viên Mới Hai",
            "date_of_birth": "2003-08-22",
            "gender": "Nam",
            "class_name": "KT-K15B",
            "department": "Kế toán",
        },
    )
    assert resp.status_code in (200, 201)
    assert resp.json()["role"] == "thanh_vien"


def test_register_creates_member_visible_to_leader():
    """Tài khoản mới phải xuất hiện ngay trong Danh sách thành viên."""
    username = "sv_moi_list"
    resp = client.post(
        "/auth/register",
        json={
            "username": username,
            "password": "pass123",
            "full_name": "Sinh Viên Danh Sách",
            "date_of_birth": "2004-06-15",
            "gender": "Khác",
            "class_name": "NNA-K17A",
            "department": "Ngôn ngữ Anh",
        },
    )
    assert resp.status_code in (200, 201), resp.text
    members = client.get("/members", headers=auth("chunhiem")).json()
    found = [m for m in members if m["full_name"] == "Sinh Viên Danh Sách"]
    assert found, "Thành viên mới phải hiển thị cho Chủ nhiệm"
    row = found[0]
    assert row["gender"] == "Khác"
    assert row["class_name"] == "NNA-K17A"
    assert row["department"] == "Ngôn ngữ Anh"
    assert row["date_of_birth"] == "2004-06-15"


def test_member_cannot_view_member_list():
    """Thành viên thường không được xem Danh sách thành viên (403)."""
    resp = client.get("/members", headers=auth("thanhvien"))
    assert resp.status_code == 403


def test_login_returns_member_id_and_token():
    resp = login("thanhvien", "123456")
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "thanh_vien"
    assert body["access_token"]
    assert body["member_id"] is not None


def test_auth_me_endpoint():
    resp = client.get("/auth/me", headers=auth("thanhvien"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "thanhvien"
    assert body["role"] == "thanh_vien"


# ---------------------------------------------------------------------------
# Social login (Google / Facebook / Discord)
# ---------------------------------------------------------------------------

def test_oauth_providers_listed():
    resp = client.get("/auth/oauth/providers")
    assert resp.status_code == 200
    providers = {p["provider"] for p in resp.json()["providers"]}
    assert {"google", "facebook", "discord"} <= providers
    assert resp.json()["default_role"] == "thanh_vien"


def test_oauth_demo_login_creates_member():
    resp = client.post(
        "/auth/oauth/demo",
        json={"provider": "google", "email": "social.new@gmail.com", "name": "Social New"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["role"] == "thanh_vien"
    assert body["is_new_user"] is True
    assert body["access_token"]


def test_oauth_demo_login_second_time_reuses_account():
    payload = {"provider": "facebook", "email": "fb.user@club.edu.vn", "name": "FB User"}
    first = client.post("/auth/oauth/demo", json=payload).json()
    second = client.post("/auth/oauth/demo", json=payload).json()
    assert first["user_id"] == second["user_id"]
    assert second["is_new_user"] is False


def test_oauth_demo_rejects_unknown_provider():
    resp = client.post("/auth/oauth/demo", json={"provider": "tiktok"})
    assert resp.status_code == 400


def test_oauth_login_requires_configuration():
    """Chưa đặt CLIENT_ID/SECRET thì endpoint redirect phải báo chưa cấu hình."""
    resp = client.get("/auth/oauth/google/login")
    assert resp.status_code == 400
    assert "Chưa cấu hình" in resp.json()["detail"]