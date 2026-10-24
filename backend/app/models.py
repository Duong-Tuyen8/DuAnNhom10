from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
    Boolean,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# Vai trò mặc định cho mọi tài khoản đăng ký mới (kể cả social login)
DEFAULT_ROLE = "thanh_vien"
# Các vai trò hợp lệ trong hệ thống
ROLES = ("chu_nhiem", "truong_ban", "thanh_vien")
# Nhãn hiển thị của vai trò
ROLE_LABELS = {
    "chu_nhiem": "Chủ nhiệm",
    "truong_ban": "Trưởng ban",
    "thanh_vien": "Thành viên",
}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    # "chu_nhiem" (Chủ nhiệm) / "truong_ban" (Trưởng ban) / "thanh_vien" (Thành viên)
    role = Column(String, nullable=False, default=DEFAULT_ROLE)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)

    # ---- Thông tin bổ sung cho đăng nhập mạng xã hội (social login) ----
    email = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    # local / google / facebook / discord
    auth_provider = Column(String, nullable=False, default="local")
    # ID người dùng trả về từ nhà cung cấp OAuth
    provider_user_id = Column(String, nullable=True)

    member = relationship("Member", back_populates="user")

    @property
    def is_admin_or_leader(self) -> bool:
        return self.role in ("chu_nhiem", "truong_ban")

    @property
    def role_label(self) -> str:
        return ROLE_LABELS.get(self.role, self.role)


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    student_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    # ---- Hồ sơ bổ sung khi đăng ký tài khoản (yêu cầu mới) ----
    # Ngày sinh (YYYY-MM-DD), Giới tính (Nam / Nữ / Khác),
    # Lớp (văn bản), Khoa (văn bản).
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    class_name = Column(String, nullable=True)
    department = Column(String, nullable=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=True)
    skills = Column(Text, default="")  # comma-separated skills
    free_time = Column(Text, default="")  # e.g. "T2, T4, T6"
    joined_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    committee = relationship(
        "Committee",
        back_populates="members",
        foreign_keys=[committee_id],
    )
    user = relationship("User", back_populates="member", uselist=False)
    attendances = relationship("Attendance", back_populates="member")
    assigned_tasks = relationship("Task", back_populates="assignee")
    registrations = relationship("Registration", back_populates="member")


class Committee(Base):
    __tablename__ = "committees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, default="")
    leader_id = Column(Integer, ForeignKey("members.id"), nullable=True)

    members = relationship(
        "Member",
        back_populates="committee",
        foreign_keys="Member.committee_id",
    )
    leader = relationship("Member", foreign_keys=[leader_id])


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    location = Column(String, default="")
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    notes = Column(Text, default="")  # for AI summary
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    attendances = relationship("Attendance", back_populates="activity")
    tasks = relationship("Task", back_populates="activity")
    registrations = relationship("Registration", back_populates="activity")


class Registration(Base):
    """Đăng ký tham gia hoạt động của thành viên.

    Thành viên phải đăng ký trước, sau đó mới được điểm danh (self check-in)
    khi hoạt động diễn ra.
    """

    __tablename__ = "registrations"
    __table_args__ = (
        UniqueConstraint("activity_id", "member_id", name="uq_registration_activity_member"),
    )

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    activity = relationship("Activity", back_populates="registrations")
    member = relationship("Member", back_populates="registrations")


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    # present/absent/late là trạng thái quản lý cũ; điểm danh ảnh dùng
    # REGISTERED/PENDING_CHECKIN/ATTENDED/REJECTED.
    status = Column(String, default="pending")
    feedback = Column(Text, default="")
    checked_at = Column(DateTime, default=datetime.utcnow)
    checked_in_at = Column(DateTime, nullable=True)
    # ---- Minh chứng điểm danh (yêu cầu mới) ----
    proof_image_url = Column(String, nullable=True)  # /attendance/proofs/<uuid>.<ext>
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # người duyệt
    verified_at = Column(DateTime, nullable=True)
    reject_reason = Column(Text, default="")

    activity = relationship("Activity", back_populates="attendances")
    member = relationship("Member", back_populates="attendances")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    assignee_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    status = Column(String, default="todo")  # todo / in_progress / done
    priority = Column(String, default="medium")  # low / medium / high
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    activity = relationship("Activity", back_populates="tasks")
    assignee = relationship("Member", back_populates="assigned_tasks")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_ai_generated = Column(Boolean, default=False)

    activity = relationship("Activity")