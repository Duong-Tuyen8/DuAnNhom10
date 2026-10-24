"""
OAuth 2.0 social login (Google / Facebook / Discord).

Thiết kế:
- Nếu biến môi trường CLIENT_ID/SECRET của provider được cấu hình, hệ thống
  chạy luồng OAuth thật (authorization code flow) qua `build_authorize_url` +
  `exchange_code`.
- Nếu chưa cấu hình, hệ thống vẫn hoạt động ở *chế độ demo offline*: endpoint
  `/auth/oauth/demo` tạo tài khoản mạng xã hội giả lập (vai trò Thành viên) để
  có thể demo/test tính năng mà không cần API key.

Biến môi trường:
    GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET
    FACEBOOK_CLIENT_ID / FACEBOOK_CLIENT_SECRET
    DISCORD_CLIENT_ID / DISCORD_CLIENT_SECRET
    OAUTH_REDIRECT_BASE    (mặc định http://localhost:8000)
    OAUTH_SUCCESS_REDIRECT (nơi frontend nhận token, mặc định "/")
"""
import os
from typing import Dict, Optional
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException

# Tên provider -> cấu hình endpoint
PROVIDERS: Dict[str, dict] = {
    "google": {
        "label": "Google",
        "icon": "🔍",
        "env_id": "GOOGLE_CLIENT_ID",
        "env_secret": "GOOGLE_CLIENT_SECRET",
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid email profile",
        "extra_authorize_params": {"access_type": "online", "prompt": "select_account"},
    },
    "facebook": {
        "label": "Facebook",
        "icon": "📘",
        "env_id": "FACEBOOK_CLIENT_ID",
        "env_secret": "FACEBOOK_CLIENT_SECRET",
        "authorize_url": "https://www.facebook.com/v19.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v19.0/oauth/access_token",
        "userinfo_url": "https://graph.facebook.com/me?fields=id,name,email",
        "scope": "email public_profile",
        "extra_authorize_params": {},
    },
    "discord": {
        "label": "Discord",
        "icon": "🎮",
        "env_id": "DISCORD_CLIENT_ID",
        "env_secret": "DISCORD_CLIENT_SECRET",
        "authorize_url": "https://discord.com/api/oauth2/authorize",
        "token_url": "https://discord.com/api/oauth2/token",
        "userinfo_url": "https://discord.com/api/users/@me",
        "scope": "identify email",
        "extra_authorize_params": {"prompt": "consent"},
    },
}

SUPPORTED_PROVIDERS = tuple(PROVIDERS.keys())


def get_provider(provider: str) -> dict:
    config = PROVIDERS.get((provider or "").lower())
    if not config:
        raise HTTPException(
            status_code=400,
            detail=f"Provider không hợp lệ. Chỉ hỗ trợ: {', '.join(SUPPORTED_PROVIDERS)}",
        )
    return config


def client_id(provider: str) -> str:
    return os.getenv(get_provider(provider)["env_id"], "").strip()


def client_secret(provider: str) -> str:
    return os.getenv(get_provider(provider)["env_secret"], "").strip()


def is_configured(provider: str) -> bool:
    """True nếu đã có CLIENT_ID + CLIENT_SECRET cho provider."""
    return bool(client_id(provider)) and bool(client_secret(provider))


def redirect_uri(provider: str) -> str:
    base = os.getenv("OAUTH_REDIRECT_BASE", "http://localhost:8000").rstrip("/")
    return f"{base}/auth/oauth/{provider}/callback"


def success_redirect_url() -> str:
    return os.getenv("OAUTH_SUCCESS_REDIRECT", "/")


def build_authorize_url(provider: str, state: str) -> str:
    """Tạo URL chuyển hướng người dùng sang trang đăng nhập của provider."""
    config = get_provider(provider)
    params = {
        "client_id": client_id(provider),
        "redirect_uri": redirect_uri(provider),
        "response_type": "code",
        "scope": config["scope"],
        "state": state,
        **config.get("extra_authorize_params", {}),
    }
    return f"{config['authorize_url']}?{urlencode(params)}"


def _normalize_userinfo(provider: str, raw: dict) -> dict:
    """Chuẩn hoá dữ liệu người dùng trả về từ từng provider."""
    if provider == "google":
        return {
            "provider_user_id": str(raw.get("sub") or raw.get("id") or ""),
            "email": raw.get("email") or "",
            "name": raw.get("name") or "",
        }
    if provider == "facebook":
        return {
            "provider_user_id": str(raw.get("id") or ""),
            "email": raw.get("email") or "",
            "name": raw.get("name") or "",
        }
    if provider == "discord":
        return {
            "provider_user_id": str(raw.get("id") or ""),
            "email": raw.get("email") or "",
            "name": raw.get("global_name") or raw.get("username") or "",
        }
    return {"provider_user_id": "", "email": "", "name": ""}


def exchange_code(provider: str, code: str) -> dict:
    """Đổi authorization code lấy access token rồi lấy thông tin người dùng."""
    config = get_provider(provider)
    data = {
        "client_id": client_id(provider),
        "client_secret": client_secret(provider),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri(provider),
    }
    headers = {"Accept": "application/json"}
    try:
        with httpx.Client(timeout=30) as client:
            token_resp = client.post(config["token_url"], data=data, headers=headers)
            token_resp.raise_for_status()
            access_token = token_resp.json().get("access_token")
            if not access_token:
                raise HTTPException(
                    status_code=400, detail="Không lấy được access token từ provider"
                )

            user_resp = client.get(
                config["userinfo_url"],
                headers={**headers, "Authorization": f"Bearer {access_token}"},
            )
            user_resp.raise_for_status()
            raw = user_resp.json()
    except HTTPException:
        raise
    except httpx.HTTPError as exc:  # pragma: no cover - phụ thuộc mạng
        raise HTTPException(
            status_code=400,
            detail=f"Không thể xác thực với {config['label']}: {exc}",
        )

    info = _normalize_userinfo(provider, raw)
    info["provider"] = provider
    return info


def demo_userinfo(
    provider: str,
    email: Optional[str] = None,
    name: Optional[str] = None,
    provider_user_id: Optional[str] = None,
) -> dict:
    """Sinh dữ liệu người dùng giả lập cho chế độ demo offline."""
    get_provider(provider)
    email = (email or "").strip() or f"{provider}.demo@club.edu.vn"
    name = (name or "").strip() or email.split("@")[0]
    return {
        "provider": provider,
        "provider_user_id": provider_user_id or f"demo-{provider}-{email.split('@')[0]}",
        "email": email,
        "name": name,
    }


def providers_status() -> list:
    """Danh sách provider kèm trạng thái cấu hình (cho frontend render nút)."""
    return [
        {
            "provider": name,
            "label": config["label"],
            "icon": config["icon"],
            "configured": is_configured(name),
        }
        for name, config in PROVIDERS.items()
    ]