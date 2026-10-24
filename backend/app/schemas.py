from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime, date
from typing import Optional, List, Literal

# Giới tính hợp lệ cho hồ sơ thành viên (yêu cầu đăng ký mới)
VALID_GENDERS = ("Nam", "Nữ", "Khác")


# ---------- Auth ----------
class UserCreate(BaseModel):
    username: str
    password: str
    # Không còn cho phép người dùng tự chọn vai trò: mọi tài khoản đăng ký mới
    # đều mặc định là "thanh_vien" (Thành viên). Trường này chỉ giữ lại để
    # tương thích ngược và sẽ bị từ chối nếu gửi vai trò khác thành viên.
    role: Optional[str] = None
    member_id: Optional[int] = None
    email: Optional[str] = None
    # ---- Hồ sơ bắt buộc khi đăng ký (yêu cầu mới) ----
    # Họ tên, Ngày sinh (YYYY-MM-DD), Giới tính (Nam/Nữ/Khác),
    # Lớp (văn bản), Khoa (văn bản).
    full_name: str
    date_of_birth: date
    gender: str
    class_name: str
    department: str

    @field_validator("full_name", "class_name", "department")
    @classmethod
    def _not_blank(cls, v: str, info) -> str:
        if v is None or not str(v).strip():
            raise ValueError(f"Trường '{info.field_name}' không được để trống")
        return str(v).strip()

    @field_validator("gender")
    @classmethod
    def _valid_gender(cls, v: str) -> str:
        if v is None or not str(v).strip():
            raise ValueError("Giới tính không được để trống")
        normalized = str(v).strip().capitalize()
        # Chuẩn hoá "nu" / "nữ" viết thường
        mapping = {"nam": "Nam", "nữ": "Nữ", "nu": "Nữ", "khác": "Khác", "khac": "Khác"}
        normalized = mapping.get(str(v).strip().lower(), str(v).strip())
        if normalized not in VALID_GENDERS:
            raise ValueError("Giới tính phải là một trong: Nam / Nữ / Khác")
        return normalized

    @field_validator("date_of_birth")
    @classmethod
    def _valid_dob(cls, v: date) -> date:
        if v is None:
            raise ValueError("Ngày sinh không được để trống")
        if isinstance(v, str):
            try:
                v = date.fromisoformat(v)
            except ValueError:
                raise ValueError("Ngày sinh phải đúng định dạng YYYY-MM-DD")
        if v > date.today():
            raise ValueError("Ngày sinh không được là ngày trong tương lai")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class SocialLoginRequest(BaseModel):
    """Đăng nhập/đăng ký qua mạng xã hội (chế độ demo offline)."""

    provider: str  # google / facebook / discord
    email: Optional[str] = None
    name: Optional[str] = None
    provider_user_id: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: str
    member_id: Optional[int] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    auth_provider: str = "local"


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str
    user_id: int
    member_id: Optional[int] = None
    is_new_user: bool = False


# ---------- Member ----------
class MemberCreate(BaseModel):
    full_name: str
    student_id: str
    email: str
    phone: Optional[str] = None
    # ---- Hồ sơ bổ sung (đồng bộ với form Đăng ký tài khoản) ----
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    class_name: Optional[str] = None
    department: Optional[str] = None
    committee_id: Optional[int] = None
    skills: Optional[str] = ""
    free_time: Optional[str] = ""

    @field_validator("gender")
    @classmethod
    def _valid_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is None or str(v).strip() == "":
            return v
        mapping = {"nam": "Nam", "nữ": "Nữ", "nu": "Nữ", "khác": "Khác", "khac": "Khác"}
        normalized = mapping.get(str(v).strip().lower(), str(v).strip())
        if normalized not in VALID_GENDERS:
            raise ValueError("Giới tính phải là một trong: Nam / Nữ / Khác")
        return normalized


class MemberUpdate(BaseModel):
    full_name: Optional[str] = None
    student_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    # ---- Hồ sơ bổ sung ----
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    class_name: Optional[str] = None
    department: Optional[str] = None
    committee_id: Optional[int] = None
    skills: Optional[str] = None
    free_time: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("gender")
    @classmethod
    def _valid_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is None or str(v).strip() == "":
            return v
        mapping = {"nam": "Nam", "nữ": "Nữ", "nu": "Nữ", "khác": "Khác", "khac": "Khác"}
        normalized = mapping.get(str(v).strip().lower(), str(v).strip())
        if normalized not in VALID_GENDERS:
            raise ValueError("Giới tính phải là một trong: Nam / Nữ / Khác")
        return normalized


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    student_id: str
    email: str
    phone: Optional[str] = None
    # ---- Hồ sơ bổ sung hiển thị trong Danh sách thành viên ----
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    class_name: Optional[str] = None
    department: Optional[str] = None
    committee_id: Optional[int] = None
    skills: Optional[str] = ""
    free_time: Optional[str] = ""
    joined_date: datetime
    is_active: bool


# ---------- Committee ----------
class CommitteeCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    leader_id: Optional[int] = None


class CommitteeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = ""
    leader_id: Optional[int] = None
    member_count: int = 0


# ---------- Activity ----------
class ActivityCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    location: Optional[str] = ""
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = ""


class ActivityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    location: str
    start_time: datetime
    end_time: datetime
    notes: str
    created_at: datetime
    attendee_count: int = 0
    registration_count: int = 0
    # Trạng thái của người dùng đang đăng nhập (member)
    is_registered: bool = False
    my_attendance_status: Optional[str] = None
    my_checked_at: Optional[datetime] = None
    my_reject_reason: Optional[str] = ""
    can_check_in: bool = False


# ---------- Registration (đăng ký tham gia) ----------
class RegistrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    activity_id: int
    member_id: int
    created_at: datetime
    member_name: Optional[str] = None


# ---------- Attendance ----------
class AttendanceCreate(BaseModel):
    activity_id: int
    member_id: int
    status: str = "present"
    feedback: Optional[str] = ""


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    activity_id: int
    member_id: int
    member_name: Optional[str] = None
    student_id: Optional[str] = None
    class_name: Optional[str] = None
    department: Optional[str] = None
    activity_title: Optional[str] = None
    status: str
    feedback: str
    checked_at: datetime
    checked_in_at: Optional[datetime] = None
    proof_image_url: Optional[str] = None
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    reject_reason: Optional[str] = ""


class AttendanceVerification(BaseModel):
    member_id: int
    action: Literal["approve", "reject"]
    reject_reason: Optional[str] = ""


class AttendanceIdVerification(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    reject_reason: Optional[str] = ""


class BulkAttendance(BaseModel):
    activity_id: int
    member_ids: List[int]
    statuses: Optional[List[str]] = None


# ---------- Task ----------
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    activity_id: Optional[int] = None
    assignee_id: Optional[int] = None
    status: Optional[str] = "todo"
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    activity_id: Optional[int] = None
    assignee_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    activity_id: Optional[int] = None
    assignee_id: Optional[int] = None
    status: str
    priority: str
    due_date: Optional[datetime] = None
    created_at: datetime


# ---------- Notification ----------
class NotificationCreate(BaseModel):
    title: str
    content: str
    activity_id: Optional[int] = None
    is_ai_generated: bool = False


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    content: str
    activity_id: Optional[int] = None
    created_at: datetime
    is_ai_generated: bool


# ---------- AI ----------
class AINotificationRequest(BaseModel):
    activity_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = ""
    location: Optional[str] = ""
    start_time: Optional[str] = ""
    end_time: Optional[str] = ""


class AISummaryRequest(BaseModel):
    activity_id: int


# ---------- AI Chatbot (trợ lý hỏi đáp về hoạt động) ----------
class ChatMessage(BaseModel):
    role: str = "user"  # user / assistant
    content: str = ""


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    provider: str
    context: Optional[dict] = None