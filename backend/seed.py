"""
Seed script - Tạo dữ liệu mẫu cho hệ thống quản lý CLB sinh viên.
Chạy: python seed.py
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from app.database import Base, engine, SessionLocal
from app.models import (
    User,
    Member,
    Committee,
    Activity,
    Attendance,
    Registration,
    Task,
    Notification,
)
from app.security import hash_password, unusable_password_hash


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing data
    db.query(Attendance).delete()
    db.query(Registration).delete()
    db.query(Task).delete()
    db.query(Notification).delete()
    db.query(Activity).delete()
    db.query(User).delete()
    db.query(Member).delete()
    db.query(Committee).delete()
    db.commit()

    # ---- Committees ----
    c_truyen_thong = Committee(
        name="Ban Truyền thông",
        description="Quản lý fanpage, bài viết, thiết kế ấn phẩm",
    )
    c_to_chuc = Committee(
        name="Ban Tổ chức",
        description="Lên kế hoạch và tổ chức sự kiện",
    )
    c_chuyen_mon = Committee(
        name="Ban Chuyên môn",
        description="Phụ trách nội dung học thuật và đào tạo",
    )
    db.add_all([c_truyen_thong, c_to_chuc, c_chuyen_mon])
    db.commit()

    # ---- Members ----
    from datetime import date
    members = [
        Member(
            full_name="Nguyễn Văn An",
            student_id="SV001",
            email="an.nguyen@club.edu.vn",
            phone="0912345678",
            date_of_birth=date(2003, 5, 12),
            gender="Nam",
            class_name="CNTT-K15A",
            department="Công nghệ thông tin",
            committee_id=c_truyen_thong.id,
            skills="truyền thông, content, viết bài",
            free_time="T2, T3, T6",
        ),
        Member(
            full_name="Trần Thị Bình",
            student_id="SV002",
            email="binh.tran@club.edu.vn",
            phone="0987654321",
            date_of_birth=date(2004, 2, 20),
            gender="Nữ",
            class_name="QTKD-K16B",
            department="Quản trị kinh doanh",
            committee_id=c_to_chuc.id,
            skills="tổ chức sự kiện, quản lý thời gian",
            free_time="T4, T5, T7",
        ),
        Member(
            full_name="Lê Hoàng Cường",
            student_id="SV003",
            email="cuong.le@club.edu.vn",
            phone="0905123456",
            date_of_birth=date(2003, 11, 3),
            gender="Nam",
            class_name="DTVT-K14C",
            department="Điện tử viễn thông",
            committee_id=c_chuyen_mon.id,
            skills="kỹ thuật, công nghệ, thuyết trình",
            free_time="T2, T4, T5",
        ),
        Member(
            full_name="Phạm Thu Dung",
            student_id="SV004",
            email="dung.pham@club.edu.vn",
            phone="0933456789",
            date_of_birth=date(2004, 7, 15),
            gender="Nữ",
            class_name="TKĐH-K16A",
            department="Thiết kế đồ họa",
            committee_id=c_truyen_thong.id,
            skills="thiết kế, photoshop, video",
            free_time="T3, T6, CN",
        ),
        Member(
            full_name="Hoàng Minh Đức",
            student_id="SV005",
            email="duc.hoang@club.edu.vn",
            phone="0911987654",
            date_of_birth=date(2002, 9, 28),
            gender="Nam",
            class_name="KT-K13B",
            department="Kế toán",
            committee_id=c_to_chuc.id,
            skills="đối ngoại, hậu cần",
            free_time="T5, T7, CN",
        ),
        Member(
            full_name="Vũ Thị Em",
            student_id="SV006",
            email="em.vu@club.edu.vn",
            phone="0922334455",
            date_of_birth=date(2005, 1, 8),
            gender="Khác",
            class_name="NNA-K17A",
            department="Ngôn ngữ Anh",
            committee_id=c_chuyen_mon.id,
            skills="ngôn ngữ Anh, biên tập",
            free_time="T2, T3, T4",
        ),
    ]
    db.add_all(members)
    db.commit()

    # Set committee leaders
    c_truyen_thong.leader_id = members[0].id
    c_to_chuc.leader_id = members[1].id
    c_chuyen_mon.leader_id = members[2].id
    db.commit()

    # ---- Users ----
    # Vai trò được gán cố định trong seed (không cho người dùng tự chọn khi
    # đăng ký). Tài khoản mới đăng ký luôn mặc định là "thanh_vien".
    users = [
        User(
            username="chunhiem",
            password_hash=hash_password("123456"),
            role="chu_nhiem",
            member_id=members[3].id,
            email="dung.pham@club.edu.vn",
            full_name="Phạm Thu Dung",
            auth_provider="local",
        ),
        User(
            username="truongbantt",
            password_hash=hash_password("123456"),
            role="truong_ban",
            member_id=members[0].id,
            email="an.nguyen@club.edu.vn",
            full_name="Nguyễn Văn An",
            auth_provider="local",
        ),
        User(
            username="thanhvien",
            password_hash=hash_password("123456"),
            role="thanh_vien",
            member_id=members[4].id,
            email="duc.hoang@club.edu.vn",
            full_name="Hoàng Minh Đức",
            auth_provider="local",
        ),
        # Tài khoản tạo qua social login — luôn có vai trò Thành viên (Member)
        User(
            username="google.demo",
            password_hash=unusable_password_hash(),
            role="thanh_vien",
            member_id=members[5].id,
            email="em.vu@club.edu.vn",
            full_name="Vũ Thị Em",
            auth_provider="google",
            provider_user_id="demo-google-em.vu",
        ),
        User(
            username="discord.demo",
            password_hash=unusable_password_hash(),
            role="thanh_vien",
            member_id=members[1].id,
            email="binh.tran@club.edu.vn",
            full_name="Trần Thị Bình",
            auth_provider="discord",
            provider_user_id="demo-discord-binh.tran",
        ),
    ]
    db.add_all(users)
    db.commit()

    # ---- Activities ----
    now = datetime.utcnow()
    activities = [
        Activity(
            title="Workshop Kỹ năng mềm - Giao tiếp hiệu quả",
            description="Buổi workshop chia sẻ kỹ năng giao tiếp, làm việc nhóm cho thành viên CLB",
            location="Hội trường A, Trường Đại học",
            start_time=now + timedelta(days=5, hours=2),
            end_time=now + timedelta(days=5, hours=5),
            notes="Chuẩn bị slide, microphone, nước uống. Diễn giả: Thầy Nguyễn Văn Hùng.",
            created_by=users[0].id,
        ),
        Activity(
            title="Tình nguyện viên - Ngày hội chào Tân sinh viên",
            description="Tham gia hỗ trợ tổ chức ngày hội chào đón tân sinh viên của trường",
            location="Sân trường Đại học",
            start_time=now + timedelta(days=10, hours=1),
            end_time=now + timedelta(days=10, hours=7),
            notes="Phân công 3 ca trực, chuẩn bị banner, bàn ghế.",
            created_by=users[0].id,
        ),
        Activity(
            title="Họp CLB định kỳ tháng",
            description="Họp tổng kết hoạt động tháng và triển khai kế hoạch mới",
            location="Phòng sinh hoạt CLB",
            start_time=now + timedelta(days=2, hours=3),
            end_time=now + timedelta(days=2, hours=5),
            notes="Điểm danh đầy đủ các ban. Cập nhật nhiệm vụ mới.",
            created_by=users[1].id,
        ),
    ]
    db.add_all(activities)
    db.commit()

    # ---- Hoạt động đang diễn ra HÔM NAY (để demo đăng ký + tự điểm danh) ----
    today_activity = Activity(
        title="Sinh hoạt chuyên đề: Kỹ năng thuyết trình",
        description="Buổi sinh hoạt chuyên đề hướng dẫn kỹ năng thuyết trình trước đám đông",
        location="Phòng B203, Trường Đại học",
        start_time=now - timedelta(minutes=15),
        end_time=now + timedelta(hours=2),
        notes="Có phần thực hành theo nhóm. Thành viên nhớ mang theo sổ tay.",
        created_by=users[0].id,
    )
    db.add(today_activity)
    db.commit()

    # ---- Đăng ký tham gia (Registration) ----
    registrations = [
        Registration(activity_id=today_activity.id, member_id=m.id)
        for m in [members[0], members[1], members[2], members[4], members[5]]
    ]
    registrations += [
        Registration(activity_id=a.id, member_id=m.id)
        for a in activities
        for m in [members[0], members[3], members[4]]
    ]
    db.add_all(registrations)
    db.commit()

    # ---- Attendance for past activity ----
    past_activity = Activity(
        title="Chương trình Teambuilding CLB",
        description="Hoạt động teambuilding gắn kết thành viên các ban",
        location="Công viên Thanh Niên",
        start_time=now - timedelta(days=15, hours=1),
        end_time=now - timedelta(days=15, hours=5),
        notes="Các trò chơi diễn ra thành công. Thành viên tham gia đầy đủ.",
        created_by=users[0].id,
    )
    db.add(past_activity)
    db.commit()

    attendances = []
    for i, m in enumerate(members):
        feedback = "Hoạt động bổ ích, mong có nhiều lần như vậy!" if i % 2 == 0 else "Chương trình khá hay, hy vọng lần sau tổ chức lâu hơn."
        attendances.append(
            Attendance(
                activity_id=past_activity.id,
                member_id=m.id,
                status="present" if i != 5 else "late",
                feedback=feedback,
                checked_at=now - timedelta(days=15),
            )
        )
    db.add_all(attendances)
    db.commit()

    # ---- Tasks ----
    tasks = [
        Task(
            title="Thiết kế banner sự kiện",
            description="Thiết kế banner cho workshop kỹ năng mềm - kích thước 1920x1080",
            activity_id=activities[0].id,
            assignee_id=members[3].id,
            status="in_progress",
            priority="high",
            due_date=now + timedelta(days=2),
        ),
        Task(
            title="Viết bài truyền thông",
            description="Viết bài giới thiệu workshop đăng fanpage",
            activity_id=activities[0].id,
            assignee_id=members[0].id,
            status="done",
            priority="medium",
            due_date=now + timedelta(days=1),
        ),
        Task(
            title="Chuẩn bị âm thanh hội trường",
            description="Kiểm tra micro, loa, máy chiếu trước sự kiện 1 ngày",
            activity_id=activities[0].id,
            assignee_id=members[2].id,
            status="todo",
            priority="high",
            due_date=now + timedelta(days=4),
        ),
        Task(
            title="Phân công tình nguyện viên các khâu",
            description="Lên danh sách phân công 3 ca trực sự kiện chào tân sinh viên",
            activity_id=activities[1].id,
            assignee_id=members[1].id,
            status="todo",
            priority="medium",
            due_date=now + timedelta(days=7),
        ),
    ]
    db.add_all(tasks)
    db.commit()

    # ---- AI notification sample ----
    ai_notif = Notification(
        title="Thông báo: Workshop Kỹ năng mềm",
        content=(
            "📢 THÔNG BÁO HOẠT ĐỘNG\n\n"
            "Xin chào các bạn thành viên CLB!\n\n"
            "Chúng ta sắp có hoạt động **Workshop Kỹ năng mềm - Giao tiếp hiệu quả** "
            "diễn ra vào ngày sắp tới tại Hội trường A, Trường Đại học.\n"
            "Nội dung: Buổi workshop chia sẻ kỹ năng giao tiếp, làm việc nhóm.\n\n"
            "Rất mong các bạn sắp xếp thời gian tham gia đầy đủ và đúng giờ!\n\n"
            "— Ban chủ nhiệm CLB"
        ),
        activity_id=activities[0].id,
        created_by=users[0].id,
        is_ai_generated=True,
    )
    db.add(ai_notif)
    db.commit()

    print("✅ Đã tạo dữ liệu mẫu thành công!")
    print("\nTài khoản đăng nhập (mật khẩu: 123456):")
    print("  - Chủ nhiệm:   chunhiem")
    print("  - Trưởng ban:  truongbantt")
    print("  - Thành viên:  thanhvien")
    print("\nTài khoản tạo qua social login (vai trò Thành viên, đăng nhập bằng")
    print("nút Google/Discord trên giao diện ở chế độ demo):")
    print("  - Google:  em.vu@club.edu.vn")
    print("  - Discord: binh.tran@club.edu.vn")
    print("\nDữ liệu: 3 ban, 6 thành viên, 5 hoạt động (1 hoạt động đang diễn ra),")
    print("đăng ký tham gia, điểm danh, nhiệm vụ, thông báo AI")


if __name__ == "__main__":
    seed()