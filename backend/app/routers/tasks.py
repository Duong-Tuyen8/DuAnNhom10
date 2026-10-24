from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Task, Activity, Member, User
from ..schemas import TaskCreate, TaskUpdate, TaskOut
from ..security import require_roles, get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskOut])
def list_tasks(
    status: Optional[str] = None,
    assignee_id: Optional[int] = None,
    activity_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    if activity_id:
        query = query.filter(Task.activity_id == activity_id)
    tasks = query.order_by(Task.created_at.desc()).all()
    result = []
    for t in tasks:
        result.append(
            TaskOut(
                id=t.id,
                title=t.title,
                description=t.description or "",
                activity_id=t.activity_id,
                assignee_id=t.assignee_id,
                status=t.status,
                priority=t.priority,
                due_date=t.due_date,
                created_at=t.created_at,
            )
        )
    return result


@router.post("", response_model=TaskOut, status_code=201)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem", "truong_ban")),
):
    if data.activity_id:
        activity = db.query(Activity).filter(Activity.id == data.activity_id).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Hoạt động không tồn tại")
    if data.assignee_id:
        member = db.query(Member).filter(Member.id == data.assignee_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Thành viên không tồn tại")
    if data.status and data.status not in ["todo", "in_progress", "done"]:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")

    task = Task(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Nhiệm vụ không tồn tại")
    return task


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Nhiệm vụ không tồn tại")

    # Only chu_nhiem/truong_ban can reassign; assignee can update status
    changes = data.model_dump(exclude_unset=True)
    if current_user.role == "thanh_vien":
        allowed = {"status", "description"}
        for key in changes:
            if key not in allowed:
                raise HTTPException(status_code=403, detail="Thành viên chỉ được cập nhật trạng thái")
        if "status" in changes:
            task.status = changes["status"]
            db.commit()
            db.refresh(task)
            return task

    if data.assignee_id:
        member = db.query(Member).filter(Member.id == data.assignee_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Thành viên được giao không tồn tại")
    if data.activity_id:
        activity = db.query(Activity).filter(Activity.id == data.activity_id).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Hoạt động không tồn tại")
    if data.status and data.status not in ["todo", "in_progress", "done"]:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")

    for key, value in changes.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem", "truong_ban")),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Nhiệm vụ không tồn tại")
    db.delete(task)
    db.commit()
    return None