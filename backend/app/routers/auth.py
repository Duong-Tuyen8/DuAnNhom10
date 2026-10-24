from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote, urlencode

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import oauth
from ..database import get_db
from ..models import DEFAULT_ROLE, Member, User
from ..schemas import (
    SocialLoginRequest,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
)
from ..security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    get_current_user,
    hash_password,
    unusable_password_hash,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Các vai trò được phép tự đăng ký. Mọi tài khoản mới (kể cả social login)
# đều mặc định là Thành viên.
SELF_REGISTER_ROLES = (None, "", "thanh_vien", "member")


def _issue_token(user: User, is_new_user: bool = False) -> Token:
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        username=user.username,
        user_id=user.id,
        member_id=user.member_id,
        is_new_user=is_new_user,
    )


def _unique_username(db: Session, base: str) -> str:
    """Sinh username không trùng từ email/tên hiển thị của tài khoản social."""
    slug = "".join(ch if ch.isalnum() or ch in "._-" else "." for ch in (base or "user")).strip(".")
    slug = slug or "user"
    candidate = slug
    index = 1
    while db.query(User).filter(User.username == candidate).first():
        index += 1
        candidate = f"{slug}{index}"
    return candidate


def _find_or_create_social_user(db: Session, info: dict) -> tuple:
    """Tìm hoặc tạo user từ thông tin provider trước khi phát hành JWT.

    Tài khoản tạo mới qua social login luôn nhận vai trò mặc định là
    Thành viên (`thanh_vien`).
    """
    provider = info["provider"]
    provider_user_id = info.get("provider_user_id") or ""
    email = (info.get("email") or "").strip().lower()
    name = (info.get("name") or "").strip()

    user = None
    if provider_user_id:
        user = (
            db.query(User)
            .filter(User.auth_provider == provider, User.provider_user_id == provider_user_id)
            .first()
        )
    if user is None and email:
        user = db.query(User).filter(User.email == email).first()

    if user is not None:
        # Cập nhật thông tin hồ sơ social nếu còn thiếu
        if not user.email and email:
            user.email = email
        if not user.full_name and name:
            user.full_name = name
        db.commit()
        db.refresh(user)
        return user, False

    username = _unique_username(db, email.split("@")[0] if email else (name or provider))
    user = User(
        username=username,
        password_hash=unusable_password_hash(),
        role=DEFAULT_ROLE,  # luôn là Thành viên
        email=email or None,
        full_name=name or None,
        auth_provider=provider,
        provider_user_id=provider_user_id or None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, True


@router.post("/register", response_model=UserOut)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Đăng ký tài khoản thường + tự tạo hồ sơ thành viên gắn liền.

    Giao diện đã bỏ phần chọn vai trò: mọi tài khoản mới đều là **Thành viên**.
    Các trường hồ sơ bắt buộc (Họ tên, Ngày sinh YYYY-MM-DD, Giới tính
    Nam/Nữ/Khác, Lớp, Khoa) được validation bởi `UserCreate` — không cho
    để trống. Sau khi tạo User, hệ thống tự tạo 1 `Member` để Chủ nhiệm /
    Trưởng ban nhìn thấy ngay trong Danh sách thành viên.
    """
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    if user_data.role not in SELF_REGISTER_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Bạn không thể tự chọn vai trò. Tài khoản mới mặc định là Thành viên",
        )
    email = (user_data.email or "").strip().lower() or None
    if email and db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email đã được sử dụng")

    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=DEFAULT_ROLE,
        member_id=None,
        email=email,
        full_name=user_data.full_name,
        auth_provider="local",
    )
    db.add(user)
    db.flush()  # lấy user.id trước khi tạo Member

    # ---- Tự tạo hồ sơ Member gắn liền với User vừa tạo ----
    base = "".join(ch if ch.isalnum() else "" for ch in user.username.upper()) or "SV"
    student_id = f"{base}"
    suffix = 1
    while db.query(Member).filter(Member.student_id == student_id).first():
        suffix += 1
        student_id = f"{base}{suffix}"
    member_email = email or f"{user.username}@member.local"
    if db.query(Member).filter(Member.email == member_email).first():
        member_email = f"{user.username}+{user.id}@member.local"

    member = Member(
        full_name=user_data.full_name,
        student_id=student_id,
        email=member_email,
        phone=None,
        date_of_birth=user_data.date_of_birth,
        gender=user_data.gender,
        class_name=user_data.class_name,
        department=user_data.department,
    )
    db.add(member)
    db.flush()
    user.member_id = member.id
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")

    return _issue_token(user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Thông tin người dùng đang đăng nhập (dùng để khôi phục phiên)."""
    return current_user
# ---------------------------------------------------------------------------
# Social login: Google / Facebook / Discord
# ---------------------------------------------------------------------------

def _make_state(provider: str) -> str:
    """State token ký bằng SECRET_KEY để chống CSRF trong luồng OAuth."""
    return jwt.encode(
        {"provider": provider, "exp": datetime.now(timezone.utc) + timedelta(minutes=10)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def _redirect_with_result(target: str, token: str = "", error: str = "") -> str:
    """Ghép query string cho URL quay về frontend sau khi OAuth hoàn tất."""
    params = {"oauth_token": token} if token else {"oauth_error": error}
    separator = "&" if "?" in target else "?"
    return f"{target}{separator}{urlencode(params)}"


@router.get("/oauth/providers")
def oauth_providers():
    """Danh sách provider social login kèm trạng thái cấu hình.

    Frontend dùng endpoint này để hiển thị các nút Google / Facebook / Discord.
    """
    return {
        "providers": oauth.providers_status(),
        "demo_enabled": True,
        "default_role": DEFAULT_ROLE,
    }


@router.get("/oauth/{provider}/login")
def oauth_login(provider: str):
    """Trả về URL đăng nhập của provider để frontend chuyển hướng người dùng."""
    config = oauth.get_provider(provider)
    if not oauth.is_configured(provider):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Chưa cấu hình đăng nhập {config['label']}. Hãy đặt biến môi trường "
                f"{config['env_id']} và {config['env_secret']}, "
                "hoặc dùng chế độ demo (POST /auth/oauth/demo)."
            ),
        )
    return {
        "provider": provider,
        "authorize_url": oauth.build_authorize_url(provider, _make_state(provider)),
        "redirect_uri": oauth.redirect_uri(provider),
    }


@router.get("/oauth/{provider}/callback")
def oauth_callback(
    provider: str,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Provider gọi lại endpoint này sau khi người dùng đồng ý cấp quyền.

    Sau khi lấy được thông tin người dùng, hệ thống tạo/khôi phục tài khoản
    (vai trò mặc định: Thành viên) rồi chuyển hướng về frontend kèm JWT.
    """
    oauth.get_provider(provider)
    target = oauth.success_redirect_url()

    if error:
        return RedirectResponse(_redirect_with_result(target, error=error))
    if not code:
        return RedirectResponse(
            _redirect_with_result(target, error="Thiếu authorization code")
        )

    if state:
        try:
            payload = jwt.decode(state, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("provider") != provider:
                raise ValueError("state mismatch")
        except Exception:
            return RedirectResponse(
                _redirect_with_result(target, error="State không hợp lệ hoặc đã hết hạn")
            )

    try:
        info = oauth.exchange_code(provider, code)
        user, is_new = _find_or_create_social_user(db, info)
        result = _issue_token(user, is_new_user=is_new)
    except HTTPException as exc:
        return RedirectResponse(_redirect_with_result(target, error=str(exc.detail)))
    except Exception:  # pragma: no cover - phòng ngừa lỗi không lường trước
        return RedirectResponse(
            _redirect_with_result(target, error="Đăng nhập mạng xã hội thất bại")
        )

    return RedirectResponse(_redirect_with_result(target, token=result.access_token))


@router.post("/oauth/demo", response_model=Token)
def oauth_demo_login(payload: SocialLoginRequest, db: Session = Depends(get_db)):
    """Đăng nhập social ở *chế độ demo offline* (không cần API key).

    Dùng cho môi trường học tập/demo: mô phỏng kết quả trả về của Google /
    Facebook / Discord. Tài khoản tạo mới vẫn luôn có vai trò **Thành viên**.
    """
    info = oauth.demo_userinfo(
        payload.provider,
        email=payload.email,
        name=payload.name,
        provider_user_id=payload.provider_user_id,
    )
    user, is_new = _find_or_create_social_user(db, info)
    return _issue_token(user, is_new_user=is_new)