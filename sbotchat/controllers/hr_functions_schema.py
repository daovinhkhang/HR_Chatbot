# -*- coding: utf-8 -*-
"""
HR Functions Schema for AI Function Calling
Contains the complete schema definitions for HR-related functions
Extracted from main.py _get_hr_functions_schema method for better organization
"""

class HRFunctionsSchema:
    """Class containing HR functions schema for AI function calling"""
    
    @staticmethod
    def get_schema():
        """Get HR functions schema for AI function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_employees",
                    "description": "Lấy danh sách nhân viên với filter tùy chọn",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "department": {"type": "string", "description": "Tên phòng ban để lọc"},
                            "name": {"type": "string", "description": "Tên nhân viên để tìm kiếm"},
                            "active": {"type": "boolean", "description": "Chỉ lấy nhân viên đang hoạt động", "default": True},
                            "limit": {"type": "integer", "description": "Số lượng nhân viên tối đa", "default": 20}
                        }
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "create_leave_request",
                    "description": "Tạo đơn xin nghỉ phép cho nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "leave_type_id": {"type": "integer", "description": "ID loại nghỉ phép"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu nghỉ (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc nghỉ (YYYY-MM-DD)"},
                            "name": {"type": "string", "description": "Lý do nghỉ phép"}
                        },
                        "required": ["employee_id", "leave_type_id", "date_from", "date_to", "name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_attendance_summary",
                    "description": "Lấy tóm tắt chấm công của nhân viên",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên, không bắt buộc"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "checkin_employee", 
                    "description": "Check-in cho nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "checkout_employee",
                    "description": "Check-out cho nhân viên", 
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_dashboard_stats",
                    "description": "Lấy thống kê tổng quan HR dashboard",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "search_hr_global",
                    "description": "Tìm kiếm toàn bộ dữ liệu HR (nhân viên, đơn nghỉ, hợp đồng...)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_term": {"type": "string", "description": "Từ khóa tìm kiếm"}
                        },
                        "required": ["search_term"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_leave_types",
                    "description": "Lấy danh sách các loại nghỉ phép",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "approve_leave_request", 
                    "description": "Phê duyệt đơn nghỉ phép",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "leave_id": {"type": "integer", "description": "ID đơn nghỉ phép"}
                        },
                        "required": ["leave_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_employee_leaves",
                    "description": "Lấy danh sách đơn nghỉ phép của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên, không bắt buộc"},
                            "state": {"type": "string", "description": "Trạng thái đơn: draft, confirm, validate, refuse"}
                        }
                    }
                }
            },
            # ======================= BƯỚC 1: EMPLOYEE MANAGEMENT =======================
            {
                "type": "function",
                "function": {
                    "name": "create_employee",
                    "description": "Tạo nhân viên mới",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Tên nhân viên"},
                            "work_email": {"type": "string", "description": "Email công việc"},
                            "department_id": {"type": "integer", "description": "ID phòng ban"},
                            "job_id": {"type": "integer", "description": "ID vị trí công việc"}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_employee",
                    "description": "Cập nhật thông tin nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "name": {"type": "string", "description": "Tên nhân viên"},
                            "work_email": {"type": "string", "description": "Email công việc"},
                            "department_id": {"type": "integer", "description": "ID phòng ban"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_employee_detail",
                    "description": "Lấy thông tin chi tiết nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "archive_employee",
                    "description": "Lưu trữ/vô hiệu hóa nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_departments",
                    "description": "Lấy danh sách phòng ban",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "active": {"type": "boolean", "description": "Chỉ lấy phòng ban hoạt động", "default": True}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_department",
                    "description": "Tạo phòng ban mới",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Tên phòng ban"},
                            "manager_id": {"type": "integer", "description": "ID người quản lý"}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_department",
                    "description": "Cập nhật thông tin phòng ban",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "department_id": {"type": "integer", "description": "ID phòng ban"},
                            "name": {"type": "string", "description": "Tên phòng ban"},
                            "manager_id": {"type": "integer", "description": "ID người quản lý"}
                        },
                        "required": ["department_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_jobs",
                    "description": "Lấy danh sách vị trí công việc",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "department_id": {"type": "integer", "description": "ID phòng ban để lọc"},
                            "active": {"type": "boolean", "description": "Chỉ lấy vị trí đang hoạt động", "default": True},
                            "limit": {"type": "integer", "description": "Số lượng vị trí tối đa", "default": 20}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_job",
                    "description": "Tạo vị trí công việc mới với thông tin đầy đủ",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Tên vị trí"},
                            "department_id": {"type": "integer", "description": "ID phòng ban"},
                            "expected_employees": {"type": "integer", "description": "Số lượng nhân viên dự kiến", "default": 1},
                            "description": {"type": "string", "description": "Mô tả công việc chi tiết"},
                            "requirements": {"type": "string", "description": "Yêu cầu công việc"}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_employee_status",
                    "description": "Lấy trạng thái nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_employee_status",
                    "description": "Cập nhật trạng thái nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "active": {"type": "boolean", "description": "Trạng thái hoạt động"},
                            "departure_date": {"type": "string", "description": "Ngày nghỉ việc (YYYY-MM-DD)"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_employee_bhxh",
                    "description": "Lấy thông tin BHXH/BHYT/BHTN của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_employee_bhxh",
                    "description": "Cập nhật thông tin BHXH/BHYT/BHTN",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "bhxh_code": {"type": "string", "description": "Mã số BHXH"},
                            "bhyt_code": {"type": "string", "description": "Mã số BHYT"},
                            "personal_tax_code": {"type": "string", "description": "Mã số thuế TNCN"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_employee_projects",
                    "description": "Lấy danh sách dự án của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "assign_employee_project",
                    "description": "Phân công nhân viên vào dự án",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "project_id": {"type": "integer", "description": "ID dự án"},
                            "role": {"type": "string", "description": "Vai trò trong dự án"},
                            "date_start": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"}
                        },
                        "required": ["employee_id", "project_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_employee_shifts",
                    "description": "Lấy ca làm việc của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "assign_employee_shift",
                    "description": "Phân công ca làm việc cho nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "shift_name": {"type": "string", "description": "Tên ca làm việc"},
                            "time_start": {"type": "string", "description": "Giờ bắt đầu (HH:MM)"},
                            "time_end": {"type": "string", "description": "Giờ kết thúc (HH:MM)"},
                            "date_apply": {"type": "string", "description": "Ngày áp dụng (YYYY-MM-DD)"}
                        },
                        "required": ["employee_id", "shift_name", "time_start", "time_end"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_employee_tax_info",
                    "description": "Lấy thông tin thuế TNCN của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "year": {"type": "integer", "description": "Năm thuế"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_employee_tax_record",
                    "description": "Tạo bản kê khai thuế TNCN",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "year": {"type": "integer", "description": "Năm thuế"},
                            "total_income": {"type": "number", "description": "Tổng thu nhập"},
                            "self_deduction": {"type": "number", "description": "Giảm trừ bản thân"},
                            "dependent_deduction": {"type": "number", "description": "Giảm trừ người phụ thuộc"}
                        },
                        "required": ["employee_id", "year", "total_income"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_details",
                    "description": "Lấy thông tin chi tiết hợp đồng của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_contract_details",
                    "description": "Cập nhật thông tin hợp đồng của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "contract_id": {"type": "integer", "description": "ID hợp đồng"},
                            "start_date": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "end_date": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "status": {"type": "string", "description": "Trạng thái hợp đồng"}
                        },
                        "required": ["employee_id", "contract_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_history",
                    "description": "Lấy lịch sử hợp đồng của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_status",
                    "description": "Lấy trạng thái hợp đồng của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_type",
                    "description": "Lấy loại hợp đồng của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_duration",
                    "description": "Lấy thời hạn hợp đồng của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_renewal_date",
                    "description": "Lấy ngày hết hạn hợp đồng của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_termination_reason",
                    "description": "Lấy lý do kết thúc hợp đồng của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_signing_date",
                    "description": "Lấy ngày ký hợp đồng của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_signatory",
                    "description": "Lấy người ký hợp đồng của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_signature",
                    "description": "Lấy chữ ký của nhân viên trong hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_attachment",
                    "description": "Lấy tệp đính kèm của hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_revision_history",
                    "description": "Lấy lịch sử sửa đổi hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_approval_status",
                    "description": "Lấy trạng thái phê duyệt hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_approval_date",
                    "description": "Lấy ngày phê duyệt hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_approval_signatory",
                    "description": "Lấy người ký phê duyệt hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_approval_signature",
                    "description": "Lấy chữ ký của người ký phê duyệt hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_approval_attachment",
                    "description": "Lấy tệp đính kèm của hợp đồng đã được phê duyệt",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_amendment_history",
                    "description": "Lấy lịch sử sửa đổi hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_amendment_status",
                    "description": "Lấy trạng thái sửa đổi hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_amendment_approval_status",
                    "description": "Lấy trạng thái phê duyệt sửa đổi hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_amendment_approval_date",
                    "description": "Lấy ngày phê duyệt sửa đổi hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_amendment_approval_signatory",
                    "description": "Lấy người ký phê duyệt sửa đổi hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_amendment_approval_signature",
                    "description": "Lấy chữ ký của người ký phê duyệt sửa đổi hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_amendment_approval_attachment",
                    "description": "Lấy tệp đính kèm của hợp đồng đã được phê duyệt",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            # ======================= BƯỚC 2: CONTRACT MANAGEMENT =======================
            {
                "type": "function",
                "function": {
                    "name": "get_contracts",
                    "description": "Lấy danh sách hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên để lọc"},
                            "state": {"type": "string", "description": "Trạng thái hợp đồng: draft, open, close, cancel"},
                            "active": {"type": "boolean", "description": "Chỉ lấy hợp đồng đang hoạt động", "default": True}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_contract",
                    "description": "Tạo hợp đồng mới cho nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "name": {"type": "string", "description": "Tên hợp đồng"},
                            "date_start": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_end": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "wage": {"type": "number", "description": "Mức lương"}
                        },
                        "required": ["employee_id", "name", "date_start", "wage"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_contract",
                    "description": "Cập nhật thông tin hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contract_id": {"type": "integer", "description": "ID hợp đồng"},
                            "name": {"type": "string", "description": "Tên hợp đồng"},
                            "date_end": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "wage": {"type": "number", "description": "Mức lương"}
                        },
                        "required": ["contract_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_detail",
                    "description": "Lấy thông tin chi tiết hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contract_id": {"type": "integer", "description": "ID hợp đồng"}
                        },
                        "required": ["contract_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "activate_contract",
                    "description": "Kích hoạt hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contract_id": {"type": "integer", "description": "ID hợp đồng"}
                        },
                        "required": ["contract_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "terminate_contract",
                    "description": "Chấm dứt hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contract_id": {"type": "integer", "description": "ID hợp đồng"},
                            "date_end": {"type": "string", "description": "Ngày chấm dứt (YYYY-MM-DD)"},
                            "reason": {"type": "string", "description": "Lý do chấm dứt"}
                        },
                        "required": ["contract_id", "date_end"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "renew_contract",
                    "description": "Gia hạn hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contract_id": {"type": "integer", "description": "ID hợp đồng"},
                            "new_end_date": {"type": "string", "description": "Ngày kết thúc mới (YYYY-MM-DD)"},
                            "new_wage": {"type": "number", "description": "Mức lương mới"}
                        },
                        "required": ["contract_id", "new_end_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contract_history",
                    "description": "Lấy lịch sử hợp đồng của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_salary_structures",
                    "description": "Lấy danh sách cấu trúc lương",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "active": {"type": "boolean", "description": "Chỉ lấy cấu trúc đang hoạt động", "default": True}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_contract_salary",
                    "description": "Cập nhật lương trong hợp đồng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contract_id": {"type": "integer", "description": "ID hợp đồng"},
                            "wage": {"type": "number", "description": "Mức lương mới"},
                            "effective_date": {"type": "string", "description": "Ngày hiệu lực (YYYY-MM-DD)"}
                        },
                        "required": ["contract_id", "wage"]
                    }
                }
            },
            # ======================= BƯỚC 3: ATTENDANCE MANAGEMENT =======================
            {
                "type": "function",
                "function": {
                    "name": "get_attendance_records",
                    "description": "Lấy bản ghi chấm công",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên để lọc"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "limit": {"type": "integer", "description": "Số lượng bản ghi tối đa", "default": 50}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_attendance_manual",
                    "description": "Tạo bản ghi chấm công thủ công",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "check_in": {"type": "string", "description": "Thời gian vào (YYYY-MM-DD HH:MM:SS)"},
                            "check_out": {"type": "string", "description": "Thời gian ra (YYYY-MM-DD HH:MM:SS)"},
                            "reason": {"type": "string", "description": "Lý do tạo thủ công"}
                        },
                        "required": ["employee_id", "check_in"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_attendance_record",
                    "description": "Cập nhật bản ghi chấm công",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "attendance_id": {"type": "integer", "description": "ID bản ghi chấm công"},
                            "check_in": {"type": "string", "description": "Thời gian vào (YYYY-MM-DD HH:MM:SS)"},
                            "check_out": {"type": "string", "description": "Thời gian ra (YYYY-MM-DD HH:MM:SS)"}
                        },
                        "required": ["attendance_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_attendance_record",
                    "description": "Xóa bản ghi chấm công",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "attendance_id": {"type": "integer", "description": "ID bản ghi chấm công"}
                        },
                        "required": ["attendance_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_overtime",
                    "description": "Tính toán giờ làm thêm",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "standard_hours": {"type": "number", "description": "Số giờ chuẩn/ngày", "default": 8}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_missing_attendance",
                    "description": "Tìm chấm công thiếu",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "approve_attendance",
                    "description": "Phê duyệt chấm công",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "attendance_ids": {"type": "array", "items": {"type": "integer"}, "description": "Danh sách ID bản ghi chấm công"},
                            "approved_by": {"type": "integer", "description": "ID người phê duyệt"}
                        },
                        "required": ["attendance_ids"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_work_schedules",
                    "description": "Lấy lịch làm việc",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_attendance",
                    "description": "Xác thực chấm công",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "date": {"type": "string", "description": "Ngày kiểm tra (YYYY-MM-DD)"}
                        },
                        "required": ["employee_id", "date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_attendance_analytics",
                    "description": "Phân tích chấm công",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên để lọc"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "group_by": {"type": "string", "description": "Nhóm theo: day, week, month", "default": "day"}
                        }
                    }
                }
            },
            # ======================= BƯỚC 4: LEAVE MANAGEMENT =======================
            {
                "type": "function",
                "function": {
                    "name": "get_leave_types_new",
                    "description": "Lấy danh sách loại nghỉ phép",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "active": {"type": "boolean", "description": "Chỉ lấy loại đang hoạt động", "default": True},
                            "company_id": {"type": "integer", "description": "ID công ty để lọc"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_leave_type",
                    "description": "Tạo loại nghỉ phép mới",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Tên loại nghỉ phép"},
                            "allocation_type": {"type": "string", "description": "Loại phân bổ: no, fixed, fixed_allocation"},
                            "color": {"type": "integer", "description": "Màu hiển thị (0-11)"},
                            "time_type": {"type": "string", "description": "Đơn vị: leave (ngày), hour (giờ)"}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_leave_allocations",
                    "description": "Lấy danh sách phân bổ nghỉ phép",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên để lọc"},
                            "leave_type_id": {"type": "integer", "description": "ID loại nghỉ phép"},
                            "state": {"type": "string", "description": "Trạng thái: draft, confirm, validate"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_leave_allocation",
                    "description": "Tạo phân bổ nghỉ phép",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "leave_type_id": {"type": "integer", "description": "ID loại nghỉ phép"},
                            "number_of_days": {"type": "number", "description": "Số ngày phân bổ"},
                            "name": {"type": "string", "description": "Mô tả phân bổ"}
                        },
                        "required": ["employee_id", "leave_type_id", "number_of_days"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_leave_requests",
                    "description": "Lấy danh sách đơn nghỉ phép",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên để lọc"},
                            "state": {"type": "string", "description": "Trạng thái: draft, confirm, validate, refuse, cancel"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_leave_request_new",
                    "description": "Tạo đơn nghỉ phép mới",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "leave_type_id": {"type": "integer", "description": "ID loại nghỉ phép"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu nghỉ (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc nghỉ (YYYY-MM-DD)"},
                            "name": {"type": "string", "description": "Lý do nghỉ phép"},
                            "request_date_from": {"type": "string", "description": "Thời gian bắt đầu (YYYY-MM-DD HH:MM:SS)"},
                            "request_date_to": {"type": "string", "description": "Thời gian kết thúc (YYYY-MM-DD HH:MM:SS)"}
                        },
                        "required": ["employee_id", "leave_type_id", "date_from", "date_to", "name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "approve_leave",
                    "description": "Phê duyệt đơn nghỉ phép",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "leave_id": {"type": "integer", "description": "ID đơn nghỉ phép"},
                            "approve_note": {"type": "string", "description": "Ghi chú phê duyệt"}
                        },
                        "required": ["leave_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "refuse_leave",
                    "description": "Từ chối đơn nghỉ phép",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "leave_id": {"type": "integer", "description": "ID đơn nghỉ phép"},
                            "refuse_reason": {"type": "string", "description": "Lý do từ chối"}
                        },
                        "required": ["leave_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_leave_balance",
                    "description": "Lấy số ngày nghỉ còn lại của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "leave_type_id": {"type": "integer", "description": "ID loại nghỉ phép để lọc"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_leave_analytics",
                    "description": "Phân tích và thống kê nghỉ phép",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên để lọc"},
                            "department_id": {"type": "integer", "description": "ID phòng ban để lọc"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "group_by": {"type": "string", "description": "Nhóm theo: employee, department, leave_type", "default": "employee"}
                        }
                    }
                }
            },
            # ======================= BƯỚC 5: PAYROLL MANAGEMENT =======================
            {
                "type": "function",
                "function": {
                    "name": "get_payslips",
                    "description": "Lấy danh sách bảng lương",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên để lọc"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "state": {"type": "string", "description": "Trạng thái: draft, verify, done, cancel"},
                            "limit": {"type": "integer", "description": "Số lượng bảng lương tối đa", "default": 20}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_payslip",
                    "description": "Tạo bảng lương mới cho nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu tính lương (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc tính lương (YYYY-MM-DD)"},
                            "contract_id": {"type": "integer", "description": "ID hợp đồng"},
                            "struct_id": {"type": "integer", "description": "ID cấu trúc lương"}
                        },
                        "required": ["employee_id", "date_from", "date_to"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compute_payslip",
                    "description": "Tính toán bảng lương",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "payslip_id": {"type": "integer", "description": "ID bảng lương cần tính"},
                            "force_recompute": {"type": "boolean", "description": "Buộc tính lại", "default": False}
                        },
                        "required": ["payslip_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_payslip_lines",
                    "description": "Lấy chi tiết dòng bảng lương",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "payslip_id": {"type": "integer", "description": "ID bảng lương"},
                            "category": {"type": "string", "description": "Loại dòng: BASIC, ALW, DED, GROSS, NET"}
                        },
                        "required": ["payslip_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_salary_rules",
                    "description": "Lấy danh sách quy tắc lương",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category_id": {"type": "integer", "description": "ID danh mục quy tắc"},
                            "active": {"type": "boolean", "description": "Chỉ lấy quy tắc đang hoạt động", "default": True},
                            "struct_id": {"type": "integer", "description": "ID cấu trúc lương để lọc"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_salary_rule",
                    "description": "Tạo quy tắc lương mới",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Tên quy tắc lương"},
                            "code": {"type": "string", "description": "Mã quy tắc (viết hoa, không dấu)"},
                            "category_id": {"type": "integer", "description": "ID danh mục quy tắc"},
                            "sequence": {"type": "integer", "description": "Thứ tự ưu tiên", "default": 5},
                            "amount_select": {"type": "string", "description": "Loại tính: fix, percentage, python", "default": "fix"},
                            "amount_fix": {"type": "number", "description": "Số tiền cố định"},
                            "amount_percentage": {"type": "number", "description": "Tỷ lệ phần trăm"}
                        },
                        "required": ["name", "code", "category_id"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "get_payroll_structures",
                    "description": "Lấy danh sách cấu trúc lương",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "active": {"type": "boolean", "description": "Chỉ lấy cấu trúc đang hoạt động", "default": True},
                            "country_id": {"type": "integer", "description": "ID quốc gia để lọc"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_payroll_structure",
                    "description": "Tạo cấu trúc lương mới",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Tên cấu trúc lương"},
                            "code": {"type": "string", "description": "Mã cấu trúc"},
                            "country_id": {"type": "integer", "description": "ID quốc gia"},
                            "rule_ids": {"type": "array", "items": {"type": "integer"}, "description": "Danh sách ID quy tắc lương"}
                        },
                        "required": ["name", "code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_payslip",
                    "description": "Xác nhận và phê duyệt bảng lương",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "payslip_id": {"type": "integer", "description": "ID bảng lương"},
                            "validation_note": {"type": "string", "description": "Ghi chú xác nhận"}
                        },
                        "required": ["payslip_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_payroll_summary",
                    "description": "Tóm tắt và thống kê bảng lương",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên để lọc"},
                            "department_id": {"type": "integer", "description": "ID phòng ban để lọc"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "group_by": {"type": "string", "description": "Nhóm theo: employee, department, month", "default": "employee"}
                        }
                    }
                }
            },
            # ======================= BƯỚC 6: RECRUITMENT MANAGEMENT =======================
            {
                "type": "function",
                "function": {
                    "name": "get_applicants",
                    "description": "Lấy danh sách ứng viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer", "description": "ID vị trí tuyển dụng để lọc"},
                            "stage_id": {"type": "integer", "description": "ID giai đoạn tuyển dụng"},
                            "state": {"type": "string", "description": "Trạng thái: new, draft, confirm, done, cancel"},
                            "active": {"type": "boolean", "description": "Chỉ lấy ứng viên đang hoạt động", "default": True},
                            "limit": {"type": "integer", "description": "Số lượng ứng viên tối đa", "default": 20}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_applicant",
                    "description": "Tạo ứng viên mới",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "partner_name": {"type": "string", "description": "Tên ứng viên"},
                            "email_from": {"type": "string", "description": "Email ứng viên"},
                            "partner_phone": {"type": "string", "description": "Số điện thoại"},
                            "job_id": {"type": "integer", "description": "ID vị trí tuyển dụng"},
                            "description": {"type": "string", "description": "Mô tả/CV ứng viên"}
                        },
                        "required": ["partner_name", "job_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_applicant_stage",
                    "description": "Cập nhật giai đoạn tuyển dụng của ứng viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "applicant_id": {"type": "integer", "description": "ID ứng viên"},
                            "stage_id": {"type": "integer", "description": "ID giai đoạn mới"},
                            "note": {"type": "string", "description": "Ghi chú thay đổi"}
                        },
                        "required": ["applicant_id", "stage_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "hire_applicant",
                    "description": "Tuyển dụng ứng viên (tạo nhân viên)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "applicant_id": {"type": "integer", "description": "ID ứng viên"},
                            "department_id": {"type": "integer", "description": "ID phòng ban"},
                            "job_id": {"type": "integer", "description": "ID vị trí công việc"},
                            "start_date": {"type": "string", "description": "Ngày bắt đầu làm việc (YYYY-MM-DD)"}
                        },
                        "required": ["applicant_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "refuse_applicant",
                    "description": "Từ chối ứng viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "applicant_id": {"type": "integer", "description": "ID ứng viên"},
                            "refuse_reason": {"type": "string", "description": "Lý do từ chối"}
                        },
                        "required": ["applicant_id", "refuse_reason"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recruitment_stages",
                    "description": "Lấy danh sách giai đoạn tuyển dụng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer", "description": "ID vị trí tuyển dụng để lọc"},
                            "active": {"type": "boolean", "description": "Chỉ lấy giai đoạn đang hoạt động", "default": True}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_recruitment_stage",
                    "description": "Tạo giai đoạn tuyển dụng mới",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Tên giai đoạn"},
                            "sequence": {"type": "integer", "description": "Thứ tự ưu tiên", "default": 10},
                            "fold": {"type": "boolean", "description": "Ẩn trong kanban view", "default": False},
                            "hired_stage": {"type": "boolean", "description": "Giai đoạn tuyển dụng", "default": False}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recruitment_jobs",
                    "description": "Lấy danh sách vị trí tuyển dụng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "department_id": {"type": "integer", "description": "ID phòng ban để lọc"},
                            "active": {"type": "boolean", "description": "Chỉ lấy vị trí đang tuyển", "default": True},
                            "state": {"type": "string", "description": "Trạng thái: recruit, open"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_recruitment_job",
                    "description": "Tạo vị trí tuyển dụng mới",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Tên vị trí tuyển dụng"},
                            "department_id": {"type": "integer", "description": "ID phòng ban"},
                            "no_of_recruitment": {"type": "integer", "description": "Số lượng cần tuyển", "default": 1},
                            "description": {"type": "string", "description": "Mô tả công việc"},
                            "requirements": {"type": "string", "description": "Yêu cầu ứng viên"}
                        },
                        "required": ["name", "department_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recruitment_analytics",
                    "description": "Phân tích và thống kê tuyển dụng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer", "description": "ID vị trí tuyển dụng để lọc"},
                            "department_id": {"type": "integer", "description": "ID phòng ban để lọc"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "group_by": {"type": "string", "description": "Nhóm theo: job, department, stage, month", "default": "job"}
                        }
                    }
                }
            },
            # ======================= BƯỚC 7: SKILLS MANAGEMENT =======================
            {
                "type": "function",
                "function": {
                    "name": "get_skills",
                    "description": "Lấy danh sách kỹ năng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "skill_type_id": {"type": "integer", "description": "ID loại kỹ năng để lọc"},
                            "active": {"type": "boolean", "description": "Chỉ lấy kỹ năng đang hoạt động", "default": True},
                            "search": {"type": "string", "description": "Tìm kiếm theo tên kỹ năng"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_skill",
                    "description": "Tạo kỹ năng mới",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Tên kỹ năng"},
                            "skill_type_id": {"type": "integer", "description": "ID loại kỹ năng"},
                            "sequence": {"type": "integer", "description": "Thứ tự ưu tiên", "default": 10},
                            "color": {"type": "integer", "description": "Màu hiển thị (0-11)", "default": 0}
                        },
                        "required": ["name", "skill_type_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_skill_types",
                    "description": "Lấy danh sách loại kỹ năng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "active": {"type": "boolean", "description": "Chỉ lấy loại đang hoạt động", "default": True}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_skill_type",
                    "description": "Tạo loại kỹ năng mới",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Tên loại kỹ năng"},
                            "color": {"type": "integer", "description": "Màu hiển thị (0-11)", "default": 0}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_employee_skills",
                    "description": "Lấy kỹ năng của nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "skill_type_id": {"type": "integer", "description": "ID loại kỹ năng để lọc"},
                            "skill_level_id": {"type": "integer", "description": "ID cấp độ kỹ năng để lọc"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "assign_employee_skill",
                    "description": "Gán kỹ năng cho nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "skill_id": {"type": "integer", "description": "ID kỹ năng"},
                            "skill_level_id": {"type": "integer", "description": "ID cấp độ kỹ năng"},
                            "level_progress": {"type": "integer", "description": "Tiến độ % (0-100)", "default": 0}
                        },
                        "required": ["employee_id", "skill_id", "skill_level_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_skill_levels",
                    "description": "Lấy danh sách cấp độ kỹ năng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "skill_type_id": {"type": "integer", "description": "ID loại kỹ năng để lọc"},
                            "active": {"type": "boolean", "description": "Chỉ lấy cấp độ đang hoạt động", "default": True}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_skills_analytics",
                    "description": "Phân tích và thống kê kỹ năng",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "department_id": {"type": "integer", "description": "ID phòng ban để lọc"},
                            "skill_type_id": {"type": "integer", "description": "ID loại kỹ năng để lọc"},
                            "group_by": {"type": "string", "description": "Nhóm theo: employee, department, skill_type, skill_level", "default": "skill_type"}
                        }
                    }
                }
            },
            # ======================= BƯỚC 8: TIMESHEET MANAGEMENT =======================
            {
                "type": "function",
                "function": {
                    "name": "get_timesheets",
                    "description": "Lấy danh sách timesheet",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên để lọc"},
                            "project_id": {"type": "integer", "description": "ID dự án để lọc"},
                            "task_id": {"type": "integer", "description": "ID task để lọc"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "limit": {"type": "integer", "description": "Số lượng timesheet tối đa", "default": 50}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_timesheet",
                    "description": "Tạo timesheet mới",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "project_id": {"type": "integer", "description": "ID dự án"},
                            "task_id": {"type": "integer", "description": "ID task"},
                            "date": {"type": "string", "description": "Ngày làm việc (YYYY-MM-DD)"},
                            "unit_amount": {"type": "number", "description": "Số giờ làm việc"},
                            "name": {"type": "string", "description": "Mô tả công việc"}
                        },
                        "required": ["employee_id", "project_id", "date", "unit_amount", "name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_timesheet",
                    "description": "Cập nhật timesheet",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "timesheet_id": {"type": "integer", "description": "ID timesheet"},
                            "unit_amount": {"type": "number", "description": "Số giờ làm việc mới"},
                            "name": {"type": "string", "description": "Mô tả công việc mới"},
                            "date": {"type": "string", "description": "Ngày làm việc mới (YYYY-MM-DD)"}
                        },
                        "required": ["timesheet_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_employee_timesheets",
                    "description": "Lấy timesheet theo nhân viên với tổng hợp",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "group_by": {"type": "string", "description": "Nhóm theo: day, week, month, project", "default": "day"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_project_timesheets",
                    "description": "Lấy timesheet theo dự án với chi phí",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "integer", "description": "ID dự án"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "include_cost": {"type": "boolean", "description": "Bao gồm chi phí", "default": True}
                        },
                        "required": ["project_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_timesheet_analytics",
                    "description": "Phân tích và thống kê timesheet",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên để lọc"},
                            "department_id": {"type": "integer", "description": "ID phòng ban để lọc"},
                            "project_id": {"type": "integer", "description": "ID dự án để lọc"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "group_by": {"type": "string", "description": "Nhóm theo: employee, project, task, department", "default": "employee"}
                        }
                    }
                }
            },
            # ======================= BƯỚC 9: INSURANCE MANAGEMENT =======================
            {
                "type": "function",
                "function": {
                    "name": "get_insurances",
                    "description": "Lấy danh sách bảo hiểm nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên để lọc"},
                            "policy_type": {"type": "string", "description": "Loại bảo hiểm: bhxh, bhyt, bhtn, accident"},
                            "state": {"type": "string", "description": "Trạng thái: draft, active, expired, cancelled"},
                            "active": {"type": "boolean", "description": "Chỉ lấy bảo hiểm đang hoạt động", "default": True}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_insurance",
                    "description": "Tạo bảo hiểm mới cho nhân viên",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên"},
                            "policy_type": {"type": "string", "description": "Loại bảo hiểm: bhxh, bhyt, bhtn, accident"},
                            "start_date": {"type": "string", "description": "Ngày bắt đầu hiệu lực (YYYY-MM-DD)"},
                            "end_date": {"type": "string", "description": "Ngày kết thúc hiệu lực (YYYY-MM-DD)"},
                            "premium_amount": {"type": "number", "description": "Số tiền phí bảo hiểm"},
                            "company_contribution": {"type": "number", "description": "Đóng góp của công ty"},
                            "employee_contribution": {"type": "number", "description": "Đóng góp của nhân viên"}
                        },
                        "required": ["employee_id", "policy_type", "start_date", "premium_amount"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_insurance_status",
                    "description": "Cập nhật trạng thái bảo hiểm",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "insurance_id": {"type": "integer", "description": "ID bảo hiểm"},
                            "state": {"type": "string", "description": "Trạng thái mới: active, expired, cancelled"},
                            "note": {"type": "string", "description": "Ghi chú thay đổi"}
                        },
                        "required": ["insurance_id", "state"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_insurance_analytics",
                    "description": "Phân tích và thống kê bảo hiểm",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer", "description": "ID nhân viên để lọc"},
                            "department_id": {"type": "integer", "description": "ID phòng ban để lọc"},
                            "policy_type": {"type": "string", "description": "Loại bảo hiểm để lọc"},
                            "date_from": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "date_to": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"},
                            "group_by": {"type": "string", "description": "Nhóm theo: employee, department, policy_type, month", "default": "policy_type"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_job_detail",
                    "description": "Lấy thông tin chi tiết vị trí công việc",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer", "description": "ID vị trí công việc"}
                        },
                        "required": ["job_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_job",
                    "description": "Cập nhật thông tin vị trí công việc",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer", "description": "ID vị trí công việc"},
                            "name": {"type": "string", "description": "Tên vị trí"},
                            "department_id": {"type": "integer", "description": "ID phòng ban"},
                            "expected_employees": {"type": "integer", "description": "Số lượng nhân viên dự kiến"},
                            "description": {"type": "string", "description": "Mô tả công việc"},
                            "requirements": {"type": "string", "description": "Yêu cầu công việc"},
                            "state": {"type": "string", "description": "Trạng thái: open, recruit, close"}
                        },
                        "required": ["job_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "archive_job",
                    "description": "Lưu trữ/vô hiệu hóa vị trí công việc",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "integer", "description": "ID vị trí công việc"}
                        },
                        "required": ["job_id"]
                    }
                }
            }
        ] 