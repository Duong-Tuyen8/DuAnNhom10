# 🎓 Hệ thống Quản lý CLB Sinh viên tích hợp AI

Đề tài 28: **Hệ thống quản lý câu lạc bộ sinh viên có tích hợp AI**

Hệ thống quản lý thành viên, ban chuyên môn, hoạt động, điểm danh, nhiệm vụ, thông báo
và thống kê cho câu lạc bộ sinh viên. Tích hợp AI để **sinh thông báo**, **tóm tắt hoạt động**
và **gợi ý hoạt động phù hợp cho thành viên**.

---

## 📚 Công nghệ sử dụng

| Thành phần | Công nghệ |
|-----------|-----------|
| Backend | FastAPI (Python) |
| Frontend | HTML + CSS + JavaScript thuần (Vanilla JS) |
| Cơ sở dữ liệu | SQLite (SQLAlchemy ORM) |
| Xác thực | JWT + OAuth2, phân quyền |
| AI Engine | OpenAI / Gemini / Hugging Face / Ollama + Engine mặc định (offline) |

## 🗂 Cấu trúc dự án

```
D:\DuAnNhom
├── backend/
│   ├── app/
│   │   ├── ai/ai_service.py          # AI engine (OpenAI/Gemini/Ollama/mock)
│   │   ├── routers/                # API endpoints
│   │   │   ├── auth.py             # Đăng nhập, đăng ký, phân quyền
│   │   │   ├── members.py          # Quản lý thành viên
│   │   │   ├── committees.py       # Quản lý ban chuyên môn
│   │   │   ├── activities.py       # Quản lý hoạt động
│   │   │   ├── attendance.py       # Điểm danh
│   │   │   ├── tasks.py            # Quản lý nhiệm vụ
│   │   │   ├── notifications.py    # Thông báo nội bộ
│   │   │   ├── ai.py               # Các chức năng AI
│   │   │   └── stats.py            # Thống kê & báo cáo
│   │   ├── models.py               # CSDL models
│   │   ├── schemas.py              # Pydantic schemas
│   │   ├── security.py             # JWT, hash password
│   │   └── database.py             # Kết nối SQLite
│   ├── tests/                      # Test pytest
│   ├── seed.py                     # Tạo dữ liệu mẫu
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/api.js, app.js
├── docs/
│   └── AI_USAGE.md                 # Minh chứng sử dụng AI trong SDLC
├── run_backend.bat
└── run_frontend.bat
```

---

## 🚀 Cài đặt & Chạy

### Yêu cầu
- Python 3.9+
- Trình duyệt web

### 1. Cài đặt dependencies và chạy backend

**Cách 1 — Dùng file tự động (khuyên dùng, Windows):**
```
Chạy đúp chuột vào run_backend.bat
```
File này sẽ tự tạo venv (ưu tiên `uv` nếu có), cài dependencies, seed dữ liệu và khởi động server.

**Cách 2 — Thủ công:**
```bash
cd D:\DuAnNhom\backend

# Tạo môi trường ao (neu co uv thi dung uv)
uv venv                       # hoac: python -m venv .venv

# Cai dependencies
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
# hoac: .venv\Scripts\activate && pip install -r requirements.txt

# Tao du lieu mau (chi lan dau)
.venv\Scripts\python.exe seed.py

# Chay server
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### 2. Chạy frontend
Mở file `D:\DuAnNhom\frontend\index.html` bằng trình duyệt (nên dùng Live Server trong VS Code)
hoặc chạy `run_frontend.bat`.

---

## 👤 Tài khoản đăng nhập mẫu

| Vai trò | Tên đăng nhập | Mật khẩu |
|---------|---------------|----------|
| 👑 Chủ nhiệm | `chunhiem` | `123456` |
| 🌟 Trưởng ban | `truongbantt` | `123456` |
| 👤 Thành viên | `thanhvien` | `123456` |

---

## 🤖 Cấu hình AI Engine

Mặc định hệ thống dùng **engine mẫu (offline)** để chạy demo không cần API key.
Để dùng model AI thật, đặt biến môi trường:

| Biến | Giá trị | Ví dụ |
|------|--------|-------|
| `AI_PROVIDER` | `openai` / `gemini` / `ollama` / `huggingface` | `openai` |
| `AI_API_KEY` | Khóa API | `sk-...` |
| `AI_MODEL` | Tên model (tùy chọn) | `gpt-4o-mini` |
| `AI_BASE_URL` | URL tùy chỉnh (tùy chọn) | - |

Ví dụ dùng OpenAI:
```bash
set AI_PROVIDER=openai
set AI_API_KEY=sk-xxxx
python -m uvicorn app.main:app --reload --port 8000
```

Ví dụ dùng Ollama (local):
```bash
set AI_PROVIDER=ollama
python -m uvicorn app.main:app --reload --port 8000
```

---

## 🧪 Chạy test

```bash
cd D:\DuAnNhom\backend
.venv\Scripts\python.exe -m pytest -v
```

Kết quả hiện tại: **83/83 PASSED** ✅

Test bao gồm: đăng nhập/phân quyền, hoạt động, điểm danh, nhiệm vụ, thành viên,
AI và thống kê.

---

## ✨ Chức năng chính

### Quản lý (CRUD)
- **Thành viên**: hồ sơ gồm họ tên, ngày sinh, giới tính, lớp, khoa, ngày tham gia; kỹ năng, lịch rảnh và lịch sử tham gia. Đăng ký tài khoản mới tự tạo hồ sơ thành viên liên kết với User.
- **Ban chuyên môn**: tạo ban, xem thành viên theo ban.
- **Hoạt động**: tạo hoạt động/sự kiện nội bộ, ghi chú.
- **Hoạt động & điểm danh**: thành viên đăng ký tham gia, nộp ảnh minh chứng khi điểm danh và theo dõi trạng thái chờ duyệt. Chủ nhiệm / Trưởng ban xem minh chứng, duyệt hoặc từ chối; thành viên có thể gửi lại ảnh sau khi bị từ chối.
- **Nhiệm vụ**: giao nhiệm vụ, theo dõi tiến độ, phân quyền cập nhật.
- **Thông báo**: thông báo nội bộ, đánh dấu thông báo do AI sinh.

### AI (Trợ lý AI)
1. 📢 **Soạn nháp thông báo hoạt động** từ dữ liệu hoạt động; Chủ nhiệm / Trưởng ban có thể chỉnh sửa rồi mới phát hành.
2. 📋 **Tóm tắt báo cáo sau hoạt động** từ số người đăng ký, lượt điểm danh đã duyệt, ghi chú và phản hồi.
3. 🎯 **Gợi ý hoạt động cho thành viên** dựa trên kỹ năng và lịch rảnh trong hồ sơ; thành viên có thể mở chi tiết hoặc đăng ký ngay.

### Thống kê & Báo cáo
- Tổng quan CLB, phân bố theo ban.
- Tỷ lệ tham gia từng hoạt động.
- Xếp hạng thành viên tích cực (điểm danh + nhiệm vụ hoàn thành).

---

## 📄 API Docs

Truy cập `http://localhost:8000/docs` sau khi chạy backend (Swagger UI).

### Luồng đăng ký, tham gia và điểm danh

1. `POST /auth/register` yêu cầu `username`, `password`, `full_name`, `date_of_birth` (YYYY-MM-DD), `gender` (`Nam`, `Nữ`, `Khác`), `class_name` và `department`. Backend kiểm tra các trường bắt buộc, tạo User cùng Member trong một luồng đăng ký và liên kết bằng `member_id`.
2. `GET /members` chỉ dành cho Chủ nhiệm / Trưởng ban; danh sách trả về ngày sinh, giới tính, lớp, khoa và `joined_date`.
3. Thành viên dùng `POST /api/activities/{id}/join` (hoặc `/activities/{id}/register`) để đăng ký; tài khoản thành viên không cần liên kết hồ sơ trước, hồ sơ Member được khởi tạo tự động nếu thiếu. Gửi `POST /api/activities/{id}/checkin` dưới dạng `multipart/form-data` với trường `photo` (JPEG, PNG, GIF hoặc WebP; tối đa 5 MB) để chuyển trạng thái sang `PENDING_CHECKIN`.
4. `GET /api/activities/{id}/participants` trả về ba nhóm trạng thái cho thành viên và ban quản lý; `GET /api/attendance/pending` trả về hàng đợi duyệt. Chủ nhiệm / Trưởng ban xem ảnh minh chứng (link yêu cầu xác thực) và gọi `PATCH /api/attendance/{attendance_id}/verify` với `{ "status": "APPROVED" }` hoặc `{ "status": "REJECTED", "reject_reason": "..." }`. Trạng thái sau duyệt là `ATTENDED`; sau từ chối là `REJECTED` và thành viên có thể điểm danh lại.

### Luồng trợ lý AI

1. Chủ nhiệm / Trưởng ban tạo bản nháp bằng `POST /ai/notifications` (dữ liệu hoạt động hiện có hoặc trường `title`, `description`, `location`, `start_time`, `end_time`). API chỉ trả nội dung nháp, không tạo thông báo.
2. Sau khi biên tập, phát hành bằng `POST /notifications` với `title`, `content`, `activity_id` và `is_ai_generated: true`.
3. Chủ nhiệm / Trưởng ban có thể gọi `POST /ai/summaries` cho hoạt động đã kết thúc; báo cáo kèm số đăng ký, số lượt điểm danh được duyệt, số phản hồi và bản tóm tắt.
4. Thành viên gọi `GET /ai/activity-recommendations?limit=5` để nhận tối đa 5 hoạt động sắp tới chưa đăng ký, kèm lý do dựa trên kỹ năng và lịch rảnh. API này chỉ dành cho role `thanh_vien`.

### Múi giờ và cửa sổ Trợ lý AI

- Thời gian hoạt động được lưu trong cơ sở dữ liệu theo UTC; API nhận ISO-8601 có múi giờ và chuẩn hóa về UTC. Frontend hiểu timestamp không có offset là UTC từ các bản ghi cũ, rồi hiển thị theo `Asia/Ho_Chi_Minh` với định dạng `HH:mm DD/MM/YYYY`.
- Trường thời gian `datetime-local` trong biểu mẫu được xem là giờ Việt Nam; khi gửi lên API sẽ chuyển thành UTC. Nội dung nháp thông báo cũng dùng giờ Việt Nam.
- Cửa sổ chat hỗ trợ kéo dãn hai chiều bằng tay nắm góc, tự giới hạn theo viewport và giữ ô nhập ở đáy.

---

Xem `docs/AI_USAGE.md` để biết cách hệ thống AI được sử dụng qua từng giai đoạn SDLC
(khâu phân tích → thiết kế → code → test → báo cáo cuối kỳ).