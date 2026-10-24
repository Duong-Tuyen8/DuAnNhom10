from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Committee, Member, User
from ..schemas import CommitteeCreate, CommitteeOut
from ..security import require_roles, get_current_user

router = APIRouter(prefix="/committees", tags=["committees"])


@router.get("", response_model=List[CommitteeOut])
def list_committees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    committees = db.query(Committee).order_by(Committee.name).all()
    result = []
    for c in committees:
        member_count = db.query(Member).filter(Member.committee_id == c.id, Member.is_active == True).count()
        result.append(
            CommitteeOut(
                id=c.id,
                name=c.name,
                description=c.description or "",
                leader_id=c.leader_id,
                member_count=member_count,
            )
        )
    return result


@router.post("", response_model=CommitteeOut, status_code=201)
def create_committee(
    data: CommitteeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem")),
):
    if db.query(Committee).filter(Committee.name == data.name).first():
        raise HTTPException(status_code=400, detail="Tên ban đã tồn tại")
    committee = Committee(**data.model_dump())
    db.add(committee)
    db.commit()
    db.refresh(committee)
    return CommitteeOut(
        id=committee.id,
        name=committee.name,
        description=committee.description or "",
        leader_id=committee.leader_id,
        member_count=0,
    )


@router.get("/{committee_id}", response_model=CommitteeOut)
def get_committee(
    committee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    committee = db.query(Committee).filter(Committee.id == committee_id).first()
    if not committee:
        raise HTTPException(status_code=404, detail="Ban không tồn tại")
    member_count = db.query(Member).filter(
        Member.committee_id == committee.id, Member.is_active == True
    ).count()
    return CommitteeOut(
        id=committee.id,
        name=committee.name,
        description=committee.description or "",
        leader_id=committee.leader_id,
        member_count=member_count,
    )


@router.get("/{committee_id}/members", response_model=List[dict])
def committee_members(
    committee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    committee = db.query(Committee).filter(Committee.id == committee_id).first()
    if not committee:
        raise HTTPException(status_code=404, detail="Ban không tồn tại")
    members = (
        db.query(Member)
        .filter(Member.committee_id == committee_id, Member.is_active == True)
        .order_by(Member.full_name)
        .all()
    )
    return [
        {
            "id": m.id,
            "full_name": m.full_name,
            "student_id": m.student_id,
            "email": m.email,
            "phone": m.phone,
            "skills": m.skills or "",
            "free_time": m.free_time or "",
        }
        for m in members
    ]


@router.put("/{committee_id}", response_model=CommitteeOut)
def update_committee(
    committee_id: int,
    data: CommitteeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem")),
):
    committee = db.query(Committee).filter(Committee.id == committee_id).first()
    if not committee:
        raise HTTPException(status_code=404, detail="Ban không tồn tại")
    if data.leader_id and not db.query(Member).filter(Member.id == data.leader_id).first():
        raise HTTPException(status_code=404, detail="Trưởng ban không tồn tại")
    committee.name = data.name
    committee.description = data.description
    committee.leader_id = data.leader_id
    db.commit()
    db.refresh(committee)
    member_count = db.query(Member).filter(
        Member.committee_id == committee.id, Member.is_active == True
    ).count()
    return CommitteeOut(
        id=committee.id,
        name=committee.name,
        description=committee.description or "",
        leader_id=committee.leader_id,
        member_count=member_count,
    )


@router.delete("/{committee_id}", status_code=204)
def delete_committee(
    committee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem")),
):
    committee = db.query(Committee).filter(Committee.id == committee_id).first()
    if not committee:
        raise HTTPException(status_code=404, detail="Ban không tồn tại")
    members = db.query(Member).filter(Member.committee_id == committee_id).all()
    for m in members:
        m.committee_id = None
    db.delete(committee)
    db.commit()
    return None