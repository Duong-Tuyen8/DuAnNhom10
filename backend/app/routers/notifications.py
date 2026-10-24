from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Notification, Activity, User
from ..schemas import NotificationCreate, NotificationOut
from ..security import require_roles, get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationOut])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = db.query(Notification).order_by(Notification.created_at.desc()).all()
    result = []
    for n in records:
        result.append(
            NotificationOut(
                id=n.id,
                title=n.title,
                content=n.content,
                activity_id=n.activity_id,
                created_at=n.created_at,
                is_ai_generated=n.is_ai_generated,
            )
        )
    return result


@router.post("", response_model=NotificationOut, status_code=201)
def create_notification(
    data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem", "truong_ban")),
):
    if data.activity_id:
        activity = db.query(Activity).filter(Activity.id == data.activity_id).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Hoạt động không tồn tại")

    notification = Notification(
        title=data.title,
        content=data.content,
        activity_id=data.activity_id,
        created_by=current_user.id,
        is_ai_generated=data.is_ai_generated,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.delete("/{notification_id}", status_code=204)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem", "truong_ban")),
):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Thông báo không tồn tại")
    db.delete(notification)
    db.commit()
    return None