from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Member, Committee, Activity, Attendance, Task, User
from ..security import require_roles, get_current_user
from ..activity_helpers import APPROVED_ATTENDANCE_STATUSES

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
def overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_members = db.query(Member).filter(Member.is_active == True).count()
    total_committees = db.query(Committee).count()
    total_activities = db.query(Activity).count()
    total_tasks = db.query(Task).count()
    tasks_done = db.query(Task).filter(Task.status == "done").count()
    total_attendance = db.query(Attendance).filter(
        Attendance.status.in_(APPROVED_ATTENDANCE_STATUSES)
    ).count()

    # Top committees by members
    committees = db.query(Committee).all()
    committee_stats = []
    for c in committees:
        count = db.query(Member).filter(Member.committee_id == c.id, Member.is_active == True).count()
        committee_stats.append({"id": c.id, "name": c.name, "member_count": count})

    return {
        "total_members": total_members,
        "total_committees": total_committees,
        "total_activities": total_activities,
        "total_tasks": total_tasks,
        "tasks_done": tasks_done,
        "total_attendance": total_attendance,
        "committees": committee_stats,
    }


@router.get("/activities")
def activity_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Thống kê hoạt động: số lượng, tỷ lệ tham gia."""
    activities = db.query(Activity).order_by(Activity.start_time.desc()).all()
    total_members = db.query(Member).filter(Member.is_active == True).count() or 1

    result = []
    for a in activities:
        attendance_count = db.query(Attendance).filter(
            Attendance.activity_id == a.id,
            Attendance.status.in_(APPROVED_ATTENDANCE_STATUSES),
        ).count()
        present_count = db.query(Attendance).filter(
            Attendance.activity_id == a.id,
            Attendance.status.in_(APPROVED_ATTENDANCE_STATUSES),
        ).count()
        result.append(
            {
                "id": a.id,
                "title": a.title,
                "start_time": a.start_time,
                "attendance_count": attendance_count,
                "present_count": present_count,
                "participation_rate": round((attendance_count / total_members) * 100, 1) if total_members else 0,
            }
        )
    return result


@router.get("/members/top")
def top_members(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem", "truong_ban")),
):
    """Thành viên tích cực nhất dựa trên số lần điểm danh và nhiệm vụ hoàn thành."""
    members = db.query(Member).filter(Member.is_active == True).all()
    scores = []
    for m in members:
        attendance_count = db.query(Attendance).filter(
            Attendance.member_id == m.id,
            Attendance.status.in_(APPROVED_ATTENDANCE_STATUSES),
        ).count()
        tasks_done = db.query(Task).filter(
            Task.assignee_id == m.id, Task.status == "done"
        ).count()
        score = attendance_count * 2 + tasks_done * 3
        scores.append(
            {
                "id": m.id,
                "full_name": m.full_name,
                "student_id": m.student_id,
                "committee_id": m.committee_id,
                "attendance_count": attendance_count,
                "tasks_done": tasks_done,
                "score": score,
            }
        )
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:limit]


@router.get("/members/participation")
def member_participation(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lịch sử tham gia của một thành viên."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Thành viên không tồn tại")

    attendances = (
        db.query(Attendance)
        .filter(Attendance.member_id == member_id)
        .order_by(Attendance.checked_at.desc())
        .all()
    )
    tasks = db.query(Task).filter(Task.assignee_id == member_id).all()

    activities = []
    for a in attendances:
        activity = db.query(Activity).filter(Activity.id == a.activity_id).first()
        if activity:
            activities.append(
                {
                    "activity_id": activity.id,
                    "activity_title": activity.title,
                    "start_time": activity.start_time,
                    "status": a.status,
                    "feedback": a.feedback,
                }
            )

    return {
        "member_id": member.id,
        "full_name": member.full_name,
        "student_id": member.student_id,
        "total_activities": len(activities),
        "activities": activities,
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