from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import Member, User

SECRET_KEY = "club-management-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# ---- Nhóm vai trò dùng cho phân quyền (role-based authorization) ----
ADMIN_OR_LEADER_ROLES = ("chu_nhiem", "truong_ban")
MEMBER_ROLES = ("thanh_vien",)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _to_bytes(value: str) -> bytes:
    return value.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_to_bytes(password), bcrypt.gensalt()).decode("utf-8")


def unusable_password_hash() -> str:
    """Hash 'vô hiệu' cho tài khoản tạo qua social login (không có mật khẩu).

    Tiền tố '!' không phải là chuỗi bcrypt hợp lệ nên `verify_password` sẽ
    luôn trả về False -> tài khoản social không thể đăng nhập bằng mật khẩu.
    """
    import secrets

    return "!" + secrets.token_urlsafe(32)



def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bytes(plain_password), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Không thể xác thực người dùng")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Người dùng không tồn tại")
    return user


def require_roles(*roles: str):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền thực hiện thao tác này",
            )
        return current_user

    return checker


def is_admin_or_leader(current_user: User = Depends(get_current_user)) -> User:
    """Guard: chỉ Chủ nhiệm hoặc Trưởng ban được phép truy cập.

    Dùng cho các chức năng quản lý: tạo/sửa/xóa hoạt động, xem danh sách
    điểm danh, xuất báo cáo...
    """
    if current_user.role not in ADMIN_OR_LEADER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Chủ nhiệm hoặc Trưởng ban mới có quyền thực hiện thao tác này",
        )
    return current_user


def is_member(current_user: User = Depends(get_current_user)) -> User:
    """Guard: chỉ kiểm tra vai trò Thành viên.

    Dùng cho các chức năng tự phục vụ của thành viên: đăng ký tham gia,
    điểm danh cá nhân. Hồ sơ Member sẽ được khởi tạo tự động khi cần.
    """
    if current_user.role not in MEMBER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chức năng này chỉ dành cho Thành viên",
        )
    return current_user


def ensure_member_profile(db: Session, current_user: User) -> Member:
    """Return or create a minimal Member record for a member account."""
    if current_user.member_id is not None:
        member = db.query(Member).filter(Member.id == current_user.member_id).first()
        if member:
            return member

    student_id = "".join(
        character for character in current_user.username.upper() if character.isalnum()
    ) or "SV"
    student_id = f"{student_id}{current_user.id}"
    email = (current_user.email or "").strip().lower()
    if not email or db.query(Member).filter(Member.email == email).first():
        email = f"user{current_user.id}@member.local"
        suffix = 1
        while db.query(Member).filter(Member.email == email).first():
            suffix += 1
            email = f"user{current_user.id}.{suffix}@member.local"

    member = Member(
        full_name=(current_user.full_name or "").strip() or current_user.username,
        student_id=student_id,
        email=email,
    )
    db.add(member)
    db.flush()
    current_user.member_id = member.id
    db.commit()
    db.refresh(current_user)
    db.refresh(member)
    return member


def get_member_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current account has a Member record for member-only history."""
    ensure_member_profile(db, current_user)
    return current_user