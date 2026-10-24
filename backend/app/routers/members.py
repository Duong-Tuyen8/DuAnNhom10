from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Member, Committee, User, Attendance, Task
from ..schemas import MemberCreate, MemberUpdate, MemberOut
from ..security import require_roles, get_current_user, is_admin_or_leader

router = APIRouter(prefix="/members", tags=["members"])


def _member_history(db: Session, member_id: int) -> dict:
    """Build participation history for a member."""
    attendances = (
        db.query(Attendance)
        .filter(Attendance.member_id == member_id)
        .order_by(Attendance.checked_at.desc())
        .all()
    )
    tasks = db.query(Task).filter(Task.assignee_id == member_id).all()
    return {
        "attendances": [
            {
                "activity_id": a.activity_id,
                "status": a.status,
                "feedback": a.feedback,
                "checked_at": a.checked_at,
            }
            for a in attendances
        ],
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
            }
            for t in tasks
        ],
    }


@router.get("", response_model=List[MemberOut])
def list_members(
    committee_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Danh sách thành viên — CHỈ Chủ nhiệm / Trưởng ban được xem.

    Hiển thị: Họ tên, Ngày sinh, Giới tính, Lớp, Khoa, Ngày tham gia.
    Thành viên mới đăng ký (API tự tạo Member) xuất hiện ngay tại đây.
    """
    query = db.query(Member)
    if committee_id:
        query = query.filter(Member.committee_id == committee_id)
    if search:
        query = query.filter(
            Member.full_name.contains(search) | Member.student_id.contains(search)
        )
    members = query.order_by(Member.full_name).all()
    # FIX 1b: trả trực tiếp ORM — MemberOut(from_attributes) tự map
    # date_of_birth/gender/class_name/department. Không dùng model_copy
    # ghi đè thiếu trường (nguyên nhân cũ gây mất dữ liệu).
    return members


@router.post("", response_model=MemberOut, status_code=201)
def create_member(
    data: MemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem")),
):
    if db.query(Member).filter(Member.student_id == data.student_id).first():
        raise HTTPException(status_code=400, detail="Mã số sinh viên đã tồn tại")
    if db.query(Member).filter(Member.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email đã tồn tại")
    if data.committee_id:
        committee = db.query(Committee).filter(Committee.id == data.committee_id).first()
        if not committee:
            raise HTTPException(status_code=404, detail="Ban không tồn tại")

    member = Member(**data.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get("/{member_id}", response_model=MemberOut)
def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Chi tiết 1 thành viên — chỉ Chủ nhiệm / Trưởng ban."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Thành viên không tồn tại")
    return member


@router.put("/{member_id}", response_model=MemberOut)
def update_member(
    member_id: int,
    data: MemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem", "truong_ban")),
):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Thành viên không tồn tại")

    changes = data.model_dump(exclude_unset=True)
    if "student_id" in changes and changes["student_id"] != member.student_id:
        if db.query(Member).filter(Member.student_id == changes["student_id"]).first():
            raise HTTPException(status_code=400, detail="Mã số sinh viên đã tồn tại")
    if "email" in changes and changes["email"] != member.email:
        if db.query(Member).filter(Member.email == changes["email"]).first():
            raise HTTPException(status_code=400, detail="Email đã tồn tại")

    for key, value in changes.items():
        setattr(member, key, value)
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=204)
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem")),
):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Thành viên không tồn tại")
    # Soft delete to preserve history
    member.is_active = False
    db.commit()
    return None


@router.get("/{member_id}/history")
def member_history(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lịch sử tham gia của thành viên.

    - Chủ nhiệm / Trưởng ban: xem lịch sử của mọi thành viên.
    - Thành viên: chỉ xem lịch sử của chính mình.
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Thành viên không tồn tại")
    if current_user.role == "thanh_vien" and current_user.member_id != member_id:
        raise HTTPException(
            status_code=403,
            detail="Bạn chỉ được xem lịch sử tham gia của chính mình",
        )
    return {"member_id": member_id, "full_name": member.full_name, **_member_history(db, member_id)}