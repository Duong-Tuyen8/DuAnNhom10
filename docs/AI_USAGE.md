# 🤖 Minh chứng sử dụng AI trong SDLC (KT1 – KT3 – Cuối kỳ)

Tài liệu này ghi nhận cách AI được sử dụng trong từng giai đoạn phát triển phần mềm (SDLC)
cho đề tài **"Hệ thống quản lý câu lạc bộ sinh viên tích hợp AI"**.

---

## 1. Giai đoạn Phân tích (KT1)

### Mục tiêu
Phân tích đối tượng thành viên, hoạt động, nhiệm vụ; thiết kế use case và ERD.

### Cách dùng AI (Prompt mẫu đã sử dụng)

```
System: Bạn là chuyên gia phân tích hệ thống quản lý câu lạc bộ sinh viên.
User:  Tôi cần quản lý: thành viên, ban chuyên môn, hoạt động, điểm danh,
       nhiệm vụ, thông báo. Hãy:
       1) Đề xuất use case cho 3 vai trò (chủ nhiệm, trưởng ban, thành viên).
       2) Thiết kế ERD với bảng, khóa chính, khóa ngoại.
       3) Gợi ý các thuộc tính cần thiết (kỹ năng, lịch rảnh, feedback).
```

### Kết quả áp dụng vào hệ thống thực tế
| Ý tưởng từ AI | Nơi triển khai |
|---------------|----------------|
| Bảng `users` + phân quyền `role` (chu_nhiem / truong_ban / thanh_vien) | `backend/app/models.py` |
| Bảng `members` có `skills`, `free_time` để AI phân công | `models.py` |
| Bảng `committees` (ban chuyên môn), bảng `activities` | `models.py` |
| Bảng `attendances` có `feedback` làm đầu vào AI tóm tắt | `models.py` |
| Bảng `tasks` theo dõi tiến độ | `models.py` |

---

## 2. Giai đoạn Thiết kế & Code (KT2)

### Mục tiêu
Sinh CRUD cho thành viên, hoạt động, điểm danh, nhiệm vụ.

### Cách sử dụng AI (prompt mẫu)
```
System: Bạn là kỹ sư phát triển FastAPI.
User: Viết REST API CRUD cho thực thể "Activity" gồm các trường
      (title, description, location, start_time, end_time) với SQLAlchemy.
```

### Kết quả đã được triển khai
- Router CRUD: `members.py`, `committees.py`, `activities.py`, `attendance.py`, `tasks.py`, `notifications.py`.
- Pydantic schemas chuẩn hóa dữ liệu vào/ra: `schemas.py`.
- Bảo mật JWT và phân quyền theo vai trò: `security.py`.

---

## 3. Giai đoạn Test AI & Xử lý dữ liệu thiều (KT3)

### Mục tiêu
Thiết kế prompt sinh thông báo & phân công; test với dữ liệu thiếu.

### Prompt sinh thông báo (theo đề bài)

Prompt gốc từ đề bài:
```
System: Bạn là trợ lý quản lý câu lạc bộ sinh viên.
        Viết ngắn gọn, thân thiện, không tự thêm thông tin chưa có.
User: Hoạt động: {{activity_info}}. Danh sách thành viên và kỹ năng: {{member_skills}}.
      Hãy gợi ý phân công nhiệm vụ.
```

Được cài đặt trong `backend/app/ai/ai_service.py`:
- `build_notification_prompt()` – sinh thông báo.
- `build_summary_prompt()` – tóm tắt hoạt động từ ghi chú + phản hồi.
- `build_assignment_prompt()` – gợi ý phân công dựa trên ban/kỹ năng/lịch rảnh.

### Xử lý dữ liệu thiếu (edge cases)
| Tình huống thiếu dữ liệu | Cách hệ thống xử lý |
|---|---|
| Hoạt động không tồn tại | API trả `404 Hoạt động không tồn tại` |
| Không có phản hồi | AI tóm tắt với mặc định "Chưa có phản hồi" |
| Không có thành viên phù hợp | Gán "Chưa có thành viên phù hợp", kèm lý do |
| Không có nhiệm vụ | AI gợi ý danh sách nhiệm vụ mặc định (chuẩn bị địa điểm, truyền thông, đón tiếp) |
| Không có API key AI | Engine mẫu offline hoạt động, demo không gián đoạn |

### Test
- `backend/tests/test_ai.py` — test sinh thông báo, tóm tắt, phân công.
- `backend/tests/test_activities.py`, `test_attendance.py`, `test_tasks.py` — test quy trình nghiệp vụ.

---

## 4. Giai đoạn Đầu cuối (Báo cáo, README, Slide)

### Mục tiêu
Dùng AI hỗ trợ viết README, báo cáo, slide và hướng dẫn demo.

### Prompt sử dụng
```
System: Bạn là trợ lý viết tài liệu dự án.
User: Tóm tắt dự án "Hệ thống quản lý CLB sinh viên tích hợp AI" gồm
      mục tiêu, chức năng quản lý, chức năng AI, công nghệ, cách chạy.
      Viết README ngắn gọn cho sinh viên.
```

### Kết quả
- `README.md` — hướng dẫn cài đặt, chạy, tài khoản demo, cấu hình AI.
- Tài liệu này (`docs/AI_USAGE.md`) — minh chứng sử dụng AI qua các giai đoạn.

---

## 5. Kiến trúc AI Engine

```
API Client (frontend)
        │  HTTP /ai/*
        ▼
┌──────────────────────────────────┐
│  backend/app/routers/ai.py       │
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  ai_service.generate_text()       │
│   ├── OpenAI   (AI_PROVIDER=openai)   │
│   ├── Gemini   (AI_PROVIDER=gemini)   │
│   ├── Ollama   (AI_PROVIDER=ollama)   │
│   ├── HuggingFace                  │
│   └── Mock Engine (mặc định, offline)│
└──────────────────────────────────┘
```

---

## 6. Lợi ích đạt được

- Tăng tốc sinh mã nguồn CRUD và tài liệu.
- Tự động hóa khâu tạo thông báo, tóm tắt hoạt động, gợi ý phân công.
- Giảm công việc thủ công của ban chủ nhiệm.
- Hệ thống chạy được ngay cả khi không có API key (engine mẫu), thuận tiện demo.