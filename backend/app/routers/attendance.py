import csv
import io
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .. import activity_helpers as helpers
from ..database import get_db
from ..models import Attendance, Activity, Member, User
from ..schemas import (
    AttendanceCreate,
    AttendanceIdVerification,
    AttendanceOut,
    BulkAttendance,
)
from ..security import (
    get_current_user,
    get_member_profile,
    is_admin_or_leader,
    is_member,
    ensure_member_profile,
    require_roles,
)

router = APIRouter(prefix="/attendance", tags=["attendance"])
PROOF_UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "proofs"
MAX_PROOF_SIZE = 5 * 1024 * 1024


def _proof_file_type(content: bytes) -> str:
    if content.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "webp"
    raise HTTPException(status_code=400, detail="Tệp tải lên không phải ảnh JPEG, PNG, GIF hoặc WebP")


async def submit_check_in(
    activity_id: int,
    photo: UploadFile,
    feedback: str,
    db: Session,
    current_user: User,
) -> Attendance:
    member = ensure_member_profile(db, current_user)
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Hoạt động không tồn tại")
    if not helpers.get_registration(db, activity.id, member.id):
        raise HTTPException(status_code=400, detail="Bạn cần đăng ký tham gia hoạt động trước khi điểm danh")
    if not helpers.is_check_in_open(activity):
        raise HTTPException(
            status_code=400,
            detail=f"Chưa thể điểm danh: {helpers.check_in_window_message(activity)}",
        )

    existing = helpers.get_attendance(db, activity.id, member.id)
    if existing and existing.status not in {"REJECTED", "rejected"}:
        message = (
            "Điểm danh của bạn đang chờ duyệt"
            if existing.status == "PENDING_CHECKIN"
            else "Bạn đã điểm danh hoạt động này rồi"
        )
        raise HTTPException(status_code=400, detail=message)

    content = await photo.read(MAX_PROOF_SIZE + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Vui lòng đính kèm ảnh minh chứng")
    if len(content) > MAX_PROOF_SIZE:
        raise HTTPException(status_code=413, detail="Ảnh minh chứng không được vượt quá 5 MB")
    extension = _proof_file_type(content)

    filename = f"{uuid4().hex}.{extension}"
    file_path = PROOF_UPLOAD_DIR / filename
    try:
        PROOF_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
    except OSError as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Không thể lưu ảnh minh chứng") from exc

    from datetime import datetime

    checked_in_at = datetime.utcnow()
    if existing:
        record = existing
        record.status = "PENDING_CHECKIN"
        record.feedback = feedback or ""
        record.proof_image_url = f"/attendance/proofs/{filename}"
        record.checked_at = checked_in_at
        record.checked_in_at = checked_in_at
        record.verified_by = None
        record.verified_at = None
        record.reject_reason = ""
    else:
        record = Attendance(
            activity_id=activity.id,
            member_id=member.id,
            status="PENDING_CHECKIN",
            feedback=feedback or "",
            proof_image_url=f"/attendance/proofs/{filename}",
            checked_at=checked_in_at,
            checked_in_at=checked_in_at,
            reject_reason="",
        )
        db.add(record)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise
    db.refresh(record)
    return record


@router.get("/proofs/{filename}")
def get_attendance_proof(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Ảnh minh chứng chỉ được xem bởi Chủ nhiệm / Trưởng ban."""
    if Path(filename).name != filename:
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh minh chứng")
    record = (
        db.query(Attendance)
        .filter(Attendance.proof_image_url == f"/attendance/proofs/{filename}")
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh minh chứng")
    file_path = PROOF_UPLOAD_DIR / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh minh chứng")
    media_type = {
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(file_path.suffix.lower(), "application/octet-stream")
    return FileResponse(file_path, media_type=media_type)


@router.get("", response_model=List[AttendanceOut])
def list_attendance(
    activity_id: Optional[int] = None,
    member_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Danh sách điểm danh.

    - Chủ nhiệm / Trưởng ban: xem toàn bộ, lọc theo `activity_id` / `member_id`.
    - Thành viên: **chỉ** xem được bản ghi điểm danh của chính mình.
    """
    query = db.query(Attendance)

    if current_user.role == "thanh_vien":
        if not current_user.member_id:
            return []
        query = query.filter(Attendance.member_id == current_user.member_id)
    elif member_id:
        query = query.filter(Attendance.member_id == member_id)

    if activity_id:
        query = query.filter(Attendance.activity_id == activity_id)

    records = query.order_by(Attendance.checked_in_at.desc(), Attendance.checked_at.desc()).all()
    return [
        AttendanceOut(
            id=r.id,
            activity_id=r.activity_id,
            member_id=r.member_id,
            member_name=r.member.full_name if r.member else None,
            student_id=r.member.student_id if r.member else None,
            class_name=r.member.class_name if r.member else None,
            department=r.member.department if r.member else None,
            activity_title=r.activity.title if r.activity else None,
            status=r.status,
            feedback=r.feedback or "",
            checked_at=r.checked_in_at or r.checked_at,
            checked_in_at=r.checked_in_at,
            proof_image_url=r.proof_image_url,
            verified_by=r.verified_by,
            verified_at=r.verified_at,
            reject_reason=r.reject_reason or "",
        )
        for r in records
    ]


@router.get("/me")
def my_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_member_profile),
):
    """Lịch sử điểm danh của chính thành viên đang đăng nhập."""
    records = (
        db.query(Attendance)
        .filter(Attendance.member_id == current_user.member_id)
        .order_by(Attendance.checked_in_at.desc(), Attendance.checked_at.desc())
        .all()
    )
    items = []
    for r in records:
        activity = db.query(Activity).filter(Activity.id == r.activity_id).first()
        items.append(
            {
                "id": r.id,
                "activity_id": r.activity_id,
                "activity_title": activity.title if activity else "N/A",
                "start_time": activity.start_time if activity else None,
                "location": (activity.location or "") if activity else "",
                "status": r.status,
                "status_label": helpers.STATUS_LABELS.get(r.status, r.status),
                "feedback": r.feedback or "",
                "checked_at": r.checked_in_at or r.checked_at,
            }
        )
    return {"member_id": current_user.member_id, "count": len(items), "attendances": items}


@router.get("/pending")
def pending_attendance_verifications(
    activity_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Danh sách minh chứng đang chờ Chủ nhiệm / Trưởng ban duyệt."""
    query = db.query(Attendance).filter(Attendance.status == "PENDING_CHECKIN")
    if activity_id:
        query = query.filter(Attendance.activity_id == activity_id)
    records = query.order_by(Attendance.checked_in_at.desc(), Attendance.checked_at.desc()).all()
    return {
        "count": len(records),
        "attendances": [
            {
                "id": record.id,
                "activity_id": record.activity_id,
                "activity_title": record.activity.title if record.activity else "",
                "member_id": record.member_id,
                "member_name": record.member.full_name if record.member else None,
                "student_id": record.member.student_id if record.member else None,
                "class_name": (record.member.class_name or "") if record.member else "",
                "department": (record.member.department or "") if record.member else "",
                "status": record.status,
                "feedback": record.feedback or "",
                "checked_at": record.checked_in_at or record.checked_at,
                "proof_image_url": record.proof_image_url,
            }
            for record in records
        ],
    }


@router.post("/check-in", response_model=AttendanceOut, status_code=201)
async def self_check_in(
    activity_id: int = Form(...),
    photo: UploadFile = File(...),
    feedback: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(is_member),
):
    """Thành viên nộp điểm danh kèm ảnh minh chứng trong thời gian cho phép."""
    return await submit_check_in(activity_id, photo, feedback, db, current_user)


@router.post("", response_model=AttendanceOut, status_code=201)
def create_attendance(
    data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Điểm danh hộ thành viên — chỉ Chủ nhiệm / Trưởng ban."""
    activity = db.query(Activity).filter(Activity.id == data.activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Hoạt động không tồn tại")
    member = db.query(Member).filter(Member.id == data.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Thành viên không tồn tại")
    if data.status not in ["present", "absent", "late"]:
        raise HTTPException(status_code=400, detail="Trạng thái phải là present, absent hoặc late")

    existing = (
        db.query(Attendance)
        .filter(
            Attendance.activity_id == data.activity_id,
            Attendance.member_id == data.member_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Điểm danh đã tồn tại cho thành viên trong hoạt động này")

    record = Attendance(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/bulk", status_code=201)
def bulk_attendance(
    data: BulkAttendance,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Điểm danh hàng loạt — chỉ Chủ nhiệm / Trưởng ban."""
    activity = db.query(Activity).filter(Activity.id == data.activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Hoạt động không tồn tại")

    member_ids = data.member_ids
    statuses = data.statuses or ["present"] * len(member_ids)
    if len(statuses) != len(member_ids):
        raise HTTPException(status_code=400, detail="Danh sách trạng thái không khớp số lượng thành viên")

    created = 0
    for i, member_id in enumerate(member_ids):
        member = db.query(Member).filter(Member.id == member_id).first()
        if not member:
            continue
        existing = (
            db.query(Attendance)
            .filter(
                Attendance.activity_id == data.activity_id,
                Attendance.member_id == member_id,
            )
            .first()
        )
        if existing:
            continue
        db.add(Attendance(activity_id=data.activity_id, member_id=member_id, status=statuses[i]))
        created += 1
    db.commit()
    return {"created": created, "activity_id": data.activity_id}


@router.patch("/{attendance_id}/verify", response_model=AttendanceOut)
def verify_attendance_by_id(
    attendance_id: int,
    data: AttendanceIdVerification,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Duyệt / từ chối ảnh minh chứng bằng ID bản ghi attendance."""
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Bản ghi điểm danh không tồn tại")
    if record.status != "PENDING_CHECKIN":
        raise HTTPException(status_code=409, detail="Lượt điểm danh không còn ở trạng thái chờ duyệt")

    from datetime import datetime

    record.status = "ATTENDED" if data.status == "APPROVED" else "REJECTED"
    record.verified_by = current_user.id
    record.verified_at = datetime.utcnow()
    record.reject_reason = (data.reject_reason or "").strip() if data.status == "REJECTED" else ""
    db.commit()
    db.refresh(record)
    return record


@router.put("/{attendance_id}", response_model=AttendanceOut)
def update_attendance(
    attendance_id: int,
    status: str = None,
    feedback: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Sửa trạng thái điểm danh — chỉ Chủ nhiệm / Trưởng ban."""
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Bản ghi điểm danh không tồn tại")
    if status:
        if status not in ["present", "absent", "late"]:
            raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")
        record.status = status
    if feedback is not None:
        record.feedback = feedback
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{attendance_id}", status_code=204)
def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem")),
):
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Bản ghi điểm danh không tồn tại")
    db.delete(record)
    db.commit()
    return None
@router.get("/export")
def export_attendance_report(
    activity_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Xuất báo cáo điểm danh (toàn bộ hoặc theo hoạt động) — chỉ Chủ nhiệm / Trưởng ban."""
    query = db.query(Attendance)
    if activity_id:
        query = query.filter(Attendance.activity_id == activity_id)
    records = query.order_by(Attendance.checked_at.desc()).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["STT", "Hoạt động", "Họ tên", "MSSV", "Trạng thái", "Phản hồi", "Thời gian điểm danh"]
    )
    for index, r in enumerate(records, start=1):
        activity = db.query(Activity).filter(Activity.id == r.activity_id).first()
        member = db.query(Member).filter(Member.id == r.member_id).first()
        writer.writerow(
            [
                index,
                activity.title if activity else "N/A",
                member.full_name if member else "N/A",
                member.student_id if member else "",
                helpers.STATUS_LABELS.get(r.status, r.status),
                r.feedback or "",
                r.checked_at.strftime("%d/%m/%Y %H:%M") if r.checked_at else "",
            ]
        )

    buffer.seek(0)
    suffix = f"_hoat_dong_{activity_id}" if activity_id else ""
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": f'attachment; filename="bao_cao_diem_danh{suffix}.csv"'
        },
    )