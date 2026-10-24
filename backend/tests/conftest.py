import os
import sys
import pytest
from datetime import datetime, timedelta

# Must set DB path BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test_club.db"

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base, engine, SessionLocal  # noqa: E402
from app.models import User, Member, Committee, Activity, Attendance  # noqa: E402
from app.security import hash_password  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    # Seed minimal data for all tests
    c1 = Committee(name="Ban Truyền thông", description="Test")
    c2 = Committee(name="Ban Tổ chức", description="Test")
    db.add_all([c1, c2])
    db.commit()

    m1 = Member(full_name="Nguyễn Văn An", student_id="SV001", email="an@test.vn",
                committee_id=c1.id, skills="truyền thông, content", free_time="T2, T4")
    m2 = Member(full_name="Trần Thị Bình", student_id="SV002", email="binh@test.vn",
                committee_id=c2.id, skills="tổ chức, hậu cần", free_time="T3, T5")
    m3 = Member(full_name="Lê Văn Cường", student_id="SV003", email="cuong@test.vn",
                skills="kỹ thuật, IT", free_time="T6, CN")
    db.add_all([m1, m2, m3])
    db.commit()

    u1 = User(username="chunhiem", password_hash=hash_password("123456"), role="chu_nhiem", member_id=m1.id)
    u2 = User(username="truongbantt", password_hash=hash_password("123456"), role="truong_ban", member_id=m2.id)
    u3 = User(username="thanhvien", password_hash=hash_password("123456"), role="thanh_vien", member_id=m3.id)
    db.add_all([u1, u2, u3])
    db.commit()

    now = datetime.utcnow()
    act = Activity(title="Workshop AI", description="AI workshop", location="Hội trường A",
                   start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=3),
                   created_by=u1.id)
    db.add(act)
    db.commit()

    db.add(Attendance(activity_id=act.id, member_id=m1.id, status="present", feedback="Tốt"))
    db.add(Attendance(activity_id=act.id, member_id=m2.id, status="present", feedback="Hay"))
    db.commit()
    db.close()

    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()