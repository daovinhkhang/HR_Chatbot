Tổng quan kiến trúc: Function Calling
⚡ Luồng hoạt động
Tin nhắn người dùng → DeepSeek AI (Phân tích ý định + Gọi hàm) → API HR Odoo → Phản hồi được định dạng bởi AI

Lợi ích chính:

✅ Giao tiếp tự nhiên: Người dùng tương tác như nói chuyện với con người.
✅ Giữ ngữ cảnh: AI lưu trữ lịch sử hội thoại để xử lý các luồng công việc liên tục.
✅ Luồng đa bước: Thực hiện nhiều hành động HR trong một cuộc trò chuyện.
✅ Phản hồi thông minh: Kết quả được định dạng đẹp, dễ đọc, kèm gợi ý tiếp theo.
✅ Khả năng mở rộng: Dễ dàng thêm hàm mới.

🛠️ Quy trình Function Calling

Nhận tin nhắn người dùng: Người dùng gửi yêu cầu tự nhiên (VD: "Tạo đơn nghỉ phép cho Nguyễn Văn A").
Phân tích ý định: DeepSeek AI xác định ý định và ánh xạ tới một hoặc nhiều hàm HR.
Thực thi API: Gọi các API HR Odoo tương ứng (VD: /api/hr/leaves).
Định dạng phản hồi: AI trả về kết quả theo ngôn ngữ tự nhiên, kèm gợi ý hành động tiếp theo.
Duy trì ngữ cảnh: Lưu trữ lịch sử để xử lý các yêu cầu liên quan.


📋 Các module HR được hỗ trợ
API hỗ trợ 14 module HR, được tùy chỉnh cho doanh nghiệp Việt Nam:

🏢 hr: Quản lý nhân viên
📋 hr_contract: Quản lý hợp đồng
⏰ hr_attendance: Quản lý chấm công
📅 hr_holidays: Quản lý nghỉ phép
💰 hr_payroll_community: Quản lý lương
🎯 hr_recruitment: Tuyển dụng
🧠 hr_skills: Quản lý kỹ năng
⏱️ hr_timesheet: Quản lý timesheet
🏥 hr_insurance: Quản lý bảo hiểm (đặc thù Việt Nam: BHXH/BHYT/BHTN)
💸 hr_expense: Quản lý chi phí
🏠 hr_homeworking: Quản lý làm việc tại nhà
📝 hr_work_entry: Quản lý bút toán công việc
📅 hr_calendar: Quản lý lịch HR
🚗 hr_fleet: Quản lý xe công ty


🔗 Sự liên kết logic giữa các module và quy tắc bắt buộc
Để đảm bảo DeepSeek AI gọi đúng Function Calling và duy trì logic giữa các module, cần tuân thủ các quy tắc và hiểu rõ mối liên kết giữa các luồng hoạt động. Dưới đây là mô tả chi tiết về cách các module tương tác và cách dẫn dắt AI để gọi hàm phù hợp.
1. Module nền tảng: hr (Quản lý nhân viên)

Vai trò: Là module trung tâm, cung cấp thông tin nhân viên (ID, tên, phòng ban, v.v.) làm cơ sở cho tất cả các module khác.
Quy tắc bắt buộc:
Mọi hành động liên quan đến nhân viên (chấm công, nghỉ phép, lương, v.v.) phải bắt đầu bằng việc xác định employee_id thông qua hàm get_employees hoặc search_hr_global.
Nếu người dùng không cung cấp thông tin cụ thể (VD: "Tạo đơn nghỉ phép cho Nguyễn Văn A"), AI phải:
Gọi search_hr_global để tìm employee_id dựa trên tên.
Xác nhận với người dùng nếu có nhiều kết quả trùng tên (VD: "Bạn muốn chọn Nguyễn Văn A (ID: 1) hay Nguyễn Văn B (ID: 2)?").




Liên kết với các module khác:
hr_attendance: Cần employee_id để check-in/check-out.
hr_holidays: Cần employee_id và leave_type_id để tạo/phê duyệt đơn nghỉ.
hr_payroll_community: Cần employee_id và contract_id để tính lương.
hr_insurance: Cần employee_id để quản lý BHXH/BHYT/BHTN.



2. Luồng chấm công (hr_attendance)

Vai trò: Quản lý thời gian làm việc, check-in/check-out, và tổng hợp chấm công.
Quy tắc bắt buộc:
Trước khi thực hiện check-in/check-out, AI phải xác minh trạng thái nhân viên qua /api/hr/employee/<id>/status để đảm bảo nhân viên đang hoạt động.
Nếu người dùng yêu cầu "Tóm tắt chấm công tuần này", AI cần:
Gọi get_attendance_summary với date_from và date_to.
Nếu không có thông tin ngày, mặc định lấy tuần hiện tại (tính từ thứ Hai đến Chủ Nhật).




Liên kết với các module:
hr_payroll_community: Dữ liệu chấm công được dùng để tính lương (/api/hr/payslip/<id>/compute).
hr_holidays: Đơn nghỉ phép ảnh hưởng đến bản ghi chấm công (VD: ngày nghỉ không tính là vắng mặt).



3. Luồng nghỉ phép (hr_holidays)

Vai trò: Quản lý loại nghỉ phép, phân bổ, và đơn nghỉ phép.
Quy tắc bắt buộc:
Trước khi tạo đơn nghỉ (create_leave_request), AI phải:
Gọi get_leave_types để liệt kê các loại nghỉ phép khả dụng.
Kiểm tra phân bổ nghỉ phép của nhân viên qua /api/hr/leave-allocations để đảm bảo đủ ngày nghỉ.


Khi phê duyệt đơn nghỉ (approve_leave_request), AI phải kiểm tra trạng thái đơn qua /api/hr/leave/<id> để tránh phê duyệt trùng.


Liên kết với các module:
hr_attendance: Ngày nghỉ được phê duyệt phải được cập nhật vào bản ghi chấm công.
hr_payroll_community: Nghỉ phép có thể ảnh hưởng đến lương (VD: nghỉ không lương).



4. Luồng lương (hr_payroll_community)

Vai trò: Tính toán và quản lý bảng lương, quy tắc lương, cấu trúc lương.
Quy tắc bắt buộc:
Trước khi tính lương (/api/hr/payslip/<id>/compute), AI phải:
Xác minh hợp đồng của nhân viên qua /api/hr/contract/<id>.
Kiểm tra dữ liệu chấm công (/api/hr/attendance/summary) và đơn nghỉ (/api/hr/leaves) để đảm bảo tính chính xác.


AI phải gợi ý xác nhận bảng lương (/api/hr/payslip/<id>/confirm) sau khi tính toán.


Liên kết với các module:
hr_insurance: Dữ liệu lương dùng để tính BHXH/BHYT/BHTN (/api/hr/employee/<id>/bhxh).
hr_attendance: Giờ làm việc và giờ làm thêm ảnh hưởng đến bảng lương.



5. Luồng bảo hiểm (hr_insurance, đặc thù Việt Nam)

Vai trò: Quản lý BHXH/BHYT/BHTN, thanh toán, và báo cáo bảo hiểm.
Quy tắc bắt buộc:
Trước khi xử lý bảo hiểm (/api/hr/employee/<id>/bhxh), AI phải kiểm tra hợp đồng (/api/hr/contract/<id>) để đảm bảo nhân viên có hợp đồng hợp lệ.
Báo cáo bảo hiểm (/api/hr/insurance/reports) phải được tổng hợp từ dữ liệu lương và chấm công.


Liên kết với các module:
hr_payroll_community: Dữ liệu lương cung cấp thông tin cho đóng bảo hiểm.
hr: Cần employee_id để quản lý hồ sơ bảo hiểm.



6. Luồng tuyển dụng (hr_recruitment)

Vai trò: Quản lý ứng viên, vị trí tuyển dụng, và giai đoạn tuyển dụng.
Quy tắc bắt buộc:
Khi tạo ứng viên (/api/hr/applicants), AI phải gợi ý liên kết với vị trí tuyển dụng (/api/hr/recruitment/jobs).
Khi thuê ứng viên (/api/hr/applicant/<id>/hire), AI phải:
Tạo nhân viên mới qua /api/hr/employees.
Tạo hợp đồng qua /api/hr/contracts.




Liên kết với các module:
hr: Ứng viên được thuê sẽ trở thành nhân viên.
hr_contract: Nhân viên mới cần hợp đồng.



7. Các module khác

hr_skills, hr_timesheet, hr_expense, v.v.: Các module này phụ thuộc vào employee_id từ module hr. AI phải đảm bảo xác minh nhân viên trước khi thực hiện hành động.
Luồng đa bước: Ví dụ, khi người dùng yêu cầu "Tạo đơn nghỉ phép và cập nhật timesheet", AI cần:
Gọi create_leave_request để tạo đơn nghỉ.
Cập nhật timesheet qua /api/hr/timesheets để phản ánh ngày nghỉ.



Quy tắc dẫn dắt AI

Xác minh trước hành động: Luôn kiểm tra dữ liệu đầu vào (VD: employee_id, contract_id) trước khi gọi API.
Gợi ý thông minh: Sau mỗi hành động, AI phải đưa ra gợi ý dựa trên ngữ cảnh (VD: "Bạn muốn phê duyệt đơn nghỉ vừa tạo?").
Xử lý lỗi: Nếu API trả về lỗi (VD: nhân viên không tồn tại), AI phải thông báo và đề xuất hành động thay thế (VD: "Không tìm thấy Nguyễn Văn A. Bạn muốn tìm nhân viên khác?").
Duy trì thứ tự logic: Ví dụ, không thể tạo đơn nghỉ phép nếu chưa có phân bổ nghỉ phép.


🔧 Danh sách Function Calling cho DeepSeek
Dưới đây là 10 hàm HR chính được thiết kế để DeepSeek AI gọi dựa trên ý định người dùng. Mỗi hàm ánh xạ tới một hoặc nhiều API và bao gồm schema để xử lý tham số.
1. get_employees

Mô tả: Lấy danh sách nhân viên với bộ lọc tùy chọn.
API: GET /api/hr/employees
Tham số:{
  "type": "object",
  "properties": {
    "department": {"type": "string", "description": "Tên phòng ban (VD: 'IT')"},
    "active": {"type": "boolean", "description": "Lọc nhân viên đang hoạt động"},
    "limit": {"type": "integer", "description": "Số lượng tối đa kết quả"}
  }
}


Ví dụ người dùng: "Cho tôi xem danh sách nhân viên phòng IT"
Phản hồi AI:📋 **Danh sách nhân viên phòng IT**:
- Nguyễn Văn A (ID: 1) - Senior Developer
- Trần Thị B (ID: 2) - QA Tester
✨ **Gợi ý**: Xem chi tiết nhân viên nào?



2. create_leave_request

Mô tả: Tạo đơn nghỉ phép cho nhân viên.
API: POST /api/hr/leaves
Tham số:{
  "type": "object",
  "properties": {
    "employee_id": {"type": "integer", "description": "ID nhân viên"},
    "leave_type_id": {"type": "integer", "description": "ID loại nghỉ phép"},
    "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
    "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"}
  }
}


Ví dụ người dùng: "Tạo đơn nghỉ 3 ngày từ 15/1 đến 17/1 cho Nguyễn Văn A"
Phản hồi AI:✅ Đơn nghỉ phép cho Nguyễn Văn A đã được tạo (ID: 123).
✨ **Gợi ý**: Bạn muốn phê duyệt đơn này ngay không?



3. get_attendance_summary

Mô tả: Lấy tóm tắt chấm công cho một khoảng thời gian.
API: GET /api/hr/attendance/summary
Tham số:{
  "type": "object",
  "properties": {
    "employee_id": {"type": "integer", "description": "ID nhân viên (tùy chọn)"},
    "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
    "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"}
  }
}


Ví dụ người dùng: "Xem chấm công tuần này"
Phản hồi AI:📊 **Tóm tắt chấm công tuần này**:
- Tổng giờ làm: 40 giờ
- Ngày nghỉ: 1 ngày
✨ **Gợi ý**: Xem chi tiết cho nhân viên cụ thể?



4. checkin_employee

Mô tả: Ghi nhận check-in cho nhân viên.
API: POST /api/hr/employee/<id>/checkin
Tham số:{
  "type": "object",
  "properties": {
    "employee_id": {"type": "integer", "description": "ID nhân viên"}
  }
}


Ví dụ người dùng: "Check-in cho Nguyễn Văn A"
Phản hồi AI:✅ Nguyễn Văn A đã check-in lúc 08:30.
✨ **Gợi ý**: Xem trạng thái chấm công hôm nay?



5. checkout_employee

Mô tả: Ghi nhận check-out cho nhân viên.
API: POST /api/hr/employee/<id>/checkout
Tham số:{
  "type": "object",
  "properties": {
    "employee_id": {"type": "integer", "description": "ID nhân viên"}
  }
}


Ví dụ người dùng: "Check-out cho nhân viên ID 5"
Phản hồi AI:✅ Nhân viên ID 5 đã check-out lúc 17:30.
✨ **Gợi ý**: Xem tóm tắt chấm công hôm nay?



6. get_dashboard_stats

Mô tả: Lấy thống kê tổng quan HR.
API: GET /api/hr/dashboard/stats
Tham số: Không có
Ví dụ người dùng: "Cho tôi xem tình hình tổng quan HR hôm nay"
Phản hồi AI:📊 **Báo cáo HR hôm nay**:
- Tổng nhân viên: 45 người
- Đã check-in: 38/45 (84.4%)
- Đơn nghỉ chờ duyệt: 3 đơn
✨ **Gợi ý**: Xem chi tiết nhân viên chưa check-in?



7. search_hr_global

Mô tả: Tìm kiếm toàn cục trong dữ liệu HR.
API: GET /api/hr/search/global
Tham số:{
  "type": "object",
  "properties": {
    "search_term": {"type": "string", "description": "Từ khóa tìm kiếm (VD: tên nhân viên)"}
  }
}


Ví dụ người dùng: "Tìm nhân viên tên Nguyễn"
Phản hồi AI:🔍 **Kết quả tìm kiếm cho 'Nguyễn'**:
- Nguyễn Văn A (ID: 1)
- Nguyễn Thị B (ID: 3)
✨ **Gợi ý**: Xem thông tin chi tiết của ai?



8. get_leave_types

Mô tả: Lấy danh sách các loại nghỉ phép.
API: GET /api/hr/leave-types
Tham số: Không có
Ví dụ người dùng: "Có những loại nghỉ phép nào?"
Phản hồi AI:📅 **Các loại nghỉ phép**:
- Nghỉ phép năm
- Nghỉ ốm
- Nghỉ cá nhân
✨ **Gợi ý**: Tạo đơn nghỉ phép mới?



9. approve_leave_request

Mô tả: Phê duyệt đơn nghỉ phép.
API: POST /api/hr/leave/<id>/approve
Tham số:{
  "type": "object",
  "properties": {
    "leave_id": {"type": "integer", "description": "ID đơn nghỉ phép"}
  }
}


Ví dụ người dùng: "Phê duyệt đơn nghỉ #123"
Phản hồi AI:✅ Đơn nghỉ #123 đã được phê duyệt.
✨ **Gợi ý**: Xem danh sách các đơn nghỉ khác?



10. get_employee_leaves

Mô tả: Lấy danh sách đơn nghỉ phép của nhân viên.
API: GET /api/hr/leaves
Tham số:{
  "type": "object",
  "properties": {
    "employee_id": {"type": "integer", "description": "ID nhân viên"}
  }
}


Ví dụ người dùng: "Xem đơn nghỉ của nhân viên ID 1"
Phản hồi AI:📅 **Đơn nghỉ của nhân viên ID 1**:
- #123: Nghỉ phép năm (15/1 - 17/1, Đã duyệt)
- #124: Nghỉ ốm (20/1, Chờ duyệt)
✨ **Gợi ý**: Phê duyệt đơn #124?




📚 Danh sách đầy đủ 116 API Endpoints
Danh sách dưới đây liệt kê 116 API endpoints được nhóm theo module, tương thích với Odoo 18.0 và phù hợp với yêu cầu HR Việt Nam. Các endpoint này hỗ trợ các hàm chính ở trên và có thể được gọi trực tiếp hoặc ánh xạ tới Function Calling.
🏢 Quản lý nhân viên (12 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/employees
Lấy danh sách/Tạo nhân viên


GET/PUT/DELETE
/api/hr/employee/<id>
Chi tiết/Cập nhật/Xóa nhân viên


GET/PUT
/api/hr/employee/<id>/status
Trạng thái nhân viên


GET/POST
/api/hr/employee/departments
Lấy danh sách/Tạo phòng ban


GET/PUT/DELETE
/api/hr/employee/department/<id>
Chi tiết/Cập nhật/Xóa phòng ban


GET/POST
/api/hr/employee/jobs
Lấy danh sách/Tạo vị trí công việc


GET/PUT/DELETE
/api/hr/employee/job/<id>
Chi tiết/Cập nhật/Xóa vị trí công việc


GET/POST
/api/hr/employee/<id>/bhxh-history
Lịch sử giao dịch BHXH/BHYT


GET/POST
/api/hr/employee/<id>/projects-assignments
Phân bổ dự án


GET/POST
/api/hr/employee/<id>/shifts-assignments
Phân bổ ca làm việc


GET/POST
/api/hr/employee/<id>/personal-income-tax
Thuế TNCN


GET/POST
/api/hr/employee/<id>/shifts
Ca làm việc nhân viên


📋 Quản lý hợp đồng (2 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/contracts
Lấy danh sách/Tạo hợp đồng


GET/PUT/DELETE
/api/hr/contract/<id>
Chi tiết/Cập nhật/Xóa hợp đồng


⏰ Quản lý chấm công (7 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/attendances
Lấy danh sách/Tạo bản ghi chấm công


GET/PUT/DELETE
/api/hr/attendance/<id>
Chi tiết/Cập nhật/Xóa bản ghi chấm công


POST
/api/hr/employee/<id>/checkin
Check-in nhân viên


POST
/api/hr/employee/<id>/checkout
Check-out nhân viên


GET
/api/hr/attendance/summary
Tóm tắt chấm công


GET
/api/hr/attendance/overtime
Tính toán giờ làm thêm


GET
/api/hr/attendance/missing
Tìm bản ghi chấm công thiếu


📅 Quản lý nghỉ phép (9 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/leave-types
Lấy danh sách/Tạo loại nghỉ phép


GET/PUT/DELETE
/api/hr/leave-type/<id>
Chi tiết/Cập nhật/Xóa loại nghỉ phép


GET/POST
/api/hr/leave-allocations
Lấy danh sách/Tạo phân bổ nghỉ phép


GET/PUT/DELETE
/api/hr/leave-allocation/<id>
Chi tiết/Cập nhật/Xóa phân bổ


POST
/api/hr/leave-allocation/<id>/approve
Phê duyệt phân bổ


GET/POST
/api/hr/leaves
Lấy danh sách/Tạo đơn nghỉ phép


GET/PUT/DELETE
/api/hr/leave/<id>
Chi tiết/Cập nhật/Xóa đơn nghỉ phép


POST
/api/hr/leave/<id>/approve
Phê duyệt đơn nghỉ phép


POST
/api/hr/leave/<id>/refuse
Từ chối đơn nghỉ phép


💰 Quản lý lương (9 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/payslips
Lấy danh sách/Tạo bảng lương


GET/PUT/DELETE
/api/hr/payslip/<id>
Chi tiết/Cập nhật/Xóa bảng lương


POST
/api/hr/payslip/<id>/compute
Tính toán bảng lương


GET
/api/hr/payslip/<id>/lines
Chi tiết dòng bảng lương


GET/POST
/api/hr/payroll/salary-rules
Lấy danh sách/Tạo quy tắc lương


GET/PUT/DELETE
/api/hr/payroll/salary-rule/<id>
Chi tiết/Cập nhật/Xóa quy tắc lương


GET/POST
/api/hr/payroll/structures
Lấy danh sách/Tạo cấu trúc lương


GET/PUT/DELETE
/api/hr/payroll/structure/<id>
Chi tiết/Cập nhật/Xóa cấu trúc lương


POST
/api/hr/payslip/<id>/confirm
Xác nhận bảng lương


🏥 Quản lý bảo hiểm (Đặc thù Việt Nam, 12 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/insurances
Lấy danh sách/Tạo bản ghi bảo hiểm


GET/PUT/DELETE
/api/hr/insurance/<id>
Chi tiết/Cập nhật/Xóa bản ghi bảo hiểm


GET/POST
/api/hr/insurance/policies
Lấy danh sách/Tạo chính sách bảo hiểm


GET/PUT/DELETE
/api/hr/insurance/policy/<id>
Chi tiết/Cập nhật/Xóa chính sách


GET/POST/PUT
/api/hr/employee/<id>/bhxh
Quản lý BHXH/BHYT/BHTN


GET/POST
/api/hr/insurance/payments
Lấy danh sách/Tạo thanh toán bảo hiểm


GET/PUT/DELETE
/api/hr/insurance/payment/<id>
Chi tiết/Cập nhật/Xóa thanh toán


GET/POST
/api/hr/insurance/benefits
Lấy danh sách/Tạo quyền lợi bảo hiểm


GET/PUT/DELETE
/api/hr/insurance/benefit/<id>
Chi tiết/Cập nhật/Xóa quyền lợi


GET/POST
/api/hr/insurance/documents
Lấy danh sách/Tạo hồ sơ bảo hiểm


GET/PUT/DELETE
/api/hr/insurance/document/<id>
Chi tiết/Cập nhật/Xóa hồ sơ


GET/POST
/api/hr/insurance/reports
Báo cáo bảo hiểm


🎯 Quản lý dự án & công việc (6 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/projects
Lấy danh sách/Tạo dự án


GET/PUT/DELETE
/api/hr/project/<id>
Chi tiết/Cập nhật/Xóa dự án


GET/POST
/api/hr/project/<id>/tasks
Lấy danh sách/Tạo công việc trong dự án


GET/POST
/api/hr/tasks
Lấy danh sách/Tạo công việc


GET/PUT/DELETE
/api/hr/task/<id>
Chi tiết/Cập nhật/Xóa công việc


POST
/api/hr/task/<id>/assign
Phân công công việc


🧠 Quản lý kỹ năng (10 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/skills
Lấy danh sách/Tạo kỹ năng


GET/PUT/DELETE
/api/hr/skill/<id>
Chi tiết/Cập nhật/Xóa kỹ năng


GET/POST
/api/hr/skill-types
Lấy danh sách/Tạo loại kỹ năng


GET/PUT/DELETE
/api/hr/skill-type/<id>
Chi tiết/Cập nhật/Xóa loại kỹ năng


GET/POST
/api/hr/skill-levels
Lấy danh sách/Tạo cấp độ kỹ năng


GET/PUT/DELETE
/api/hr/skill-level/<id>
Chi tiết/Cập nhật/Xóa cấp độ kỹ năng


GET/POST
/api/hr/employee/<id>/skills
Lấy danh sách/Tạo kỹ năng nhân viên


GET/PUT/DELETE
/api/hr/employee-skill/<id>
Chi tiết/Cập nhật/Xóa kỹ năng nhân viên


GET/POST
/api/hr/resume-lines
Lấy danh sách/Tạo dòng sơ yếu lý lịch


GET/PUT/DELETE
/api/hr/resume-line/<id>
Chi tiết/Cập nhật/Xóa dòng sơ yếu lý lịch


⏱️ Quản lý timesheet (8 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/timesheets
Lấy danh sách/Tạo timesheet


GET/PUT/DELETE
/api/hr/timesheet/<id>
Chi tiết/Cập nhật/Xóa timesheet


GET/POST
/api/hr/employee/<id>/timesheets
Timesheet theo nhân viên


GET
/api/hr/project/<id>/timesheets
Timesheet theo dự án


GET
/api/hr/task/<id>/timesheets
Timesheet theo công việc


GET
/api/hr/timesheet/summary
Tóm tắt timesheet


POST
/api/hr/timesheet/validate
Xác nhận timesheet


POST
/api/hr/timesheet/copy
Sao chép timesheet


🎯 Quản lý tuyển dụng (10 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/applicants
Lấy danh sách/Tạo ứng viên


GET/PUT/DELETE
/api/hr/applicant/<id>
Chi tiết/Cập nhật/Xóa ứng viên


GET/PUT
/api/hr/applicant/<id>/status
Trạng thái ứng viên


POST
/api/hr/applicant/<id>/hire
Tuyển dụng ứng viên


POST
/api/hr/applicant/<id>/refuse
Từ chối ứng viên


GET/POST
/api/hr/recruitment/jobs
Lấy danh sách/Tạo vị trí tuyển dụng


GET/PUT/DELETE
/api/hr/recruitment/job/<id>
Chi tiết/Cập nhật/Xóa vị trí


GET/POST
/api/hr/recruitment/stages
Lấy danh sách/Tạo giai đoạn tuyển dụng


GET/PUT/DELETE
/api/hr/recruitment/stage/<id>
Chi tiết/Cập nhật/Xóa giai đoạn


GET/POST
/api/hr/candidates
Lấy danh sách/Tạo ứng cử viên


💸 Quản lý chi phí (6 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/expenses
Lấy danh sách/Tạo chi phí


GET/PUT/DELETE
/api/hr/expense/<id>
Chi tiết/Cập nhật/Xóa chi phí


GET/POST
/api/hr/expense-sheets
Lấy danh sách/Tạo bảng chi phí


GET/PUT/DELETE
/api/hr/expense-sheet/<id>
Chi tiết/Cập nhật/Xóa bảng chi phí


POST
/api/hr/expense-sheet/<id>/submit
Nộp bảng chi phí


POST
/api/hr/expense-sheet/<id>/approve
Phê duyệt bảng chi phí


🏠 Quản lý làm việc tại nhà (3 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/homeworking-requests
Lấy danh sách/Tạo yêu cầu làm việc tại nhà


GET/PUT/DELETE
/api/hr/homeworking-request/<id>
Chi tiết/Cập nhật/Xóa yêu cầu


GET/POST
/api/hr/work-locations
Lấy danh sách/Tạo địa điểm làm việc


📝 Quản lý bút toán công việc (3 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/work-entries
Lấy danh sách/Tạo bút toán công việc


GET/PUT/DELETE
/api/hr/work-entry/<id>
Chi tiết/Cập nhật/Xóa bút toán


GET
/api/hr/employee/<id>/work-entries
Bút toán theo nhân viên


📅 Quản lý lịch HR (3 Endpoint)



Phương thức
Endpoint
Mô tả



GET/POST
/api/hr/calendar-events
Lấy danh sách/Tạo sự kiện lịch


GET/PUT/DELETE
/api/hr/calendar-event/<id>
Chi tiết/Cập nhật/Xóa sự kiện


GET
/api/hr/employee/<id>/calendar-events
Lịch theo nhân viên


🚗 Quản lý xe công ty (2 Endpoint)



Phương thức
Endpoint
Mô tả



GET
/api/hr/fleet-vehicles
Lấy danh sách xe công ty


GET
/api/hr/employee/<id>/fleet-vehicles
Xe theo nhân viên


📊 Báo cáo & Phân tích (5 Endpoint)



Phương thức
Endpoint
Mô tả



GET
/api/hr/reports/summary
Báo cáo tổng hợp HR


POST
/api/hr/reports/export
Xuất báo cáo (Excel/PDF)


GET
/api/hr/dashboard/stats
Thống kê dashboard


GET
/api/hr/analytics/trend
Phân tích xu hướng


GET
/api/hr/notifications
Thông báo HR


🔄 Thao tác hàng loạt (2 Endpoint)



Phương thức
Endpoint
Mô tả



POST
/api/hr/bulk/update
Cập nhật hàng loạt


POST
/api/hr/bulk/delete
Xóa hàng loạt


⚙️ Tiện ích nâng cao (3 Endpoint)



Phương thức
Endpoint
Mô tả



GET
/api/hr/employee/<id>/document-check
Kiểm tra tài liệu nhân viên


GET
/api/hr/employee/<id>/performance-summary
Tóm tắt hiệu suất


GET
/api/hr/search/global
Tìm kiếm toàn cục



💬 Ví dụ hội thoại
Ví dụ 1: Lấy danh sách nhân viên
👤 Người dùng: "Xin chào! Cho tôi xem danh sách nhân viên phòng IT"
🤖 AI: [Gọi get_employees(department='IT')]
📋 **Danh sách nhân viên phòng IT**:
- Nguyễn Văn A (ID: 1) - Senior Developer
- Trần Thị B (ID: 2) - QA Tester
✨ **Gợi ý**: Xem chi tiết nhân viên nào?

Ví dụ 2: Luồng công việc phức tạp
👤 Người dùng: "Tôi muốn xem nhân viên phòng IT, check-in cho người đầu tiên, và tạo đơn nghỉ phép"
🤖 AI: 
**Bước 1: Danh sách nhân viên phòng IT**
[Gọi get_employees(department='IT')]
- Nguyễn Văn A (ID: 1) - Senior Developer
- Trần Thị B (ID: 2) - QA Tester

**Bước 2: Check-in cho Nguyễn Văn A**
[Gọi checkin_employee(employee_id=1)]
✅ Nguyễn Văn A đã check-in lúc 08:30

**Bước 3: Tạo đơn nghỉ phép**
[Gọi get_leave_types()]
📅 **Loại nghỉ phép**: Nghỉ phép năm, Nghỉ ốm...
Bạn muốn tạo đơn nghỉ loại nào từ ngày nào?

Ví dụ 3: Thống kê dashboard
👤 Người dùng: "Cho tôi xem tình hình tổng quan HR hôm nay"
🤖 AI: [Gọi get_dashboard_stats()]
📊 **Báo cáo HR hôm nay**:
- Tổng nhân viên: 45 người
- Đã check-in: 38/45 (84.4%)
- Đơn nghỉ chờ duyệt: 3 đơn
✨ **Gợi ý**: Xem chi tiết nhân viên chưa check-in?


📝 Định dạng Request/Response
Định dạng Request tiêu chuẩn
{
  "domain": [["field", "operator", "value"]],
  "fields": ["field1", "field2"],
  "vals": {"field": "value"}
}

Định dạng Response tiêu chuẩn
{
  "success": true,
  "data": {...},
  "error": "Thông báo lỗi nếu có"
}


🔐 Xác thực

Loại: 'json'
Xác thực: 'user' (yêu cầu đăng nhập)
Phương thức: GET, POST, PUT, DELETE (tùy endpoint)


🚀 Ví dụ sử dụng
Lấy danh sách nhân viên
curl -X GET "http://localhost:8069/api/hr/employees" \
  -H "Content-Type: application/json" \
  -d '{"domain": [["department_id.name", "=", "IT"]]}'

Tạo nhân viên mới
curl -X POST "http://localhost:8069/api/hr/employees" \
  -H "Content-Type: application/json" \
  -d '{"vals": {"name": "Nguyễn Văn A", "work_email": "nva@company.com", "department_id": 1}}'

Check-in nhân viên
curl -X POST "http://localhost:8069/api/hr/employee/1/checkin" \
  -H "Content-Type: application/json"

Tìm kiếm toàn cục
curl -X GET "http://localhost:8069/api/hr/search/global" \
  -H "Content-Type: application/json" \
  -d '{"search_term": "Nguyễn"}'

Thống kê dashboard
curl -X GET "http://localhost:8069/api/hr/dashboard/stats" \
  -H "Content-Type: application/json"


