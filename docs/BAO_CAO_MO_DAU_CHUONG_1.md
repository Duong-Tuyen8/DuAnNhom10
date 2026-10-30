# BÁO CÁO ĐỒ ÁN HỌC PHẦN

## HỆ THỐNG QUẢN LÝ CÂU LẠC BỘ SINH VIÊN CÓ TÍCH HỢP AI

**Nhóm thực hiện:** Nhóm 10  
**Học phần:** ........................................................................  
**Giảng viên hướng dẫn:** ........................................................................  
**Trường/Khoa:** ........................................................................  
**Năm học:** .................................  

> **Hướng dẫn định dạng:** Khi chuyển tài liệu sang Word, áp dụng các kiểu Heading 1, Heading 2 và Heading 3 cho các cấp tiêu đề; cập nhật mục lục tự động; thay các dòng chấm bằng thông tin thực tế của nhóm. Các đoạn mã và sơ đồ văn bản nên dùng phông chữ đơn cách để giữ nguyên định dạng.

---

# DANH MỤC TỪ VIẾT TẮT

| Từ viết tắt | Tiếng Anh | Diễn giải |
|---|---|---|
| AI | Artificial Intelligence | Trí tuệ nhân tạo |
| API | Application Programming Interface | Giao diện lập trình ứng dụng |
| CRUD | Create, Read, Update, Delete | Tạo, đọc, cập nhật và xóa dữ liệu |
| DB | Database | Cơ sở dữ liệu |
| ERD | Entity–Relationship Diagram | Sơ đồ thực thể – liên kết |
| HTTP | Hypertext Transfer Protocol | Giao thức truyền tải siêu văn bản |
| JSON | JavaScript Object Notation | Định dạng trao đổi dữ liệu |
| LLM | Large Language Model | Mô hình ngôn ngữ lớn |
| PII | Personally Identifiable Information | Thông tin có khả năng định danh cá nhân |
| RAG | Retrieval-Augmented Generation | Sinh nội dung tăng cường bằng truy xuất dữ liệu |
| RBAC | Role-Based Access Control | Kiểm soát truy cập dựa trên vai trò |
| SDLC | Software Development Life Cycle | Vòng đời phát triển phần mềm |
| UI/UX | User Interface/User Experience | Giao diện và trải nghiệm người dùng |

# PHẦN MỞ ĐẦU

## 1. Đặt vấn đề và lý do chọn đề tài

Câu lạc bộ (CLB) sinh viên là môi trường để người học phát triển năng lực chuyên môn, kỹ năng làm việc nhóm, khả năng tổ chức và tinh thần trách nhiệm với cộng đồng. Để duy trì hoạt động liên tục, một CLB thường phải quản lý nhiều nhóm dữ liệu có quan hệ với nhau: hồ sơ thành viên, ban chuyên môn, hoạt động, đăng ký tham gia, điểm danh, nhiệm vụ, thông báo, ghi nhận đóng góp và phản hồi sau chương trình. Chất lượng quản trị các dữ liệu này ảnh hưởng trực tiếp đến khả năng lập kế hoạch, phân công nhân lực, tổng kết hoạt động và chăm sóc thành viên.

Trong thực tế, đặc biệt ở các CLB có quy mô vừa và nhỏ, công việc quản lý thường được chia nhỏ qua nhiều công cụ không đồng nhất. Danh sách thành viên có thể nằm trong bảng tính; đăng ký tham dự được thu qua biểu mẫu; lịch và thông báo được gửi trong nhóm nhắn tin; minh chứng điểm danh được lưu dưới dạng hình ảnh; còn phản hồi sau sự kiện được tổng hợp thủ công. Cách làm này thuận tiện khi quy mô nhỏ, nhưng dần bộc lộ các hạn chế:

1. **Dữ liệu phân tán và trùng lặp.** Thông tin của cùng một thành viên có thể xuất hiện ở nhiều bảng hoặc biểu mẫu. Khi thành viên thay đổi ban, số điện thoại hoặc trạng thái hoạt động, người quản lý phải cập nhật nhiều nơi.
2. **Khó kiểm soát phiên bản và quyền truy cập.** Bảng tính chia sẻ rộng có thể bị sửa nhầm, khó xác định ai đã thay đổi dữ liệu và vào thời điểm nào. Quyền xem thông tin cá nhân cũng không phải lúc nào được phân định theo nhiệm vụ.
3. **Quy trình phụ thuộc vào thao tác thủ công.** Ban tổ chức phải đối chiếu danh sách đăng ký, lập danh sách điểm danh, kiểm tra nhiệm vụ và tổng hợp số liệu sau sự kiện. Việc lặp lại thao tác làm tăng xác suất sai sót và tiêu tốn thời gian.
4. **Thiếu khả năng theo dõi xuyên suốt.** Thông tin từ giai đoạn tiếp nhận thành viên, tham gia hoạt động đến phản hồi sau chương trình thường không được liên kết thành lịch sử thống nhất. Vì vậy, người quản lý khó nhận diện xu hướng tham gia hoặc nhu cầu hỗ trợ của từng nhóm thành viên.
5. **Đánh giá hoạt động chưa có cơ sở định lượng đầy đủ.** Báo cáo thường dựa nhiều vào cảm nhận hoặc số liệu tổng hợp thủ công; các chỉ số như tỷ lệ đăng ký/tham dự, tỷ lệ hoàn thành nhiệm vụ, mức độ hài lòng và nguyên nhân phản hồi chưa được khai thác có hệ thống.
6. **Tra cứu thông tin lặp lại.** Thành viên thường hỏi về thời gian, địa điểm, quy trình đăng ký hoặc trạng thái điểm danh. Ban chủ nhiệm phải trả lời cùng một loại câu hỏi nhiều lần, trong khi thông tin có thể đã tồn tại trong dữ liệu của CLB.

Các công cụ bảng tính và nhắn tin vẫn hữu ích trong phạm vi riêng của chúng, nhưng không được thiết kế để điều phối toàn bộ vòng đời nghiệp vụ của một CLB. Do đó, đề tài lựa chọn xây dựng một hệ thống web quản lý tập trung, trong đó các quy trình quan trọng được biểu diễn thành dữ liệu có cấu trúc và có thể truy xuất thống nhất. Hệ thống đồng thời tích hợp AI như một công cụ hỗ trợ sinh nội dung, tra cứu và tổng hợp, thay vì giao cho AI quyền tự quyết định các nghiệp vụ có ảnh hưởng đến thành viên.

Đề tài có ý nghĩa ở hai phương diện. Về thực tiễn, sản phẩm hướng đến giảm thao tác lặp, tăng khả năng theo dõi và cải thiện tính nhất quán trong vận hành CLB. Về học thuật và kỹ thuật, nhóm có cơ hội áp dụng kiến thức phân tích yêu cầu, thiết kế cơ sở dữ liệu, phát triển API, xây dựng giao diện, kiểm thử và tích hợp mô hình AI trong một bài toán có người dùng và quy trình cụ thể.

## 2. Mục tiêu nghiên cứu

### 2.1. Mục tiêu tổng quát

Phân tích, thiết kế và xây dựng hệ thống quản lý hoạt động câu lạc bộ sinh viên có tích hợp các chức năng AI hỗ trợ, nhằm tập trung hóa dữ liệu, chuẩn hóa quy trình vận hành và nâng cao khả năng khai thác thông tin từ hoạt động của CLB.

### 2.2. Mục tiêu cụ thể

- Khảo sát và mô hình hóa các quy trình chính: quản lý hồ sơ thành viên, phân công ban, tạo hoạt động, đăng ký, điểm danh, giao nhiệm vụ, gửi thông báo và tổng kết hoạt động.
- Xây dựng backend cung cấp API để quản lý dữ liệu và thực thi quy tắc nghiệp vụ; áp dụng xác thực và phân quyền theo các vai trò như Chủ nhiệm, Trưởng ban và Thành viên.
- Xây dựng giao diện web giúp người dùng thực hiện nghiệp vụ theo vai trò. Phiên bản mã nguồn hiện tại sử dụng HTML, CSS và JavaScript thuần; ReactJS được xem là phương án giao diện tham khảo trong thiết kế mở rộng, không phải công nghệ đã được xác nhận là đang triển khai trong bản hiện có.
- Tích hợp AI theo hướng có kiểm soát để hỗ trợ:
  - trả lời câu hỏi về hoạt động dựa trên dữ liệu CLB được truy xuất từ cơ sở dữ liệu;
  - tạo bản nháp thông báo hoặc nội dung sự kiện từ dữ kiện do người quản lý cung cấp;
  - tóm tắt ghi chú và phản hồi sau sự kiện;
  - gợi ý hoạt động phù hợp với thông tin kỹ năng và lịch rảnh của thành viên khi dữ liệu cho phép.
- Thiết kế dữ liệu và ràng buộc nhằm hạn chế đăng ký trùng, kiểm soát tính hợp lệ của thời gian hoạt động và đảm bảo bản ghi điểm danh có thể đối chiếu với thành viên và hoạt động tương ứng.
- Đề xuất cách kiểm thử, triển khai và theo dõi hệ thống phù hợp với quy mô đồ án; nêu rõ các giới hạn của phiên bản hiện tại và hướng phát triển tiếp theo.

### 2.3. Tiêu chí đánh giá mục tiêu

| Mã | Tiêu chí | Minh chứng dự kiến |
|---|---|---|
| MT-01 | Các nghiệp vụ chính được mô hình hóa và liên kết thành quy trình nhất quán | Mô tả quy trình, use case, thiết kế dữ liệu |
| MT-02 | Người dùng có thể quản lý và tra cứu dữ liệu CLB qua hệ thống | Giao diện và API của thành viên, ban, hoạt động, điểm danh, nhiệm vụ |
| MT-03 | Quyền thao tác được phân biệt theo vai trò | Quy tắc RBAC ở backend và kịch bản kiểm thử quyền |
| MT-04 | AI sử dụng dữ liệu có nguồn gốc từ hệ thống, không tự khẳng định thông tin ngoài dữ liệu | Prompt, context được dựng từ DB, phản hồi mẫu và giới hạn an toàn |
| MT-05 | Các luồng cốt lõi có thể kiểm thử lặp lại | Unit test và integration test cho API |
| MT-06 | Có hướng dẫn cấu hình, chạy thử và đánh giá giới hạn | Hướng dẫn vận hành, cấu hình môi trường và phần đánh giá |

## 3. Câu hỏi nghiên cứu và định hướng giải quyết

Đề tài tập trung trả lời các câu hỏi sau:

1. Làm thế nào mô hình hóa dữ liệu và quy trình để thông tin thành viên, hoạt động, đăng ký và điểm danh được quản lý tập trung?
2. Làm thế nào bảo đảm các thao tác nhạy cảm, chẳng hạn tạo hoạt động hoặc xác minh điểm danh, chỉ được thực hiện bởi vai trò phù hợp?
3. Có thể khai thác mô hình ngôn ngữ để hỗ trợ tra cứu và soạn thảo nội dung mà vẫn hạn chế việc tạo ra thông tin không có trong dữ liệu nguồn hay không?
4. Những rủi ro về quyền riêng tư, chất lượng câu trả lời và chi phí gọi mô hình cần được kiểm soát bằng cơ chế nào?

Định hướng giải quyết là tách bạch trách nhiệm giữa hệ thống nghiệp vụ và AI. Backend chịu trách nhiệm xác thực, phân quyền, kiểm tra ràng buộc, truy xuất dữ liệu và ghi nhận các giao dịch. AI chỉ nhận phần ngữ cảnh tối thiểu cần thiết để tạo gợi ý hoặc bản nháp. Kết quả AI không tự động thay thế quyết định của người có thẩm quyền; đặc biệt, thông báo do AI soạn cần được người quản lý xem xét trước khi phát hành.

## 4. Đối tượng và phạm vi nghiên cứu

### 4.1. Đối tượng nghiên cứu

- Quy trình quản lý câu lạc bộ sinh viên trong môi trường đại học.
- Các nhóm người dùng: Chủ nhiệm, Trưởng ban và Thành viên.
- Mô hình dữ liệu và API phục vụ quản lý thành viên, ban chuyên môn, hoạt động, đăng ký, điểm danh, nhiệm vụ, thông báo và thống kê.
- Cách tích hợp AI vào một ứng dụng nghiệp vụ theo hướng truy xuất dữ liệu có căn cứ, giới hạn quyền của mô hình và bảo vệ dữ liệu cá nhân.

### 4.2. Phạm vi chức năng

Trong phạm vi đồ án, hệ thống tập trung vào các chức năng:

- Đăng nhập, đăng ký tài khoản và phân quyền cơ bản.
- Quản lý hồ sơ thành viên và ban chuyên môn.
- Tạo, xem, cập nhật và tra cứu hoạt động.
- Đăng ký/hủy đăng ký hoạt động và ghi nhận trạng thái điểm danh.
- Quản lý nhiệm vụ gắn với thành viên hoặc hoạt động.
- Tạo thông báo và cung cấp thống kê phục vụ quản trị.
- Tích hợp các chức năng AI hỗ trợ soạn nội dung, hỏi đáp dựa trên ngữ cảnh CLB, tóm tắt kết quả hoạt động và gợi ý hoạt động.

Các yêu cầu như quản lý quỹ CLB độc lập, quy trình tuyển thành viên nhiều vòng, chấm điểm rèn luyện theo quy chế chính thức, giới hạn sức chứa sự kiện có cơ chế chống tranh chấp đồng thời, nhật ký kiểm toán đầy đủ và tích hợp sâu với hệ thống đào tạo của nhà trường được trình bày như yêu cầu thiết kế hoặc hướng mở rộng. Không nên xem đây là chức năng đã hoàn thiện nếu chưa có bảng dữ liệu, API và kiểm thử tương ứng trong phiên bản triển khai.

### 4.3. Phạm vi kỹ thuật và giới hạn

Phiên bản mã nguồn được khảo sát có backend xây dựng bằng FastAPI, ORM SQLAlchemy và cơ sở dữ liệu SQLite theo cấu hình mặc định. Giao diện trong thư mục sản phẩm là HTML/CSS/JavaScript thuần và được backend phục vụ dưới dạng tệp tĩnh. Hệ thống có các thực thể như tài khoản, thành viên, ban, hoạt động, đăng ký, điểm danh, nhiệm vụ và thông báo. Dữ liệu phản hồi hiện gắn với bản ghi điểm danh; chưa có bảng `Feedbacks` độc lập. Mô hình hiện tại cũng chưa có thực thể tài chính/quỹ và chưa thể hiện giới hạn số lượng người tham gia ở bảng hoạt động.

Vì vậy, báo cáo phân biệt hai lớp:

- **Thiết kế mục tiêu:** nghiệp vụ và cấu trúc được đề xuất để đáp ứng đầy đủ bài toán quản lý CLB.
- **Hiện trạng mã nguồn:** những gì có thể xác nhận từ các mô hình và luồng đang có trong dự án.

Các ví dụ ReactJS trong báo cáo (nếu được dùng ở các chương tiếp theo) là minh họa cho một phương án giao diện theo đề cương; chúng không được diễn giải thành bằng chứng rằng frontend hiện tại đã được viết bằng ReactJS.

### 4.4. Phương pháp nghiên cứu

Nhóm sử dụng kết hợp các phương pháp sau:

1. **Phân tích nghiệp vụ:** xác định tác nhân, đầu vào, đầu ra, quy tắc và ngoại lệ của từng quy trình CLB.
2. **Mô hình hóa hệ thống:** sử dụng sơ đồ luồng, sơ đồ kiến trúc và ERD để thể hiện trách nhiệm của từng thành phần.
3. **Thiết kế và hiện thực phần mềm:** xây dựng API, mô hình dữ liệu và giao diện người dùng theo kiến trúc client–server.
4. **Tích hợp AI có kiểm soát:** lấy ngữ cảnh từ dữ liệu ứng dụng, giới hạn phạm vi trả lời và giữ người dùng có thẩm quyền trong vòng phê duyệt.
5. **Kiểm thử:** kiểm tra các quy tắc quan trọng ở cấp đơn vị và luồng tích hợp; chú trọng quyền truy cập, dữ liệu biên và lỗi nghiệp vụ.
6. **Đánh giá:** đối chiếu chức năng với tiêu chí ban đầu, ghi nhận giới hạn, rủi ro và đề xuất cải tiến.

## 5. Bố cục báo cáo

Báo cáo được tổ chức theo hướng đi từ bài toán đến sản phẩm và vận hành. Phần mở đầu nêu lý do, mục tiêu và phạm vi. Chương 1 phân tích nghiệp vụ, yêu cầu và kiến trúc dữ liệu. Các chương tiếp theo dự kiến trình bày cách ứng dụng AI Agent trong SDLC, quá trình hoàn thiện phần mềm, đóng gói và vận hành. Phần kết luận tổng kết mức độ đạt mục tiêu, bài học kinh nghiệm và hướng phát triển.

---

# CHƯƠNG 1. PHÂN TÍCH BÀI TOÁN VÀ THIẾT KẾ GIẢI PHÁP

## 1.1. Phân tích nghiệp vụ hệ thống quản lý câu lạc bộ sinh viên

### 1.1.1. Tác nhân và vai trò nghiệp vụ

Hệ thống có ba vai trò người dùng chính. Quyền thao tác cần được kiểm tra ở backend; việc ẩn nút trên giao diện chỉ có ý nghĩa hỗ trợ trải nghiệm và không thay thế kiểm tra quyền phía máy chủ.

| Vai trò | Trách nhiệm nghiệp vụ | Quyền điển hình |
|---|---|---|
| Chủ nhiệm | Điều phối hoạt động chung, quản lý nhân sự và chịu trách nhiệm phê duyệt | Quản lý thành viên, ban, hoạt động, thông báo; xem thống kê; xử lý các quyết định quản trị |
| Trưởng ban | Lập kế hoạch và tổ chức công việc trong phạm vi ban hoặc hoạt động được giao | Quản lý nhiệm vụ, cập nhật hoạt động theo quyền được cấp, theo dõi đăng ký và xác minh điểm danh theo chính sách |
| Thành viên | Cập nhật thông tin cá nhân, theo dõi lịch, đăng ký và tham gia hoạt động | Xem hoạt động, đăng ký/hủy đăng ký, gửi minh chứng hoặc phản hồi, xem nhiệm vụ của mình |

Trong phiên bản hiện có, vai trò được biểu diễn bằng các giá trị như `chu_nhiem`, `truong_ban` và `thanh_vien`. Quy tắc phân quyền chi tiết cần được đặc tả theo từng endpoint, tránh sử dụng quy tắc mơ hồ kiểu “người quản lý” nếu thực tế một hành động chỉ dành cho Chủ nhiệm.

### 1.1.2. Quy trình tiếp nhận, xét duyệt thành viên mới và phân công ban

Quy trình đề xuất gồm các bước:

1. **Nộp thông tin:** ứng viên tạo tài khoản và cung cấp các trường cơ bản theo chính sách của CLB. Hệ thống kiểm tra tính đầy đủ, định dạng email và tính duy nhất của mã sinh viên/tên đăng nhập.
2. **Ghi nhận hồ sơ:** hồ sơ được lưu với trạng thái nghiệp vụ ban đầu, chẳng hạn `pending_review`. Ở bước này tài khoản không nên tự cấp quyền quản trị.
3. **Xét duyệt:** Chủ nhiệm hoặc người được ủy quyền xem hồ sơ, đối chiếu tiêu chí và ghi nhận quyết định cùng thời điểm, người duyệt và lý do phù hợp.
4. **Thông báo kết quả:** hệ thống gửi thông báo chấp nhận, từ chối hoặc yêu cầu bổ sung. Nội dung do AI hỗ trợ soạn (nếu có) vẫn cần người có quyền kiểm tra.
5. **Phân công ban:** thành viên được chấp nhận có thể được gán vào một ban chuyên môn. Việc phân ban cần xem xét nhu cầu tổ chức, nguyện vọng và khả năng tham gia; AI có thể đề xuất nhưng không nên tự quyết định.
6. **Theo dõi trạng thái:** hồ sơ có thể chuyển giữa các trạng thái được quy định, đồng thời giữ lại lịch sử thay đổi để phục vụ tra cứu.

Các trạng thái tham khảo cho một luồng tuyển mới là `pending_review`, `accepted`, `rejected` và `needs_information`. Đây là trạng thái nghiệp vụ mục tiêu; không đồng nghĩa với việc phiên bản dữ liệu hiện tại đã có bảng đơn đăng ký tuyển thành viên. Trong mô hình hiện có, tài khoản mới được gán vai trò thành viên mặc định và hồ sơ thành viên có thể được tạo/cập nhật theo luồng đăng ký tài khoản. Nếu cần quy trình tuyển chọn chính thức, nên bổ sung thực thể hồ sơ ứng tuyển và lịch sử quyết định thay vì suy diễn trạng thái từ tài khoản đăng nhập.

**Ngoại lệ cần xử lý:** tài khoản trùng email hoặc mã sinh viên; người dùng gửi lại biểu mẫu; hồ sơ thiếu thông tin; thành viên rời CLB; người duyệt không đủ quyền; thao tác phân ban dẫn đến thành viên bị gán vào đơn vị không tồn tại. Các trường hợp này phải trả thông báo rõ ràng và không để lại dữ liệu ở trạng thái nửa hoàn tất.

### 1.1.3. Quy trình tổ chức sự kiện, đăng ký, điểm danh và ghi nhận đóng góp

Quy trình chuẩn hóa được mô tả như sau:

**Bước 1 – Lập kế hoạch:** người có quyền tạo hoạt động với tên, mô tả, thời gian bắt đầu/kết thúc, địa điểm và ghi chú. Backend xác thực `end_time > start_time`; các thông tin AI sinh ra chỉ là nội dung gợi ý để người tạo rà soát.

**Bước 2 – Công bố hoạt động:** hoạt động được hiển thị trong danh sách phù hợp với chính sách truy cập. Một hoạt động chỉ nên được coi là có thể đăng ký khi còn hiệu lực và chưa quá thời hạn đăng ký (nếu quy định thời hạn).

**Bước 3 – Đăng ký:** thành viên đăng ký bằng tài khoản của mình. Hệ thống phải xác thực thành viên, hoạt động tồn tại, hoạt động chưa kết thúc và thành viên chưa đăng ký trước đó. Cơ sở dữ liệu cần ràng buộc duy nhất trên cặp `(activity_id, member_id)` để ngăn đăng ký trùng kể cả khi hai yêu cầu đến gần như đồng thời.

**Bước 4 – Kiểm tra sức chứa:** nếu hoạt động có giới hạn số lượng, việc kiểm tra còn chỗ và tạo đăng ký phải được thực hiện trong một giao dịch an toàn. Cách “đếm người đăng ký rồi thêm bản ghi” mà không khóa hoặc cập nhật nguyên tử có thể vượt giới hạn khi nhiều người thao tác đồng thời. Phiên bản hiện tại có ràng buộc đăng ký trùng nhưng không có trường `capacity` trong mô hình `Activity`; do đó, giới hạn sức chứa là yêu cầu thiết kế cần bổ sung nếu được yêu cầu ở bản giao cuối.

**Bước 5 – Điểm danh:** thành viên đã đăng ký thực hiện check-in trong khoảng thời gian cho phép. Tùy hình thức vận hành, hệ thống có thể ghi nhận trực tiếp hoặc yêu cầu tải ảnh minh chứng để người quản lý xác minh. Luồng minh chứng cần có trạng thái chờ duyệt, được duyệt hoặc bị từ chối, kèm người duyệt, thời gian xử lý và lý do.

**Bước 6 – Tổng kết và ghi nhận:** sau hoạt động, người tổ chức tổng hợp số lượt đăng ký, số lượt tham dự, nhiệm vụ hoàn thành và phản hồi. Nếu nhà trường yêu cầu điểm rèn luyện, hệ thống chỉ nên ghi nhận dữ liệu tham gia và xuất báo cáo theo quy định; việc quy đổi thành điểm chính thức phải tuân theo quy chế của đơn vị có thẩm quyền. Không nên để AI tự gán điểm rèn luyện.

Luồng trạng thái điểm danh cần được thống nhất trên toàn hệ thống. Mô hình hiện tại có các trạng thái phục vụ các phiên bản và cách điểm danh khác nhau, gồm trạng thái chờ/đã gửi minh chứng/đã duyệt/từ chối và một số giá trị cũ như `present`, `absent`, `late`. Khi phát triển tiếp, nên chuẩn hóa enum trạng thái, quy định ánh xạ tương thích dữ liệu cũ và dùng cùng một bộ trạng thái trong API, giao diện, báo cáo và chatbot.

### 1.1.4. Quy trình thu thập phản hồi và chăm sóc thành viên

Sau khi sự kiện kết thúc, ban tổ chức thu thập phản hồi theo biểu mẫu phù hợp. Dữ liệu có thể bao gồm mức độ hài lòng, nội dung hữu ích, vấn đề gặp phải và đề xuất cải thiện. Một quy trình có thể gồm:

1. Hệ thống xác định sự kiện đã kết thúc và danh sách người được mời phản hồi.
2. Thành viên gửi phản hồi; dữ liệu được gắn với sự kiện và được bảo vệ theo chính sách quyền riêng tư.
3. Người quản lý theo dõi tỷ lệ phản hồi và xem số liệu tổng quan.
4. AI phân nhóm chủ đề hoặc tóm tắt ý kiến ở dạng tổng hợp, không đưa ra kết luận vượt quá dữ liệu đầu vào.
5. Ban tổ chức rà soát bản tóm tắt, bổ sung ngữ cảnh và xác định hành động cải thiện.
6. Kết quả được lưu cùng sự kiện hoặc báo cáo tổng kết để phục vụ lập kế hoạch ở lần tiếp theo.

Trong mô hình hiện có, trường `feedback` được gắn với bản ghi `Attendance`; API tổng kết có thể sử dụng các phản hồi này cùng ghi chú sự kiện và số lượng người tham dự. Nếu cần khảo sát nhiều câu hỏi, nhiều lựa chọn, ẩn danh hoặc nhiều lần gửi, cần thiết kế các bảng `FeedbackForms`, `FeedbackQuestions` và `FeedbackResponses` riêng. Không nên nhồi mọi câu trả lời khảo sát vào một trường văn bản duy nhất vì sẽ hạn chế khả năng thống kê và kiểm soát quyền.

Việc chăm sóc thành viên không chỉ là gửi tin nhắn tự động. Dữ liệu tham gia có thể giúp phát hiện thành viên ít tương tác hoặc nhiệm vụ chậm tiến độ, nhưng hệ thống nên đưa ra tín hiệu hỗ trợ để cán bộ CLB xem xét thay vì tự gắn nhãn tiêu cực. Các gợi ý cá nhân hóa phải giải thích được dựa trên dữ liệu nào và cần cho phép người dùng cập nhật kỹ năng, lịch rảnh hoặc lựa chọn nhận thông báo.

### 1.1.5. Quy trình nghiệp vụ tổng quát

```text
Ứng viên/Thành viên       Chủ nhiệm/Trưởng ban          Hệ thống
        |                         |                        |
        |-- gửi hồ sơ ------------>|                        |
        |                         |-- xét duyệt hồ sơ ----->|
        |<------ thông báo kết quả -------------------------|
        |                         |                        |
        |<------ xem lịch hoạt động ------------------------|
        |-- đăng ký hoạt động ----------------------------->|
        |                         |<-- kiểm tra danh sách --|
        |-- check-in/minh chứng --------------------------->|
        |                         |-- xác minh điểm danh -->|
        |-- gửi phản hồi ---------------------------------->|
        |                         |<-- xem báo cáo/tóm tắt --|
        |                         |                        |
        |       AI chỉ hỗ trợ tra cứu, soạn nháp và tổng hợp |
        |      ; quyết định nghiệp vụ thuộc người có quyền. |
```

### 1.1.6. Quy tắc nghiệp vụ cốt lõi

| Mã | Quy tắc | Cách kiểm tra đề xuất |
|---|---|---|
| BR-01 | Tên đăng nhập, mã sinh viên và email (nếu bắt buộc) không được trùng | Ràng buộc duy nhất ở DB và kiểm tra lỗi thân thiện ở API |
| BR-02 | Tài khoản đăng ký mới không được tự chọn vai trò quản trị | Backend gán vai trò mặc định; không tin trường role do client gửi |
| BR-03 | Thời gian kết thúc hoạt động phải sau thời gian bắt đầu | Kiểm tra ở schema/service trước khi commit |
| BR-04 | Một thành viên chỉ có một đăng ký cho một hoạt động | Unique constraint `(activity_id, member_id)` |
| BR-05 | Không đăng ký hoạt động đã kết thúc | Kiểm tra thời gian ở backend theo cùng quy ước múi giờ |
| BR-06 | Điểm danh phải liên quan đến thành viên và hoạt động hợp lệ | Khóa ngoại; kiểm tra đăng ký nếu nghiệp vụ yêu cầu đăng ký trước |
| BR-07 | Chỉ vai trò phù hợp mới được tạo, sửa, xóa hoặc xác minh dữ liệu | Dependency RBAC tại backend cho từng endpoint |
| BR-08 | AI không tự thêm thời gian, địa điểm hoặc chính sách không có trong dữ liệu | Context được lấy từ DB; prompt quy định không suy đoán; UI hiển thị giới hạn |
| BR-09 | Bản nháp AI phải được người quản lý duyệt trước khi phát hành | Tách endpoint tạo nháp khỏi thao tác lưu/gửi thông báo |
| BR-10 | Nếu có giới hạn chỗ, không được vượt sức chứa khi có đăng ký đồng thời | Giao dịch/khóa hoặc cập nhật nguyên tử; kiểm thử tải đồng thời |
| BR-11 | Chỉ tổng hợp phản hồi sau khi hoạt động kết thúc hoặc khi người có quyền cho phép | Kiểm tra thời điểm và quyền truy cập ở backend |
| BR-12 | Dữ liệu cá nhân chỉ được dùng đúng mục đích và trong phạm vi cần thiết | Lọc trường trước khi tạo context cho AI; chính sách lưu trữ và truy cập |

## 1.2. Yêu cầu chức năng và phi chức năng

### 1.2.1. Nhóm chức năng quản lý cốt lõi

| Mã | Chức năng | Mô tả và kết quả mong đợi | Vai trò chính |
|---|---|---|---|
| FR-01 | Xác thực tài khoản | Đăng nhập/đăng ký; lưu mật khẩu dạng băm; trả lỗi xác thực rõ ràng | Tất cả |
| FR-02 | Phân quyền | Giới hạn thao tác theo vai trò, kiểm tra tại backend | Tất cả |
| FR-03 | Quản lý hồ sơ thành viên | Xem/cập nhật hồ sơ, kỹ năng, lịch rảnh và trạng thái hoạt động theo quyền | Chủ nhiệm, Trưởng ban, Thành viên |
| FR-04 | Quản lý ban chuyên môn | Tạo và cập nhật ban, mô tả, trưởng ban; phân công thành viên | Chủ nhiệm |
| FR-05 | Quản lý hoạt động | Tạo, xem, cập nhật và xóa hoạt động; kiểm tra thời gian hợp lệ | Chủ nhiệm, Trưởng ban |
| FR-06 | Đăng ký hoạt động | Đăng ký/hủy đăng ký, ngăn trùng, thông báo kết quả và số lượt đăng ký | Thành viên |
| FR-07 | Điểm danh | Ghi nhận check-in, minh chứng và trạng thái xác minh | Thành viên, người xác minh |
| FR-08 | Quản lý nhiệm vụ | Tạo nhiệm vụ, giao người phụ trách, đặt hạn và cập nhật tiến độ | Chủ nhiệm, Trưởng ban, Thành viên |
| FR-09 | Thông báo | Soạn, lưu và hiển thị thông báo gắn với hoạt động; đánh dấu nguồn AI nếu có | Chủ nhiệm, Trưởng ban |
| FR-10 | Thống kê và báo cáo | Tổng hợp số thành viên, hoạt động, đăng ký, điểm danh, nhiệm vụ và mức độ tham gia | Chủ nhiệm, Trưởng ban |
| FR-11 | Quản lý tài chính/quỹ | Ghi nhận khoản thu/chi, danh mục, ngày giao dịch, người tạo và chứng từ | Đề xuất mở rộng; cần bảng và API riêng |
| FR-12 | Tiếp nhận hồ sơ thành viên | Lưu hồ sơ ứng tuyển, trạng thái xét duyệt và lịch sử quyết định | Đề xuất mở rộng nếu cần tuyển chọn nhiều bước |
| FR-13 | Khảo sát sau sự kiện | Thu câu trả lời có cấu trúc, thống kê và xuất dữ liệu | Hiện trạng dùng phản hồi gắn điểm danh; khảo sát nhiều câu hỏi cần mở rộng |

Quản lý quỹ được đưa vào yêu cầu tổng thể theo đề cương, nhưng cần lưu ý mô hình hiện tại không có bảng giao dịch tài chính. Khi bổ sung, không nên lưu tổng số dư như một giá trị độc lập dễ mất đồng bộ; số dư có thể được tính từ các giao dịch đã xác nhận hoặc được quản lý qua sổ quỹ có đối soát. Các nghiệp vụ tài chính cần quyền truy cập, dấu vết chỉnh sửa và quy tắc chứng từ rõ ràng.

### 1.2.2. Nhóm chức năng AI

| Mã | Chức năng AI | Đầu vào | Đầu ra | Kiểm soát bắt buộc |
|---|---|---|---|---|
| AI-01 | Hỏi đáp CLB | Câu hỏi người dùng và context hoạt động/quy định được truy xuất | Câu trả lời ngắn, có căn cứ | Chỉ dùng context; nói rõ khi thiếu dữ liệu; không bịa lịch |
| AI-02 | Sinh bản nháp thông báo/kế hoạch | Tên, thời gian, địa điểm, mục tiêu và ghi chú | Bản nháp để biên tập | Không tự phát hành; người có quyền duyệt |
| AI-03 | Tóm tắt phản hồi | Ghi chú, phản hồi đã thu thập và số liệu tổng hợp | Chủ đề nổi bật, điểm tích cực, vấn đề và đề xuất | Không tiết lộ danh tính; phân biệt dữ kiện và suy luận |
| AI-04 | Gợi ý hoạt động | Kỹ năng/lịch rảnh đã được người dùng cung cấp và danh sách hoạt động sắp tới | Danh sách hoạt động phù hợp kèm lý do | Không khẳng định phù hợp tuyệt đối; không dùng dữ liệu nhạy cảm không cần thiết |

Một yêu cầu quan trọng là không để mô hình AI trở thành nguồn dữ liệu chuẩn. Dữ liệu lịch hoạt động phải lấy từ cơ sở dữ liệu; kết quả tạo sinh chỉ là cách diễn đạt hoặc sắp xếp thông tin. Với những thao tác có hậu quả nghiệp vụ như duyệt thành viên, xác nhận điểm danh hoặc duyệt chi, hệ thống phải yêu cầu người có thẩm quyền thực hiện.

### 1.2.3. Yêu cầu phi chức năng

| Nhóm | Yêu cầu | Tiêu chí/định hướng |
|---|---|---|
| Bảo mật | Xác thực mọi API riêng tư, phân quyền phía máy chủ, băm mật khẩu, bảo vệ khóa AI | Không đưa khóa bí mật vào mã nguồn hoặc frontend |
| Quyền riêng tư | Chỉ thu thập dữ liệu cần thiết, hạn chế dữ liệu PII trong prompt | Ẩn danh hoặc loại bỏ tên, email, mã sinh viên khi không cần |
| Tính đúng đắn | Ràng buộc dữ liệu và quy tắc nghiệp vụ được kiểm tra tại backend/DB | Không dựa duy nhất vào kiểm tra giao diện |
| Tính sẵn sàng | Lỗi DB hoặc AI được báo rõ, không trả về thông báo thành công giả | Có health endpoint và log lỗi phù hợp |
| Hiệu năng | Các thao tác CRUD thông thường cần phản hồi nhanh trong môi trường demo | Đo trên cùng cấu hình; báo cáo số liệu thực nghiệm thay vì ước lượng |
| Khả năng sử dụng | Nhãn giao diện rõ ràng, thông báo lỗi dễ hiểu, hỗ trợ luồng theo vai trò | Kiểm tra trên màn hình máy tính và thiết bị phổ biến |
| Khả năng bảo trì | Tách router, schema, model, dịch vụ AI và cấu hình | Thay đổi quy tắc ít ảnh hưởng đến lớp khác |
| Khả năng kiểm thử | Có kiểm thử cho ràng buộc, quyền và luồng đăng ký/điểm danh | Dùng DB thử nghiệm; tránh phụ thuộc dịch vụ AI thật trong test |
| Khả năng mở rộng | Có thể thay SQLite bằng DB máy chủ và tách AI provider khi cần | Cấu hình qua biến môi trường và interface dịch vụ |
| Khả năng quan sát | Ghi nhận lỗi, độ trễ và số lần gọi AI | Không ghi token, mật khẩu hoặc PII thô vào log |

Các chỉ tiêu định lượng như độ trễ tối đa hoặc số người dùng đồng thời chỉ nên được xác nhận sau khi chạy đo trong môi trường xác định. Báo cáo không mặc định hệ thống đáp ứng một ngưỡng tải nếu chưa có kịch bản kiểm thử và kết quả đo.

### 1.2.4. Đặc tả một số use case quan trọng

#### Use case UC-01: Đăng ký tham gia hoạt động

| Thuộc tính | Nội dung |
|---|---|
| Tác nhân chính | Thành viên đã đăng nhập |
| Tiền điều kiện | Tài khoản hợp lệ; hoạt động tồn tại; thành viên chưa đăng ký |
| Luồng chính | 1) Thành viên mở chi tiết hoạt động. 2) Chọn đăng ký. 3) Backend xác thực vai trò và trạng thái hoạt động. 4) Backend kiểm tra đăng ký trùng và sức chứa nếu được cấu hình. 5) Lưu đăng ký. 6) Trả kết quả và số lượng đăng ký hiện tại. |
| Luồng ngoại lệ | Hoạt động không tồn tại: trả 404. Đã kết thúc: từ chối đăng ký. Đăng ký trùng: trả lỗi nghiệp vụ. Hết chỗ: từ chối hoặc đưa vào danh sách chờ theo chính sách. |
| Hậu điều kiện | Một bản ghi đăng ký duy nhất được lưu cho cặp thành viên–hoạt động |
| Ràng buộc | Kiểm tra ở backend; unique constraint ở DB; xử lý giao dịch để tránh tranh chấp đồng thời |

#### Use case UC-02: Tạo hoạt động

| Thuộc tính | Nội dung |
|---|---|
| Tác nhân chính | Chủ nhiệm hoặc Trưởng ban theo phạm vi quyền |
| Tiền điều kiện | Đã đăng nhập và có quyền tạo hoạt động |
| Luồng chính | Nhập thông tin hoạt động; backend kiểm tra trường bắt buộc, thời gian và quyền; lưu bản ghi; trả chi tiết hoạt động |
| Luồng ngoại lệ | Thiếu tiêu đề, thời gian kết thúc không sau thời gian bắt đầu hoặc dữ liệu không đúng định dạng: trả lỗi có thể xử lý; không ghi bản ghi lỗi |
| Hậu điều kiện | Hoạt động tồn tại và có thể được hiển thị theo chính sách |
| Kiểm soát AI | Nếu dùng AI sinh nội dung, kết quả được xem là bản nháp; người tạo rà soát trước khi lưu hoặc phát hành |

#### Use case UC-03: Tóm tắt sau hoạt động

| Thuộc tính | Nội dung |
|---|---|
| Tác nhân chính | Chủ nhiệm hoặc Trưởng ban được cấp quyền |
| Tiền điều kiện | Hoạt động tồn tại và đã kết thúc; dữ liệu đầu vào được phép sử dụng |
| Luồng chính | Backend truy vấn ghi chú, phản hồi và số liệu; loại bỏ trường nhận dạng không cần thiết; tạo prompt; gọi AI; trả bản tóm tắt cùng số liệu nguồn |
| Luồng ngoại lệ | Hoạt động chưa kết thúc: từ chối theo chính sách. Không có phản hồi: thông báo rõ phạm vi tóm tắt chỉ dựa trên ghi chú/số liệu. AI timeout: trả lỗi dịch vụ, không giả lập thành công |
| Hậu điều kiện | Bản tóm tắt được trả cho người dùng hoặc lưu sau khi người dùng xác nhận |
| Kiểm soát | Ghi rõ đây là nội dung do AI tạo; người dùng chịu trách nhiệm rà soát trước khi dùng làm báo cáo chính thức |

### 1.2.5. Tiêu chí chấp nhận ở cấp nghiệp vụ

Một chức năng được xem là đạt yêu cầu cơ bản khi: người dùng đúng vai trò có thể hoàn thành luồng chính; người dùng sai vai trò bị từ chối tại backend; dữ liệu không hợp lệ không làm thay đổi trạng thái hệ thống; thông báo lỗi đủ cụ thể để người dùng biết cần làm gì; và các tình huống quan trọng được kiểm thử tự động hoặc có kịch bản kiểm thử lặp lại.

## 1.3. Thiết kế kiến trúc tổng thể

### 1.3.1. Lựa chọn kiến trúc

Hệ thống được thiết kế theo kiến trúc client–server. Client chịu trách nhiệm hiển thị dữ liệu, nhận thao tác và gọi API. Backend đảm nhận xác thực, phân quyền, kiểm tra quy tắc nghiệp vụ, truy vấn cơ sở dữ liệu và điều phối các yêu cầu AI. Cơ sở dữ liệu lưu dữ liệu nghiệp vụ có cấu trúc. AI Engine là dịch vụ phụ trợ, chỉ được gọi từ backend để tránh lộ khóa truy cập và để kiểm soát dữ liệu gửi đi.

Trong mã nguồn hiện tại, backend được hiện thực bằng FastAPI; các router được chia theo nhóm nghiệp vụ như xác thực, thành viên, ban, hoạt động, điểm danh, nhiệm vụ, thông báo, thống kê và AI. SQLAlchemy đảm nhận ánh xạ mô hình Python với cơ sở dữ liệu. SQLite là cấu hình mặc định. Frontend hiện tại là tệp HTML/CSS/JavaScript tĩnh do FastAPI phục vụ. Sơ đồ ReactJS dưới đây thể hiện cách phân lớp tương đương nếu frontend được tái cấu trúc bằng React; đây là phương án kiến trúc, không phải mô tả chính xác ngôn ngữ giao diện đang có.

```text
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                              │
│  Giao diện web hiện tại: HTML/CSS/JavaScript                 │
│  Phương án mở rộng: ReactJS (component, state, router)        │
│  - Đăng nhập, dashboard, thành viên, hoạt động, chatbot       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / JSON
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION                      │
│  Router → xác thực/RBAC → kiểm tra nghiệp vụ → service       │
│  - Auth / Members / Committees / Activities / Attendance     │
│  - Tasks / Notifications / Stats / AI                        │
└───────────────┬──────────────────────────────┬──────────────┘
                │ SQLAlchemy                  │ prompt/context
                ▼                             ▼
┌─────────────────────────────┐   ┌───────────────────────────┐
│       DATABASE              │   │       AI ENGINE           │
│ SQLite (mặc định hiện tại); │   │ Provider cấu hình được;    │
│ có thể thay DB phù hợp khi  │   │ nhận context tối thiểu;    │
│ triển khai mở rộng          │   │ không truy cập DB trực tiếp│
└─────────────────────────────┘   └───────────────────────────┘
```

**Nguyên tắc phân lớp:**

- **Giao diện:** trình bày dữ liệu và gửi yêu cầu; không chứa bí mật hoặc là nơi duy nhất kiểm tra quyền.
- **Router/API:** nhận request, kiểm tra đầu vào bằng schema, gọi dependency xác thực và trả response theo hợp đồng.
- **Service/nghiệp vụ:** áp dụng quy tắc và điều phối các thao tác nhiều bước; nên được tách rõ hơn khi logic lớn dần.
- **ORM/cơ sở dữ liệu:** duy trì quan hệ, khóa và tính nhất quán của dữ liệu.
- **AI service:** dựng prompt, gọi provider và xử lý kết quả; không được tự truy cập hoặc thay đổi dữ liệu nghiệp vụ.

### 1.3.2. Luồng giao tiếp Client – FastAPI – AI Engine

```text
Người dùng        Frontend          FastAPI/API       Database        AI Engine
    |                 |                  |                |                |
    | nhập câu hỏi    |                  |                |                |
    |---------------->| POST /chat       |                |                |
    |                 |----------------->| xác thực/RBAC  |                |
    |                 |                  | truy xuất dữ liệu              |
    |                 |                  |--------------->|                |
    |                 |                  |<---------------| context         |
    |                 |                  | lọc PII, dựng prompt             |
    |                 |                  |-------------------------------->|
    |                 |                  |<--------------------------------|
    |                 |                  | kiểm tra/định dạng phản hồi     |
    |                 |<-----------------| JSON                           |
    |<----------------| hiển thị câu trả lời                               |
```

Đối với thao tác CRUD thông thường, FastAPI truy vấn hoặc cập nhật dữ liệu mà không cần gọi AI. Đối với tính năng AI, backend trước tiên xây dựng ngữ cảnh từ dữ liệu mà người dùng được phép xem; sau đó mới gọi nhà cung cấp mô hình. Mô hình không được nhận thông tin đăng nhập, khóa bí mật hoặc dữ liệu hồ sơ rộng hơn câu hỏi yêu cầu. Nếu provider không sẵn sàng, API cần trả trạng thái lỗi hoặc thông báo dịch vụ tạm thời không khả dụng; không nên trả nội dung giả nhưng có hình thức như kết quả thật.

### 1.3.3. Hợp đồng API tham khảo

Các đường dẫn sau minh họa cách tổ chức API theo tài nguyên. Đường dẫn cụ thể cần căn cứ vào router thực tế và phiên bản API đang triển khai.

| Phương thức | Đường dẫn tham khảo | Mục đích | Vai trò |
|---|---|---|---|
| `GET` | `/activities` | Liệt kê hoạt động | Người dùng đã xác thực |
| `GET` | `/activities/{id}` | Xem chi tiết hoạt động | Người dùng đã xác thực |
| `POST` | `/activities` | Tạo hoạt động | Chủ nhiệm/Trưởng ban |
| `POST` | `/activities/{id}/register` | Đăng ký tham gia | Thành viên |
| `DELETE` | `/activities/{id}/register` | Hủy đăng ký | Thành viên |
| `POST` | `/ai/notifications` | Tạo bản nháp thông báo | Chủ nhiệm/Trưởng ban |
| `POST` | `/ai/summaries` | Tóm tắt hoạt động đã kết thúc | Chủ nhiệm/Trưởng ban |
| `POST` | `/chat` | Hỏi đáp theo ngữ cảnh CLB | Người dùng đã xác thực |
| `GET` | `/health` | Kiểm tra tình trạng backend | Hệ thống/giám sát |

Response API nên thống nhất kiểu dữ liệu, mã HTTP và cách mô tả lỗi. Không trả stack trace hoặc thông tin cấu hình nội bộ cho client. Các lỗi nghiệp vụ phổ biến có thể biểu diễn bằng mã trạng thái phù hợp kèm thông điệp ngắn gọn; nội dung chi tiết cho đội vận hành được ghi trong log đã loại bỏ dữ liệu nhạy cảm.

### 1.3.4. Ví dụ minh họa endpoint đăng ký hoạt động bằng FastAPI

Đoạn mã dưới đây mô tả ý tưởng kiểm tra nghiệp vụ và được rút gọn để phục vụ báo cáo. Trong ứng dụng hoàn chỉnh, các dependency như `get_db`, `is_member` và `ensure_member_profile` cần được định nghĩa tập trung; xử lý sức chứa đồng thời cần có chiến lược transaction phù hợp với loại cơ sở dữ liệu triển khai.

```python
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Activity, Registration, User
from app.security import ensure_member_profile, is_member

router = APIRouter(prefix="/activities", tags=["activities"])


@router.post("/{activity_id}/register", status_code=status.HTTP_201_CREATED)
def register_for_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_member),
):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hoạt động không tồn tại",
        )

    if activity.end_time < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hoạt động đã kết thúc, không thể đăng ký",
        )

    member = ensure_member_profile(db, current_user)
    existing = (
        db.query(Registration)
        .filter(
            Registration.activity_id == activity.id,
            Registration.member_id == member.id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bạn đã đăng ký hoạt động này",
        )

    registration = Registration(
        activity_id=activity.id,
        member_id=member.id,
    )
    db.add(registration)
    try:
        db.commit()
    except Exception:
        db.rollback()
        # Ở sản phẩm thật, cần phân loại lỗi DB và ghi log an toàn.
        raise

    db.refresh(registration)
    return {
        "id": registration.id,
        "activity_id": activity.id,
        "member_id": member.id,
        "created_at": registration.created_at,
        "message": "Đăng ký tham gia thành công",
    }
```

Đoạn mã trên thể hiện các kiểm tra cơ bản nhưng không tự giải quyết giới hạn sức chứa đồng thời. Khi có ràng buộc sức chứa, cần bổ sung trường `capacity`, xác định chính sách danh sách chờ và bảo đảm phép kiểm tra–ghi dữ liệu là nguyên tử. Ràng buộc duy nhất ở cơ sở dữ liệu vẫn cần được giữ như lớp bảo vệ cuối cùng đối với đăng ký trùng.

### 1.3.5. Minh họa giao diện ReactJS cho danh sách hoạt động

Đây là đoạn mã minh họa cho phương án frontend ReactJS. Mã nguồn hiện tại của dự án sử dụng HTML/CSS/JavaScript thuần, do đó component dưới đây không được xem là trích đoạn trực tiếp từ ứng dụng hiện tại.

```jsx
import { useEffect, useState } from "react";

export function ActivityList({ apiBaseUrl, accessToken }) {
  const [activities, setActivities] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    async function loadActivities() {
      try {
        const response = await fetch(`${apiBaseUrl}/activities`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error("Không thể tải danh sách hoạt động.");
        }

        const data = await response.json();
        setActivities(data);
      } catch (requestError) {
        if (requestError.name !== "AbortError") {
          setError(requestError.message);
        }
      } finally {
        setLoading(false);
      }
    }

    loadActivities();
    return () => controller.abort();
  }, [apiBaseUrl, accessToken]);

  if (loading) return <p>Đang tải hoạt động...</p>;
  if (error) return <p role="alert">{error}</p>;
  if (activities.length === 0) return <p>Chưa có hoạt động phù hợp.</p>;

  return (
    <ul aria-label="Danh sách hoạt động">
      {activities.map((activity) => (
        <li key={activity.id}>
          <h2>{activity.title}</h2>
          <p>{activity.description || "Chưa có mô tả."}</p>
          <p>{activity.location || "Chưa cập nhật địa điểm."}</p>
        </li>
      ))}
    </ul>
  );
}
```

Trong sản phẩm thực tế, token cần được quản lý theo chính sách bảo mật phù hợp; không nên lưu thông tin xác thực nhạy cảm tùy tiện trong nơi lưu trữ phía trình duyệt. Giao diện cần xử lý trạng thái tải, lỗi và danh sách rỗng thay vì giả định API luôn trả dữ liệu thành công.

## 1.4. Thiết kế cơ sở dữ liệu

### 1.4.1. Nguyên tắc thiết kế

Thiết kế dữ liệu ưu tiên tính nhất quán, khả năng truy vấn và khả năng mở rộng. Mỗi thực thể nghiệp vụ có khóa chính riêng; các quan hệ được biểu diễn bằng khóa ngoại. Dữ liệu lặp lại được hạn chế bằng cách tách thành bảng liên quan. Các quy tắc quan trọng được đặt ở cơ sở dữ liệu khi có thể, đồng thời được kiểm tra tại lớp nghiệp vụ để phản hồi lỗi thân thiện.

Mô hình được trình bày theo hai mức:

- **Mô hình hiện có:** các thực thể xác nhận được trong mã nguồn: `users`, `members`, `committees`, `activities`, `registrations`, `attendances`, `tasks`, `notifications`.
- **Mô hình mở rộng đề xuất:** các thực thể cần thêm nếu triển khai đầy đủ hồ sơ tuyển thành viên, khảo sát nhiều câu hỏi, quản lý quỹ và giới hạn sức chứa hoạt động.

### 1.4.2. ERD mức khái niệm

```text
                         ┌────────────────┐
                         │   COMMITTEES   │
                         │ id (PK)        │
                         │ name           │
                         │ leader_id (FK) │
                         └───────┬────────┘
                                 │ 1
                                 │
                                 │ N
┌──────────────┐ 0..1       N ┌──▼───────────┐
│    USERS     ├───────────────┤   MEMBERS    │
│ id (PK)      │  member_id    │ id (PK)      │
│ username     │               │ student_id   │
│ role         │               │ committee_id │
└──────┬───────┘               └──┬──────┬────┘
       │ created_by               │      │
       │                          │      │
       │                    1     │      │ 1
       │                 ┌────────▼─┐  ┌─▼────────────┐
       └────────────────►│ACTIVITIES│  │  ATTENDANCES │
                         │ id (PK)  │  │ activity_id  │
                         └──┬───┬───┘  │ member_id    │
                            │   │      └──────────────┘
               ┌────────────┘   └───────────────┐
               │                                 │
          ┌────▼──────────┐              ┌───────▼──────┐
          │ REGISTRATIONS │              │    TASKS     │
          │ activity_id   │              │ activity_id  │
          │ member_id     │              │ assignee_id  │
          └───────────────┘              └──────────────┘

  NOTIFICATIONS ── có thể tham chiếu ACTIVITIES và USERS (người tạo)

  MỞ RỘNG ĐỀ XUẤT:
  APPLICATIONS (hồ sơ tuyển)     FEEDBACK_RESPONSES (khảo sát có cấu trúc)
  FINANCE_TRANSACTIONS (thu/chi)  capacity trên ACTIVITIES (giới hạn chỗ)
```

Trong ERD khái niệm, quan hệ một thành viên–một tài khoản có thể tùy chọn ở phía tài khoản để hỗ trợ các luồng đăng nhập hoặc hồ sơ chưa hoàn thiện. Quan hệ thành viên–ban là nhiều thành viên thuộc một ban tại một thời điểm trong mô hình hiện tại; nếu cần lưu lịch sử chuyển ban, nên thay bằng bảng liên kết có thời gian hiệu lực. Quan hệ giữa thành viên và hoạt động là nhiều–nhiều, được tách qua bảng đăng ký; dữ liệu điểm danh được lưu riêng vì có trạng thái và thông tin xác minh.

### 1.4.3. Đặc tả bảng dữ liệu chính

#### Bảng `users` – Tài khoản

| Cột | Kiểu dữ liệu tham khảo | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| `id` | Integer | PK, tự tăng | Định danh tài khoản |
| `username` | String | NOT NULL, UNIQUE, INDEX | Tên đăng nhập |
| `password_hash` | String | NOT NULL | Mật khẩu đã băm; không lưu mật khẩu dạng rõ |
| `role` | String | NOT NULL, mặc định `thanh_vien` | Vai trò nghiệp vụ |
| `member_id` | Integer | FK → `members.id`, có thể NULL | Hồ sơ thành viên liên kết |
| `email` | String | Có thể NULL | Email phục vụ tài khoản |
| `full_name` | String | Có thể NULL | Tên hiển thị ở tài khoản |
| `auth_provider` | String | NOT NULL, mặc định `local` | Nguồn xác thực |
| `provider_user_id` | String | Có thể NULL | Mã định danh từ nhà cung cấp OAuth |

Không nhận vai trò quản trị từ biểu mẫu đăng ký công khai. Backend gán vai trò mặc định; việc nâng quyền phải được thực hiện qua quy trình quản trị có xác thực.

#### Bảng `members` – Hồ sơ thành viên

| Cột | Kiểu dữ liệu tham khảo | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| `id` | Integer | PK | Định danh hồ sơ |
| `full_name` | String | NOT NULL | Họ tên |
| `student_id` | String | NOT NULL, UNIQUE, INDEX | Mã sinh viên |
| `email` | String | NOT NULL, UNIQUE, INDEX | Email liên hệ |
| `phone` | String | Có thể NULL | Số điện thoại |
| `date_of_birth` | Date | Có thể NULL | Ngày sinh, chỉ thu khi có mục đích |
| `gender` | String | Có thể NULL | Thông tin tự khai theo biểu mẫu |
| `class_name` | String | Có thể NULL | Lớp |
| `department` | String | Có thể NULL | Khoa |
| `committee_id` | Integer | FK → `committees.id`, có thể NULL | Ban chuyên môn |
| `skills` | Text | Mặc định rỗng | Kỹ năng phục vụ gợi ý hoạt động |
| `free_time` | Text | Mặc định rỗng | Lịch rảnh do thành viên khai báo |
| `joined_date` | DateTime | Có giá trị mặc định | Thời điểm tham gia |
| `is_active` | Boolean | Mặc định `true` | Trạng thái hoạt động |

Các trường hồ sơ nhạy cảm cần được giới hạn hiển thị theo vai trò. Kỹ năng và lịch rảnh chỉ nên được đưa vào dịch vụ AI khi tính năng gợi ý cần sử dụng và cần tránh gửi kèm định danh trực tiếp nếu không có lý do.

#### Bảng `committees` – Ban chuyên môn

| Cột | Kiểu dữ liệu tham khảo | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| `id` | Integer | PK | Định danh ban |
| `name` | String | NOT NULL, UNIQUE | Tên ban |
| `description` | Text | Mặc định rỗng | Mô tả nhiệm vụ |
| `leader_id` | Integer | FK → `members.id`, có thể NULL | Thành viên giữ vai trò trưởng ban |

Nếu một người có thể lãnh đạo nhiều ban hoặc cần lưu lịch sử lãnh đạo theo nhiệm kỳ, nên thay trường `leader_id` bằng bảng phân công vai trò có ngày bắt đầu/kết thúc.

#### Bảng `activities` – Hoạt động

| Cột | Kiểu dữ liệu tham khảo | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| `id` | Integer | PK | Định danh hoạt động |
| `title` | String | NOT NULL | Tiêu đề |
| `description` | Text | Mặc định rỗng | Nội dung giới thiệu |
| `location` | String | Mặc định rỗng | Địa điểm |
| `start_time` | DateTime | NOT NULL | Thời gian bắt đầu |
| `end_time` | DateTime | NOT NULL | Thời gian kết thúc; phải sau thời gian bắt đầu |
| `notes` | Text | Mặc định rỗng | Ghi chú phục vụ tổng kết |
| `created_by` | Integer | FK → `users.id`, có thể NULL | Người tạo |
| `created_at` | DateTime | Mặc định thời điểm tạo | Thời điểm ghi nhận |
| `capacity` | Integer | Chưa có trong mô hình hiện tại | Sức chứa đề xuất nếu cần giới hạn đăng ký |
| `status` | String/Enum | Chưa có trong mô hình hiện tại | Trạng thái đề xuất như nháp/đang mở/đã kết thúc/hủy |

`capacity` và `status` là các trường mở rộng, không nên mô tả như đã có trong phiên bản hiện tại. Khi bổ sung trạng thái, cần xác định rõ sự khác biệt giữa trạng thái lưu trữ, khả năng đăng ký và thời điểm thực tế của hoạt động.

#### Bảng `registrations` – Đăng ký hoạt động

| Cột | Kiểu dữ liệu tham khảo | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| `id` | Integer | PK | Định danh đăng ký |
| `activity_id` | Integer | FK → `activities.id`, NOT NULL | Hoạt động được đăng ký |
| `member_id` | Integer | FK → `members.id`, NOT NULL | Thành viên đăng ký |
| `created_at` | DateTime | Mặc định thời điểm tạo | Thời điểm đăng ký |
|  |  | UNIQUE (`activity_id`, `member_id`) | Chặn đăng ký trùng |

Nếu cho phép hủy rồi đăng ký lại, cần quyết định xóa bản ghi cũ hay lưu trạng thái `cancelled`; lưu lịch sử thường có lợi cho thống kê nhưng cần điều chỉnh cách tính số người đăng ký hiện tại.

#### Bảng `attendances` – Điểm danh và phản hồi gắn với lần tham dự

| Cột | Kiểu dữ liệu tham khảo | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| `id` | Integer | PK | Định danh bản ghi |
| `activity_id` | Integer | FK → `activities.id`, NOT NULL | Hoạt động |
| `member_id` | Integer | FK → `members.id`, NOT NULL | Thành viên |
| `status` | String/Enum | Mặc định theo luồng điểm danh | Trạng thái điểm danh/xác minh |
| `feedback` | Text | Mặc định rỗng | Phản hồi gắn với lần tham dự |
| `checked_at` | DateTime | Mặc định thời điểm tạo | Thời điểm tạo bản ghi |
| `checked_in_at` | DateTime | Có thể NULL | Thời điểm check-in |
| `proof_image_url` | String | Có thể NULL | Đường dẫn minh chứng |
| `verified_by` | Integer | FK → `users.id`, có thể NULL | Người xác minh |
| `verified_at` | DateTime | Có thể NULL | Thời điểm xác minh |
| `reject_reason` | Text | Mặc định rỗng | Lý do từ chối minh chứng |

Để bảo đảm một người không có nhiều bản ghi điểm danh bất thường cho cùng hoạt động, cần xem xét unique constraint `(activity_id, member_id)` nếu nghiệp vụ xác nhận mỗi người chỉ có một trạng thái cuối cùng. Nếu cần nhiều lần check-in hoặc nhiều lần cập nhật, nên tách bảng nhật ký sự kiện thay vì tạo nhiều bản ghi điểm danh không phân biệt.

#### Bảng `tasks` – Nhiệm vụ

| Cột | Kiểu dữ liệu tham khảo | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| `id` | Integer | PK | Định danh nhiệm vụ |
| `title` | String | NOT NULL | Tên nhiệm vụ |
| `description` | Text | Mặc định rỗng | Mô tả |
| `activity_id` | Integer | FK → `activities.id`, có thể NULL | Hoạt động liên quan |
| `assignee_id` | Integer | FK → `members.id`, có thể NULL | Người được giao |
| `status` | String/Enum | Mặc định `todo` | `todo`, `in_progress`, `done` |
| `priority` | String/Enum | Mặc định `medium` | Mức ưu tiên |
| `due_date` | DateTime | Có thể NULL | Hạn hoàn thành |
| `created_at` | DateTime | Mặc định thời điểm tạo | Thời điểm tạo nhiệm vụ |

#### Bảng `notifications` – Thông báo

| Cột | Kiểu dữ liệu tham khảo | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| `id` | Integer | PK | Định danh thông báo |
| `title` | String | NOT NULL | Tiêu đề |
| `content` | Text | NOT NULL | Nội dung |
| `activity_id` | Integer | FK → `activities.id`, có thể NULL | Hoạt động liên quan |
| `created_by` | Integer | FK → `users.id`, có thể NULL | Người tạo |
| `created_at` | DateTime | Mặc định thời điểm tạo | Thời điểm tạo |
| `is_ai_generated` | Boolean | Mặc định `false` | Đánh dấu nội dung có AI hỗ trợ |

`is_ai_generated` không thay cho lịch sử kiểm duyệt. Nếu yêu cầu truy vết nội dung, cần lưu thêm trạng thái bản nháp/đã duyệt/đã phát hành, người duyệt, thời điểm duyệt và phiên bản nội dung.

### 1.4.4. Các bảng mở rộng đề xuất

| Bảng | Cột tiêu biểu | Mục đích |
|---|---|---|
| `applications` | `id`, `member_id` hoặc thông tin ứng viên, `status`, `submitted_at`, `reviewed_by`, `reviewed_at`, `decision_note` | Quản lý quy trình tuyển thành viên nhiều bước |
| `feedback_forms` | `id`, `activity_id`, `title`, `is_anonymous`, `open_at`, `close_at` | Quản lý biểu mẫu khảo sát |
| `feedback_questions` | `id`, `form_id`, `question_text`, `question_type`, `required`, `sort_order` | Lưu câu hỏi có cấu trúc |
| `feedback_responses` | `id`, `form_id`, `member_id` có thể NULL, `submitted_at` | Lưu một lần gửi khảo sát |
| `feedback_answers` | `id`, `response_id`, `question_id`, `answer_text` hoặc giá trị chuẩn hóa | Lưu câu trả lời |
| `finance_transactions` | `id`, `type`, `amount`, `category`, `description`, `occurred_at`, `created_by`, `proof_url`, `status` | Theo dõi thu/chi và chứng từ |
| `audit_logs` | `id`, `actor_id`, `action`, `entity_type`, `entity_id`, `created_at`, metadata đã lọc | Truy vết thao tác quan trọng |
| `event_waitlist` | `id`, `activity_id`, `member_id`, `position`, `created_at` | Quản lý danh sách chờ khi hết sức chứa |

Các bảng đề xuất cần được đánh giá theo yêu cầu thực tế và chính sách của CLB. Đặc biệt, thông tin tài chính, minh chứng điểm danh và câu trả lời khảo sát có thể nhạy cảm; quyền truy cập và thời hạn lưu trữ phải được quy định trước khi đưa vào sản phẩm.

### 1.4.5. Quan hệ và ràng buộc toàn vẹn

| Quan hệ | Bội số | Ràng buộc/ghi chú |
|---|---|---|
| `committees` – `members` | Một ban có nhiều thành viên; thành viên thuộc tối đa một ban theo mô hình hiện tại | `members.committee_id` là khóa ngoại nullable |
| `members` – `users` | Một hồ sơ thành viên gắn với tối đa một tài khoản; tài khoản có thể chưa liên kết hồ sơ | Cần bảo đảm một-một nếu nghiệp vụ yêu cầu bằng unique constraint trên `users.member_id` |
| `activities` – `registrations` | Một hoạt động có nhiều đăng ký | Xóa hoạt động cần chính sách cascade/xóa mềm rõ ràng |
| `members` – `registrations` | Một thành viên có nhiều đăng ký | UNIQUE cặp hoạt động–thành viên |
| `activities` – `attendances` | Một hoạt động có nhiều bản ghi điểm danh | Xác minh trạng thái và người xác minh |
| `members` – `attendances` | Một thành viên có nhiều bản ghi điểm danh | Có thể cần UNIQUE cặp thành viên–hoạt động |
| `activities` – `tasks` | Một hoạt động có nhiều nhiệm vụ; nhiệm vụ có thể không gắn sự kiện | `activity_id` nullable |
| `members` – `tasks` | Một thành viên có thể nhận nhiều nhiệm vụ | `assignee_id` nullable |
| `activities` – `notifications` | Một hoạt động có thể có nhiều thông báo | Cho phép thông báo chung không gắn hoạt động |

### 1.4.6. Mẫu khai báo constraint với SQLAlchemy

```python
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (
        UniqueConstraint(
            "activity_id",
            "member_id",
            name="uq_registration_activity_member",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(
        Integer,
        ForeignKey("activities.id"),
        nullable=False,
    )
    member_id = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=False,
    )
    created_at = Column(DateTime, nullable=False)

    activity = relationship("Activity", back_populates="registrations")
    member = relationship("Member", back_populates="registrations")
```

Đây là minh họa về ràng buộc đăng ký trùng tương ứng với mô hình hiện có. Giá trị thời gian mặc định và xử lý múi giờ cần được thống nhất ở cấp ứng dụng; dữ liệu nên được lưu theo một quy ước rõ ràng, sau đó định dạng theo múi giờ địa phương khi hiển thị.

### 1.4.7. Mô hình dữ liệu, phản hồi và AI

Đầu vào cho AI cần được tạo từ những trường có liên quan trực tiếp đến tác vụ. Ví dụ, chatbot hỏi lịch hoạt động cần tên, mô tả, địa điểm, thời gian và trạng thái đăng ký; không cần mã sinh viên, email, số điện thoại hoặc ngày sinh. Tóm tắt khảo sát thường cần phản hồi đã được loại định danh và số liệu tổng hợp, không cần tên người trả lời.

Một cấu trúc context tối giản có thể như sau:

```json
{
  "current_time": "2026-10-31 00:00",
  "available_events": [
    {
      "id": 18,
      "title": "Workshop kỹ năng tổ chức sự kiện",
      "start_time": "2026-11-05 13:30",
      "end_time": "2026-11-05 16:30",
      "location": "Phòng sinh hoạt chung",
      "description": "Thực hành xây dựng kế hoạch và phân công nhân sự."
    }
  ],
  "club_rules": [
    "Thành viên đăng ký hoạt động qua hệ thống."
  ]
}
```

Đối với chatbot tư vấn, danh sách `available_events` phải được lấy từ truy vấn thực tế theo quyền người dùng và tiêu chí thời gian. Nếu danh sách rỗng hoặc câu hỏi không khớp dữ liệu, phản hồi nên nói rõ chưa tìm thấy thông tin và hướng người dùng liên hệ ban chủ nhiệm. Không nên yêu cầu mô hình tự tạo hoạt động thay thế.

### 1.4.8. Sao lưu, xóa và lưu trữ dữ liệu

Dữ liệu thành viên, điểm danh, minh chứng và giao dịch tài chính cần có quy tắc lưu trữ. Khi một thành viên ngừng hoạt động, có thể đánh dấu `is_active = false` thay vì xóa vật lý để bảo toàn lịch sử hoạt động; tuy nhiên, các trường nhận dạng cá nhân vẫn cần được xử lý theo chính sách lưu giữ. Khi xóa một hoạt động, cần xác định dữ liệu liên quan được lưu, xóa theo cascade hay chuyển trạng thái hủy. Thao tác quản trị quan trọng nên được ghi lại để có thể giải trình.

Với SQLite trong môi trường phát triển, cần sao lưu tệp DB theo quy trình nhất quán và tránh sao chép khi đang có giao dịch chưa hoàn tất. Trong triển khai nhiều người dùng hoặc cần tính sẵn sàng cao hơn, nên đánh giá DB máy chủ, cơ chế migration có quản lý phiên bản và quy trình backup/restore đã được kiểm thử.

## 1.5. Kết luận chương

Chương này đã xác định bài toán quản lý CLB sinh viên là bài toán liên kết nhiều quy trình và nhóm dữ liệu, không chỉ là tập hợp biểu mẫu CRUD độc lập. Các quy trình trọng tâm gồm tiếp nhận và phân công thành viên, tổ chức hoạt động, đăng ký, điểm danh, giao nhiệm vụ, thu thập phản hồi và chăm sóc thành viên. Từ đó, chương đã xây dựng nhóm yêu cầu chức năng, yêu cầu phi chức năng, quy tắc nghiệp vụ và các use case cốt lõi.

Giải pháp được tổ chức theo kiến trúc client–server, trong đó FastAPI là lớp điều phối nghiệp vụ, cơ sở dữ liệu là nguồn dữ liệu chuẩn và AI Engine chỉ đóng vai trò hỗ trợ có kiểm soát. Thiết kế cơ sở dữ liệu phân biệt các thực thể đang có trong mã nguồn với các thực thể mở rộng cần bổ sung để quản lý tuyển thành viên nhiều vòng, khảo sát có cấu trúc, quỹ CLB và sức chứa sự kiện. Sự phân biệt này là cơ sở để các chương sau đánh giá sản phẩm trung thực, lập kế hoạch hoàn thiện và xác định giới hạn của phiên bản hiện tại.

---

**Ghi chú hoàn thiện trước khi nộp:** Bổ sung tên trường, học phần, giảng viên, năm học; đối chiếu các mô tả “hiện có” với phiên bản mã nguồn cuối cùng; bổ sung hình chụp giao diện, sơ đồ ERD dạng ảnh và số liệu kiểm thử thực tế nếu nhóm đã thực hiện.