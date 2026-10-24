Hệ thống quản lý câu lạc bộ sinh viên có tích hợp AI
1. Mô tả bài toán

Câu lạc bộ sinh viên cần quản lý thành viên, ban chuyên môn, hoạt động, điểm danh, nhiệm vụ và truyền thông. Nếu chỉ dùng biểu mẫu rời rạc, ban chủ nhiệm khó theo dõi đóng góp và tổng hợp hoạt động. Hệ thống cần quản lý câu lạc bộ và tích hợp AI sinh thông báo, tóm tắt hoạt động, gợi ý hoạt động phù hợp cho thành viên.
2. Mục tiêu

- Quản lý thành viên, ban, hoạt động, điểm danh, nhiệm vụ và báo cáo.
- Tích hợp AI để soạn nháp thông báo có thể biên tập, tóm tắt sau hoạt động và gợi ý hoạt động phù hợp cho thành viên.
- Sử dụng AI trong SDLC và lưu minh chứng sử dụng AI.
3. Yêu cầu chức năng
3.1. Chức năng quản lý
1. Đăng nhập và phân quyền chủ nhiệm, trưởng ban, thành viên.
2. Quản lý hồ sơ thành viên và ban chuyên môn.
3. Quản lý hoạt động, sự kiện nội bộ.
4. Điểm danh tham gia hoạt động.
5. Quản lý nhiệm vụ và tiến độ.
6. Quản lý thông báo nội bộ.
7. Tra cứu lịch sử tham gia của thành viên.
8. Thống kê hoạt động, đóng góp, thành viên tích cực.
3.2. Chức năng AI
1. AI sinh thông báo hoạt động cho thành viên.
2. AI tóm tắt kết quả hoạt động từ ghi chú và phản hồi.
3. AI gợi ý 3–5 hoạt động sắp tới cho thành viên dựa trên kỹ năng và lịch rảnh, kèm lý do và thao tác xem chi tiết / tham gia.
4. Yêu cầu kỹ thuật

- Backend FastAPI/Flask/Django; frontend React/Vue/HTML.
- CSDL SQLite/MySQL/PostgreSQL.
- AI Engine OpenAI/Gemini/Claude/Hugging Face/Ollama.
- Có test cho hoạt động, điểm danh, nhiệm vụ và AI.
5. Dữ liệu đầu vào, đầu ra và dữ liệu hệ thống

- Dữ liệu chính: thành viên, ban, hoạt động, điểm danh, nhiệm vụ, thông báo.
- Đầu vào AI: mô tả hoạt động, kỹ năng và lịch rảnh thành viên, ghi chú và phản hồi.
- Đầu ra AI: bản nháp thông báo, tóm tắt kết quả, gợi ý hoạt động phù hợp.

Prompt mẫu:

System: Bạn là trợ lý quản lý câu lạc bộ sinh viên. Viết ngắn gọn, thân thiện, không tự thêm thông tin chưa có.
User: Hoạt động: {{activity_info}}. Hồ sơ kỹ năng và lịch rảnh của thành viên: {{member_profile}}. Hãy gợi ý hoạt động phù hợp và nêu lý do.
6. Hướng dẫn sử dụng AI trong từng giai đoạn SDLC

- KT1: Dùng AI phân tích thành viên, hoạt động, nhiệm vụ; thiết kế use case và ERD.
- KT2: Dùng AI sinh CRUD thành viên, hoạt động, điểm danh, nhiệm vụ.
- KT3: Dùng AI thiết kế prompt sinh thông báo, tóm tắt và đề xuất hoạt động; test dữ liệu thiếu.
- Cuối kỳ: Dùng AI viết README, báo cáo, slide và hướng dẫn demo.
7. Mức độ khó

Cơ bản: Nghiệp vụ gần gũi với sinh viên, chức năng AI chủ yếu sinh nội dung và đề xuất hoạt động phù hợp.
