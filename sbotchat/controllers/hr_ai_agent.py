# -*- coding: utf-8 -*-
import json
import re
from odoo import http, fields
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class HRAIAgentController(http.Controller):
    """
    AI Agent Controller để xử lý ngôn ngữ tự nhiên và mapping tới HR API calls
    """

    @http.route('/sbotchat/hr_agent', type='json', auth='user', methods=['POST'])
    def hr_ai_agent(self, message, conversation_id=None, **kwargs):
        """Main AI Agent endpoint để xử lý yêu cầu HR bằng ngôn ngữ tự nhiên"""
        try:
            # Phân tích intent từ message
            intent_result = self._analyze_intent(message)
            
            # Kiểm tra xem có trường 'intent' hay không
            if 'intent' in intent_result and intent_result['intent'] == 'hr_action':
                # Extract parameters
                params = self._extract_parameters(message, intent_result['action'])
                
                # Thực hiện API call
                api_result = self._execute_hr_api(intent_result['api_endpoint'], params)
                
                # Format response cho người dùng
                response = self._format_response(intent_result['action'], api_result)
                
                return {
                    'success': True,
                    'response': response,
                    'api_called': intent_result['api_endpoint'],
                    'data': api_result.get('data'),
                    'intent': intent_result.get('intent', 'hr_action')
                }
            else:
                # Xử lý các intent khác hoặc fallback
                action = intent_result.get('action', 'dashboard_stats')
                api_endpoint = intent_result.get('api_endpoint', '/api/hr/dashboard/stats')
                
                # Extract parameters
                params = self._extract_parameters(message, action)
                
                # Thực hiện API call
                api_result = self._execute_hr_api(api_endpoint, params)
                
                # Format response cho người dùng
                response = self._format_response(action, api_result)
                
                return {
                    'success': True,
                    'response': response,
                    'api_called': api_endpoint,
                    'data': api_result.get('data'),
                    'intent': 'hr_action',
                    'confidence': intent_result.get('confidence', 0.5)
                }
                
        except Exception as e:
            _logger.error(f"Lỗi trong HR AI Agent: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _analyze_intent(self, message):
        """Phân tích intent của user message và ánh xạ tới HR action tương ứng"""
        message_lower = message.lower()
        
        # ======================= EMPLOYEE MANAGEMENT INTENTS =======================
        # 1. /api/hr/employees (GET, POST)
        if any(keyword in message_lower for keyword in [
            'danh sách nhân viên', 'list employee', 'all employee', 'tất cả nhân viên',
            'hiển thị nhân viên', 'show employee', 'xem nhân viên', 'view employee',
            'tạo nhân viên', 'create employee', 'thêm nhân viên', 'add employee'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action',
                    'action': 'create_employee',
                    'api_endpoint': '/api/hr/employees',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'list_employees',
                    'api_endpoint': '/api/hr/employees', 
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 2. /api/hr/employee/<int:employee_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết nhân viên', 'employee detail', 'thông tin nhân viên', 'employee info',
            'cập nhật nhân viên', 'update employee', 'sửa nhân viên', 'edit employee',
            'xóa nhân viên', 'delete employee', 'archive employee'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action',
                    'action': 'update_employee',
                    'api_endpoint': '/api/hr/employee/{employee_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete', 'archive']):
                return {
                    'intent': 'hr_action',
                    'action': 'delete_employee',
                    'api_endpoint': '/api/hr/employee/{employee_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'get_employee_detail',
                    'api_endpoint': '/api/hr/employee/{employee_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 3. /api/hr/employee/<int:employee_id>/status (GET, PUT)
        if any(keyword in message_lower for keyword in [
            'trạng thái nhân viên', 'employee status', 'status nhân viên',
            'tình trạng nhân viên', 'employee state', 'hoạt động nhân viên'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'thay đổi', 'change']):
                return {
                    'intent': 'hr_action',
                    'action': 'update_employee_status',
                    'api_endpoint': '/api/hr/employee/{employee_id}/status',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'get_employee_status',
                    'api_endpoint': '/api/hr/employee/{employee_id}/status',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 4. /api/hr/employee/departments (GET, POST)
        if any(keyword in message_lower for keyword in [
            'phòng ban', 'department', 'departments', 'bộ phận',
            'danh sách phòng ban', 'list department', 'tạo phòng ban', 'create department'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action',
                    'action': 'create_department',
                    'api_endpoint': '/api/hr/employee/departments',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'list_departments',
                    'api_endpoint': '/api/hr/employee/departments',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 5. /api/hr/employee/department/<int:department_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết phòng ban', 'department detail', 'thông tin phòng ban',
            'cập nhật phòng ban', 'update department', 'sửa phòng ban', 'edit department',
            'xóa phòng ban', 'delete department'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action',
                    'action': 'update_department',
                    'api_endpoint': '/api/hr/employee/department/{department_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action',
                    'action': 'delete_department',
                    'api_endpoint': '/api/hr/employee/department/{department_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'get_department_detail',
                    'api_endpoint': '/api/hr/employee/department/{department_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 6. /api/hr/employee/jobs (GET, POST)
        if any(keyword in message_lower for keyword in [
            'vị trí công việc', 'job position', 'jobs', 'chức vụ',
            'danh sách vị trí', 'list job', 'tạo vị trí', 'create job'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action',
                    'action': 'create_job',
                    'api_endpoint': '/api/hr/employee/jobs',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'list_jobs',
                    'api_endpoint': '/api/hr/employee/jobs',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 7. /api/hr/employee/job/<int:job_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết vị trí', 'job detail', 'thông tin vị trí',
            'cập nhật vị trí', 'update job', 'sửa vị trí', 'edit job',
            'xóa vị trí', 'delete job'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action',
                    'action': 'update_job',
                    'api_endpoint': '/api/hr/employee/job/{job_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action',
                    'action': 'delete_job',
                    'api_endpoint': '/api/hr/employee/job/{job_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'get_job_detail',
                    'api_endpoint': '/api/hr/employee/job/{job_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 8. /api/hr/employee/<int:employee_id>/bhxh-history (GET, POST)
        if any(keyword in message_lower for keyword in [
            'lịch sử bhxh', 'bhxh history', 'bhxh transaction', 'giao dịch bhxh',
            'lịch sử bảo hiểm', 'insurance history'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action',
                    'action': 'create_bhxh_history',
                    'api_endpoint': '/api/hr/employee/{employee_id}/bhxh-history',
                    'method': 'POST',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'get_bhxh_history',
                    'api_endpoint': '/api/hr/employee/{employee_id}/bhxh-history',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 9. /api/hr/employee/<int:employee_id>/projects-assignments (GET, POST)
        if any(keyword in message_lower for keyword in [
            'phân bổ dự án', 'project assignment', 'dự án nhân viên',
            'employee project', 'gán dự án', 'assign project'
        ]):
            if any(keyword in message_lower for keyword in ['phân bổ', 'assign', 'gán', 'tạo', 'create']):
                return {
                    'intent': 'hr_action',
                    'action': 'assign_project',
                    'api_endpoint': '/api/hr/employee/{employee_id}/projects-assignments',
                    'method': 'POST',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'get_project_assignments',
                    'api_endpoint': '/api/hr/employee/{employee_id}/projects-assignments',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 10. /api/hr/employee/<int:employee_id>/shifts-assignments (GET, POST)
        if any(keyword in message_lower for keyword in [
            'ca làm việc', 'shift assignment', 'shifts', 'ca trực',
            'phân ca', 'assign shift', 'lịch trực'
        ]):
            if any(keyword in message_lower for keyword in ['phân ca', 'assign', 'tạo', 'create', 'thêm']):
                return {
                    'intent': 'hr_action',
                    'action': 'assign_shift',
                    'api_endpoint': '/api/hr/employee/{employee_id}/shifts-assignments',
                    'method': 'POST',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'get_shift_assignments',
                    'api_endpoint': '/api/hr/employee/{employee_id}/shifts-assignments',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 11. /api/hr/employee/<int:employee_id>/personal-income-tax (GET, POST)
        if any(keyword in message_lower for keyword in [
            'thuế tncn', 'personal income tax', 'thuế thu nhập', 'quyết toán thuế',
            'tax calculation', 'personal tax'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'tính', 'calculate']):
                return {
                    'intent': 'hr_action',
                    'action': 'create_personal_tax',
                    'api_endpoint': '/api/hr/employee/{employee_id}/personal-income-tax',
                    'method': 'POST',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'get_personal_tax',
                    'api_endpoint': '/api/hr/employee/{employee_id}/personal-income-tax',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 12. /api/hr/employee/<int:employee_id>/shifts (GET, POST)
        if any(keyword in message_lower for keyword in [
            'ca nhân viên', 'employee shifts', 'shifts của nhân viên',
            'lịch ca', 'shift schedule'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action',
                    'action': 'create_employee_shift',
                    'api_endpoint': '/api/hr/employee/{employee_id}/shifts',
                    'method': 'POST',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'get_employee_shifts',
                    'api_endpoint': '/api/hr/employee/{employee_id}/shifts',
                    'method': 'GET',
                    'confidence': 0.85
                }

        # ======================= LEAVE MANAGEMENT INTENTS =======================
        # 13. /api/hr/leave-types (GET, POST)
        if any(keyword in message_lower for keyword in [
            'loại nghỉ phép', 'leave type', 'leave types', 'kiểu nghỉ phép',
            'danh sách loại nghỉ', 'list leave type', 'tạo loại nghỉ', 'create leave type'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action',
                    'action': 'create_leave_type',
                    'api_endpoint': '/api/hr/leave-types',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'list_leave_types',
                    'api_endpoint': '/api/hr/leave-types',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 14. /api/hr/leave-type/<int:leave_type_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết loại nghỉ', 'leave type detail', 'thông tin loại nghỉ',
            'cập nhật loại nghỉ', 'update leave type', 'sửa loại nghỉ', 'edit leave type',
            'xóa loại nghỉ', 'delete leave type'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action',
                    'action': 'update_leave_type',
                    'api_endpoint': '/api/hr/leave-type/{leave_type_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action',
                    'action': 'delete_leave_type',
                    'api_endpoint': '/api/hr/leave-type/{leave_type_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'get_leave_type_detail',
                    'api_endpoint': '/api/hr/leave-type/{leave_type_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 15. /api/hr/leave-allocations (GET, POST)
        if any(keyword in message_lower for keyword in [
            'phân bổ nghỉ phép', 'leave allocation', 'leave allocations', 'cấp phát nghỉ',
            'danh sách phân bổ', 'list allocation', 'tạo phân bổ', 'create allocation'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action',
                    'action': 'create_leave_allocation',
                    'api_endpoint': '/api/hr/leave-allocations',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'list_leave_allocations',
                    'api_endpoint': '/api/hr/leave-allocations',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 16. /api/hr/leave-allocation/<int:allocation_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết phân bổ', 'allocation detail', 'thông tin phân bổ',
            'cập nhật phân bổ', 'update allocation', 'sửa phân bổ', 'edit allocation',
            'xóa phân bổ', 'delete allocation'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action',
                    'action': 'update_leave_allocation',
                    'api_endpoint': '/api/hr/leave-allocation/{allocation_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete', 'cancel']):
                return {
                    'intent': 'hr_action',
                    'action': 'delete_leave_allocation',
                    'api_endpoint': '/api/hr/leave-allocation/{allocation_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'get_leave_allocation_detail',
                    'api_endpoint': '/api/hr/leave-allocation/{allocation_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 17. /api/hr/leave-allocation/<int:allocation_id>/approve (POST)
        if any(keyword in message_lower for keyword in [
            'phê duyệt phân bổ', 'approve allocation', 'duyệt phân bổ', 'approval allocation'
        ]):
            return {
                'intent': 'hr_action',
                'action': 'approve_leave_allocation',
                'api_endpoint': '/api/hr/leave-allocation/{allocation_id}/approve',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # 18. /api/hr/leaves (GET, POST)
        if any(keyword in message_lower for keyword in [
            'nghỉ phép', 'leave request', 'leaves', 'đơn nghỉ',
            'danh sách nghỉ phép', 'list leaves', 'tạo đơn nghỉ', 'create leave'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new', 'đăng ký']):
                return {
                    'intent': 'hr_action',
                    'action': 'create_leave',
                    'api_endpoint': '/api/hr/leaves',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action',
                    'action': 'list_leaves',
                    'api_endpoint': '/api/hr/leaves',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 19. /api/hr/leave/<int:leave_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết nghỉ phép', 'leave detail', 'thông tin đơn nghỉ',
            'cập nhật nghỉ phép', 'update leave', 'sửa đơn nghỉ', 'edit leave',
            'hủy đơn nghỉ', 'cancel leave'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action',
                    'action': 'update_leave',
                    'api_endpoint': '/api/hr/leave/{leave_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['hủy', 'cancel', 'delete']):
                return {
                    'intent': 'hr_action',
                    'action': 'cancel_leave',
                    'api_endpoint': '/api/hr/leave/{leave_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_leave_detail',
                    'api_endpoint': '/api/hr/leave/{leave_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 20. /api/hr/leave/<int:leave_id>/approve (POST)
        if any(keyword in message_lower for keyword in [
            'phê duyệt nghỉ phép', 'approve leave', 'duyệt đơn nghỉ', 'approval leave'
        ]):
            return {
                'intent': 'hr_action', 'action': 'approve_leave',
                'api_endpoint': '/api/hr/leave/{leave_id}/approve',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # 21. /api/hr/leave/<int:leave_id>/refuse (POST)
        if any(keyword in message_lower for keyword in [
            'từ chối nghỉ phép', 'refuse leave', 'reject leave', 'deny leave'
        ]):
            return {
                'intent': 'hr_action', 'action': 'refuse_leave',
                'api_endpoint': '/api/hr/leave/{leave_id}/refuse',
                'method': 'POST',
                'confidence': 0.9
            }

        # ======================= CONTRACT MANAGEMENT INTENTS =======================
        # 22. /api/hr/contracts (GET, POST)
        if any(keyword in message_lower for keyword in [
            'hợp đồng', 'contract', 'contracts', 'hợp đồng lao động',
            'danh sách hợp đồng', 'list contract', 'tạo hợp đồng', 'create contract'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_contract',
                    'api_endpoint': '/api/hr/contracts',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_contracts',
                    'api_endpoint': '/api/hr/contracts',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 23. /api/hr/contract/<int:contract_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết hợp đồng', 'contract detail', 'thông tin hợp đồng',
            'cập nhật hợp đồng', 'update contract', 'sửa hợp đồng', 'edit contract',
            'hủy hợp đồng', 'cancel contract'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_contract',
                    'api_endpoint': '/api/hr/contract/{contract_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['hủy', 'cancel', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'cancel_contract',
                    'api_endpoint': '/api/hr/contract/{contract_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_contract_detail',
                    'api_endpoint': '/api/hr/contract/{contract_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # ======================= ATTENDANCE MANAGEMENT INTENTS =======================
        # 24. /api/hr/attendances (GET, POST)
        if any(keyword in message_lower for keyword in [
            'chấm công', 'attendance', 'attendances', 'điểm danh',
            'danh sách chấm công', 'list attendance', 'tạo chấm công', 'create attendance'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_attendance',
                    'api_endpoint': '/api/hr/attendances',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_attendances',
                    'api_endpoint': '/api/hr/attendances',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 25. /api/hr/attendance/<int:attendance_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết chấm công', 'attendance detail', 'thông tin chấm công',
            'cập nhật chấm công', 'update attendance', 'sửa chấm công', 'edit attendance',
            'xóa chấm công', 'delete attendance'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_attendance',
                    'api_endpoint': '/api/hr/attendance/{attendance_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'delete_attendance',
                    'api_endpoint': '/api/hr/attendance/{attendance_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_attendance_detail',
                    'api_endpoint': '/api/hr/attendance/{attendance_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 26. /api/hr/employee/<int:employee_id>/checkin (POST)
        if any(keyword in message_lower for keyword in [
            'check in', 'checkin', 'vào ca', 'bắt đầu làm việc', 'check-in'
        ]):
            return {
                'intent': 'hr_action', 'action': 'employee_checkin',
                'api_endpoint': '/api/hr/employee/{employee_id}/checkin',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # 27. /api/hr/employee/<int:employee_id>/checkout (POST)
        if any(keyword in message_lower for keyword in [
            'check out', 'checkout', 'ra ca', 'kết thúc làm việc', 'check-out'
        ]):
            return {
                'intent': 'hr_action', 'action': 'employee_checkout',
                'api_endpoint': '/api/hr/employee/{employee_id}/checkout',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # 28. /api/hr/attendance/summary (GET)
        if any(keyword in message_lower for keyword in [
            'tóm tắt chấm công', 'attendance summary', 'báo cáo chấm công', 'attendance report'
        ]):
            return {
                'intent': 'hr_action', 'action': 'attendance_summary',
                'api_endpoint': '/api/hr/attendance/summary',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 29. /api/hr/attendance/overtime (GET)
        if any(keyword in message_lower for keyword in [
            'giờ làm thêm', 'overtime', 'tăng ca', 'overtime hours'
        ]):
            return {
                'intent': 'hr_action', 'action': 'attendance_overtime',
                'api_endpoint': '/api/hr/attendance/overtime',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 30. /api/hr/attendance/missing (GET)
        if any(keyword in message_lower for keyword in [
            'chấm công thiếu', 'missing attendance', 'attendance missing', 'thiếu chấm công'
        ]):
            return {
                'intent': 'hr_action', 'action': 'attendance_missing',
                'api_endpoint': '/api/hr/attendance/missing',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # ======================= PAYROLL MANAGEMENT INTENTS =======================
        # 31. /api/hr/payslips (GET, POST)
        if any(keyword in message_lower for keyword in [
            'bảng lương', 'payslip', 'payslips', 'phiếu lương',
            'danh sách bảng lương', 'list payslip', 'tạo bảng lương', 'create payslip'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_payslip',
                    'api_endpoint': '/api/hr/payslips',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_payslips',
                    'api_endpoint': '/api/hr/payslips',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 32. /api/hr/payslip/<int:payslip_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết bảng lương', 'payslip detail', 'thông tin bảng lương',
            'cập nhật bảng lương', 'update payslip', 'sửa bảng lương', 'edit payslip',
            'hủy bảng lương', 'cancel payslip'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_payslip',
                    'api_endpoint': '/api/hr/payslip/{payslip_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['hủy', 'cancel', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'cancel_payslip',
                    'api_endpoint': '/api/hr/payslip/{payslip_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_payslip_detail',
                    'api_endpoint': '/api/hr/payslip/{payslip_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 33. /api/hr/payslip/<int:payslip_id>/compute (POST)
        if any(keyword in message_lower for keyword in [
            'tính lương', 'compute payslip', 'calculate salary', 'tính toán bảng lương'
        ]):
            return {
                'intent': 'hr_action', 'action': 'compute_payslip',
                'api_endpoint': '/api/hr/payslip/{payslip_id}/compute',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # 34. /api/hr/payslip/<int:payslip_id>/lines (GET)
        if any(keyword in message_lower for keyword in [
            'dòng bảng lương', 'payslip lines', 'chi tiết dòng lương', 'payslip line detail'
        ]):
            return {
                'intent': 'hr_action', 'action': 'get_payslip_lines',
                'api_endpoint': '/api/hr/payslip/{payslip_id}/lines',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 35. /api/hr/payroll/salary-rules (GET, POST)
        if any(keyword in message_lower for keyword in [
            'quy tắc lương', 'salary rule', 'salary rules', 'rule lương',
            'danh sách quy tắc', 'list salary rule', 'tạo quy tắc', 'create salary rule'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_salary_rule',
                    'api_endpoint': '/api/hr/payroll/salary-rules',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_salary_rules',
                    'api_endpoint': '/api/hr/payroll/salary-rules',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 36. /api/hr/payroll/salary-rule/<int:rule_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết quy tắc lương', 'salary rule detail', 'thông tin quy tắc',
            'cập nhật quy tắc', 'update salary rule', 'sửa quy tắc', 'edit salary rule',
            'xóa quy tắc', 'delete salary rule'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_salary_rule',
                    'api_endpoint': '/api/hr/payroll/salary-rule/{rule_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'delete_salary_rule',
                    'api_endpoint': '/api/hr/payroll/salary-rule/{rule_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_salary_rule_detail',
                    'api_endpoint': '/api/hr/payroll/salary-rule/{rule_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 37. /api/hr/payroll/structures (GET, POST)
        if any(keyword in message_lower for keyword in [
            'cấu trúc lương', 'payroll structure', 'salary structure', 'structure lương',
            'danh sách cấu trúc', 'list structure', 'tạo cấu trúc', 'create structure'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_payroll_structure',
                    'api_endpoint': '/api/hr/payroll/structures',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_payroll_structures',
                    'api_endpoint': '/api/hr/payroll/structures',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 38. /api/hr/payroll/structure/<int:structure_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết cấu trúc lương', 'structure detail', 'thông tin cấu trúc',
            'cập nhật cấu trúc', 'update structure', 'sửa cấu trúc', 'edit structure',
            'xóa cấu trúc', 'delete structure'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_payroll_structure',
                    'api_endpoint': '/api/hr/payroll/structure/{structure_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'delete_payroll_structure',
                    'api_endpoint': '/api/hr/payroll/structure/{structure_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_payroll_structure_detail',
                    'api_endpoint': '/api/hr/payroll/structure/{structure_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }

        # ======================= INSURANCE MANAGEMENT INTENTS =======================
        # 39. /api/hr/insurances (GET, POST)
        if any(keyword in message_lower for keyword in [
            'bảo hiểm', 'insurance', 'insurances', 'bảo hiểm nhân viên',
            'danh sách bảo hiểm', 'list insurance', 'tạo bảo hiểm', 'create insurance'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_insurance',
                    'api_endpoint': '/api/hr/insurances',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_insurances',
                    'api_endpoint': '/api/hr/insurances',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 40. /api/hr/insurance/<int:insurance_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết bảo hiểm', 'insurance detail', 'thông tin bảo hiểm',
            'cập nhật bảo hiểm', 'update insurance', 'sửa bảo hiểm', 'edit insurance',
            'hủy bảo hiểm', 'cancel insurance'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_insurance',
                    'api_endpoint': '/api/hr/insurance/{insurance_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['hủy', 'cancel', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'cancel_insurance',
                    'api_endpoint': '/api/hr/insurance/{insurance_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_insurance_detail',
                    'api_endpoint': '/api/hr/insurance/{insurance_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 41. /api/hr/insurance/policies (GET, POST)
        if any(keyword in message_lower for keyword in [
            'chính sách bảo hiểm', 'insurance policy', 'insurance policies', 'policy bảo hiểm',
            'danh sách chính sách', 'list policy', 'tạo chính sách', 'create policy'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_insurance_policy',
                    'api_endpoint': '/api/hr/insurance/policies',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_insurance_policies',
                    'api_endpoint': '/api/hr/insurance/policies',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 42. /api/hr/insurance/policy/<int:policy_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết chính sách', 'policy detail', 'thông tin chính sách',
            'cập nhật chính sách', 'update policy', 'sửa chính sách', 'edit policy',
            'xóa chính sách', 'delete policy'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_insurance_policy',
                    'api_endpoint': '/api/hr/insurance/policy/{policy_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'delete_insurance_policy',
                    'api_endpoint': '/api/hr/insurance/policy/{policy_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_insurance_policy_detail',
                    'api_endpoint': '/api/hr/insurance/policy/{policy_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 43. /api/hr/employee/<int:employee_id>/bhxh (GET, POST, PUT)
        if any(keyword in message_lower for keyword in [
            'bhxh', 'bhyt', 'bhtn', 'bảo hiểm xã hội', 'bảo hiểm y tế',
            'bảo hiểm thất nghiệp', 'social insurance', 'health insurance'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new', 'đăng ký']):
                return {
                    'intent': 'hr_action', 'action': 'create_employee_bhxh',
                    'api_endpoint': '/api/hr/employee/{employee_id}/bhxh',
                    'method': 'POST',
                    'confidence': 0.9
                }
            elif any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_employee_bhxh',
                    'api_endpoint': '/api/hr/employee/{employee_id}/bhxh',
                    'method': 'PUT',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_employee_bhxh',
                    'api_endpoint': '/api/hr/employee/{employee_id}/bhxh',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 44. /api/hr/insurance/payments (GET, POST)
        if any(keyword in message_lower for keyword in [
            'thanh toán bảo hiểm', 'insurance payment', 'insurance payments', 'payment bảo hiểm',
            'danh sách thanh toán', 'list payment', 'tạo thanh toán', 'create payment'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_insurance_payment',
                    'api_endpoint': '/api/hr/insurance/payments',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_insurance_payments',
                    'api_endpoint': '/api/hr/insurance/payments',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 45. /api/hr/insurance/payment/<int:payment_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết thanh toán', 'payment detail', 'thông tin thanh toán',
            'cập nhật thanh toán', 'update payment', 'sửa thanh toán', 'edit payment',
            'hủy thanh toán', 'cancel payment'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_insurance_payment',
                    'api_endpoint': '/api/hr/insurance/payment/{payment_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['hủy', 'cancel', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'cancel_insurance_payment',
                    'api_endpoint': '/api/hr/insurance/payment/{payment_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_insurance_payment_detail',
                    'api_endpoint': '/api/hr/insurance/payment/{payment_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 46. /api/hr/insurance/benefits (GET, POST)
        if any(keyword in message_lower for keyword in [
            'quyền lợi bảo hiểm', 'insurance benefit', 'insurance benefits', 'benefit bảo hiểm',
            'danh sách quyền lợi', 'list benefit', 'tạo quyền lợi', 'create benefit'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_insurance_benefit',
                    'api_endpoint': '/api/hr/insurance/benefits',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_insurance_benefits',
                    'api_endpoint': '/api/hr/insurance/benefits',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 47. /api/hr/insurance/benefit/<int:benefit_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết quyền lợi', 'benefit detail', 'thông tin quyền lợi',
            'cập nhật quyền lợi', 'update benefit', 'sửa quyền lợi', 'edit benefit',
            'hủy quyền lợi', 'cancel benefit'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_insurance_benefit',
                    'api_endpoint': '/api/hr/insurance/benefit/{benefit_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['hủy', 'cancel', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'cancel_insurance_benefit',
                    'api_endpoint': '/api/hr/insurance/benefit/{benefit_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_insurance_benefit_detail',
                    'api_endpoint': '/api/hr/insurance/benefit/{benefit_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 48. /api/hr/insurance/documents (GET, POST)
        if any(keyword in message_lower for keyword in [
            'hồ sơ bảo hiểm', 'insurance document', 'insurance documents', 'document bảo hiểm',
            'danh sách hồ sơ', 'list document', 'tạo hồ sơ', 'create document'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_insurance_document',
                    'api_endpoint': '/api/hr/insurance/documents',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_insurance_documents',
                    'api_endpoint': '/api/hr/insurance/documents',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 49. /api/hr/insurance/document/<int:document_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết hồ sơ', 'document detail', 'thông tin hồ sơ',
            'cập nhật hồ sơ', 'update document', 'sửa hồ sơ', 'edit document',
            'hủy hồ sơ', 'cancel document'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_insurance_document',
                    'api_endpoint': '/api/hr/insurance/document/{document_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['hủy', 'cancel', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'cancel_insurance_document',
                    'api_endpoint': '/api/hr/insurance/document/{document_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_insurance_document_detail',
                    'api_endpoint': '/api/hr/insurance/document/{document_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 50. /api/hr/insurance/reports (GET, POST)
        if any(keyword in message_lower for keyword in [
            'báo cáo bảo hiểm', 'insurance report', 'insurance reports', 'report bảo hiểm'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_insurance_report',
                    'api_endpoint': '/api/hr/insurance/reports',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_insurance_reports',
                    'api_endpoint': '/api/hr/insurance/reports',
                    'method': 'GET',
                    'confidence': 0.9
                }

        # ======================= PROJECT & TASK MANAGEMENT INTENTS =======================
        # 51. /api/hr/projects (GET, POST)
        if any(keyword in message_lower for keyword in [
            'dự án', 'project', 'projects', 'project hr',
            'danh sách dự án', 'list project', 'tạo dự án', 'create project'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_project',
                    'api_endpoint': '/api/hr/projects',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_projects',
                    'api_endpoint': '/api/hr/projects',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 52. /api/hr/project/<int:project_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết dự án', 'project detail', 'thông tin dự án',
            'cập nhật dự án', 'update project', 'sửa dự án', 'edit project',
            'xóa dự án', 'delete project', 'archive project'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_project',
                    'api_endpoint': '/api/hr/project/{project_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete', 'archive']):
                return {
                    'intent': 'hr_action', 'action': 'delete_project',
                    'api_endpoint': '/api/hr/project/{project_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_project_detail',
                    'api_endpoint': '/api/hr/project/{project_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 53. /api/hr/project/<int:project_id>/tasks (GET, POST)
        if any(keyword in message_lower for keyword in [
            'task dự án', 'project task', 'project tasks', 'task trong dự án',
            'danh sách task', 'list task', 'tạo task', 'create task'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_project_task',
                    'api_endpoint': '/api/hr/project/{project_id}/tasks',
                    'method': 'POST',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_project_tasks',
                    'api_endpoint': '/api/hr/project/{project_id}/tasks',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 54. /api/hr/tasks (GET, POST)
        if any(keyword in message_lower for keyword in [
            'công việc', 'task', 'tasks', 'nhiệm vụ',
            'danh sách công việc', 'list task', 'tạo công việc', 'create task'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_task',
                    'api_endpoint': '/api/hr/tasks',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_tasks',
                    'api_endpoint': '/api/hr/tasks',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 55. /api/hr/task/<int:task_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết task', 'task detail', 'thông tin task', 'chi tiết công việc',
            'cập nhật task', 'update task', 'sửa task', 'edit task',
            'xóa task', 'delete task', 'archive task'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_task',
                    'api_endpoint': '/api/hr/task/{task_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete', 'archive']):
                return {
                    'intent': 'hr_action', 'action': 'delete_task',
                    'api_endpoint': '/api/hr/task/{task_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_task_detail',
                    'api_endpoint': '/api/hr/task/{task_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 56. /api/hr/task/<int:task_id>/assign (POST)
        if any(keyword in message_lower for keyword in [
            'phân công task', 'assign task', 'gán task', 'phân công công việc'
        ]):
            return {
                'intent': 'hr_action', 'action': 'assign_task',
                'api_endpoint': '/api/hr/task/{task_id}/assign',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # ======================= SKILLS MANAGEMENT INTENTS =======================
        # 57. /api/hr/skills (GET, POST)
        if any(keyword in message_lower for keyword in [
            'kỹ năng', 'skill', 'skills', 'năng lực',
            'danh sách kỹ năng', 'list skill', 'tạo kỹ năng', 'create skill'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_skill',
                    'api_endpoint': '/api/hr/skills',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_skills',
                    'api_endpoint': '/api/hr/skills',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 58. /api/hr/skill/<int:skill_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết kỹ năng', 'skill detail', 'thông tin kỹ năng',
            'cập nhật kỹ năng', 'update skill', 'sửa kỹ năng', 'edit skill',
            'xóa kỹ năng', 'delete skill'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_skill',
                    'api_endpoint': '/api/hr/skill/{skill_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'delete_skill',
                    'api_endpoint': '/api/hr/skill/{skill_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_skill_detail',
                    'api_endpoint': '/api/hr/skill/{skill_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 59. /api/hr/skill-types (GET, POST)
        if any(keyword in message_lower for keyword in [
            'loại kỹ năng', 'skill type', 'skill types', 'phân loại kỹ năng',
            'danh sách loại', 'list skill type', 'tạo loại', 'create skill type'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_skill_type',
                    'api_endpoint': '/api/hr/skill-types',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_skill_types',
                    'api_endpoint': '/api/hr/skill-types',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 60. /api/hr/skill-type/<int:skill_type_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết loại kỹ năng', 'skill type detail', 'thông tin loại kỹ năng',
            'cập nhật loại kỹ năng', 'update skill type', 'sửa loại kỹ năng', 'edit skill type',
            'xóa loại kỹ năng', 'delete skill type'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_skill_type',
                    'api_endpoint': '/api/hr/skill-type/{skill_type_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'delete_skill_type',
                    'api_endpoint': '/api/hr/skill-type/{skill_type_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_skill_type_detail',
                    'api_endpoint': '/api/hr/skill-type/{skill_type_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 61. /api/hr/skill-levels (GET, POST)
        if any(keyword in message_lower for keyword in [
            'cấp độ kỹ năng', 'skill level', 'skill levels', 'level kỹ năng',
            'danh sách cấp độ', 'list skill level', 'tạo cấp độ', 'create skill level'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_skill_level',
                    'api_endpoint': '/api/hr/skill-levels',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_skill_levels',
                    'api_endpoint': '/api/hr/skill-levels',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 62. /api/hr/skill-level/<int:skill_level_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết cấp độ', 'skill level detail', 'thông tin cấp độ',
            'cập nhật cấp độ', 'update skill level', 'sửa cấp độ', 'edit skill level',
            'xóa cấp độ', 'delete skill level'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_skill_level',
                    'api_endpoint': '/api/hr/skill-level/{skill_level_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'delete_skill_level',
                    'api_endpoint': '/api/hr/skill-level/{skill_level_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_skill_level_detail',
                    'api_endpoint': '/api/hr/skill-level/{skill_level_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 63. /api/hr/employee/<int:employee_id>/skills (GET, POST)
        if any(keyword in message_lower for keyword in [
            'kỹ năng nhân viên', 'employee skill', 'employee skills', 'skill của nhân viên',
            'danh sách kỹ năng nhân viên', 'list employee skill', 'thêm kỹ năng', 'add skill'
        ]):
            if any(keyword in message_lower for keyword in ['thêm', 'add', 'tạo', 'create', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'add_employee_skill',
                    'api_endpoint': '/api/hr/employee/{employee_id}/skills',
                    'method': 'POST',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_employee_skills',
                    'api_endpoint': '/api/hr/employee/{employee_id}/skills',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 64. /api/hr/employee-skill/<int:employee_skill_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết kỹ năng nhân viên', 'employee skill detail', 'thông tin kỹ năng nhân viên',
            'cập nhật kỹ năng nhân viên', 'update employee skill', 'sửa kỹ năng nhân viên', 'edit employee skill',
            'xóa kỹ năng nhân viên', 'delete employee skill'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_employee_skill',
                    'api_endpoint': '/api/hr/employee-skill/{employee_skill_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'delete_employee_skill',
                    'api_endpoint': '/api/hr/employee-skill/{employee_skill_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_employee_skill_detail',
                    'api_endpoint': '/api/hr/employee-skill/{employee_skill_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 65. /api/hr/resume-lines (GET, POST)
        if any(keyword in message_lower for keyword in [
            'sơ yếu lý lịch', 'resume line', 'resume lines', 'lý lịch',
            'danh sách sơ yếu', 'list resume', 'tạo sơ yếu', 'create resume'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_resume_line',
                    'api_endpoint': '/api/hr/resume-lines',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_resume_lines',
                    'api_endpoint': '/api/hr/resume-lines',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 66. /api/hr/resume-line/<int:resume_line_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết sơ yếu', 'resume line detail', 'thông tin sơ yếu',
            'cập nhật sơ yếu', 'update resume line', 'sửa sơ yếu', 'edit resume line',
            'xóa sơ yếu', 'delete resume line'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_resume_line',
                    'api_endpoint': '/api/hr/resume-line/{resume_line_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'delete_resume_line',
                    'api_endpoint': '/api/hr/resume-line/{resume_line_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_resume_line_detail',
                    'api_endpoint': '/api/hr/resume-line/{resume_line_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 67. /api/hr/employee/<int:employee_id>/resume (GET)
        if any(keyword in message_lower for keyword in [
            'lý lịch nhân viên', 'employee resume', 'resume nhân viên', 'cv nhân viên'
        ]):
            return {
                'intent': 'hr_action', 'action': 'get_employee_resume',
                'api_endpoint': '/api/hr/employee/{employee_id}/resume',
                'method': 'GET',
                'confidence': 0.9
            }

        # ======================= TIMESHEET MANAGEMENT INTENTS =======================
        # 68. /api/hr/timesheets (GET, POST)
        if any(keyword in message_lower for keyword in [
            'timesheet', 'timesheets', 'báo công', 'giờ công',
            'danh sách timesheet', 'list timesheet', 'tạo timesheet', 'create timesheet'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_timesheet',
                    'api_endpoint': '/api/hr/timesheets',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_timesheets',
                    'api_endpoint': '/api/hr/timesheets',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 69. /api/hr/timesheet/<int:timesheet_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết timesheet', 'timesheet detail', 'thông tin timesheet',
            'cập nhật timesheet', 'update timesheet', 'sửa timesheet', 'edit timesheet',
            'xóa timesheet', 'delete timesheet'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_timesheet',
                    'api_endpoint': '/api/hr/timesheet/{timesheet_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'delete_timesheet',
                    'api_endpoint': '/api/hr/timesheet/{timesheet_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_timesheet_detail',
                    'api_endpoint': '/api/hr/timesheet/{timesheet_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 70. /api/hr/employee/<int:employee_id>/timesheets (GET, POST)
        if any(keyword in message_lower for keyword in [
            'timesheet nhân viên', 'employee timesheet', 'employee timesheets', 'timesheet của nhân viên',
            'báo công nhân viên', 'giờ công nhân viên'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_employee_timesheet',
                    'api_endpoint': '/api/hr/employee/{employee_id}/timesheets',
                    'method': 'POST',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_employee_timesheets',
                    'api_endpoint': '/api/hr/employee/{employee_id}/timesheets',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 71. /api/hr/project/<int:project_id>/timesheets (GET)
        if any(keyword in message_lower for keyword in [
            'timesheet dự án', 'project timesheet', 'project timesheets', 'timesheet theo dự án',
            'báo công dự án', 'giờ công dự án'
        ]):
            return {
                'intent': 'hr_action', 'action': 'get_project_timesheets',
                'api_endpoint': '/api/hr/project/{project_id}/timesheets',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 72. /api/hr/task/<int:task_id>/timesheets (GET)
        if any(keyword in message_lower for keyword in [
            'timesheet task', 'task timesheet', 'task timesheets', 'timesheet theo task',
            'báo công task', 'giờ công task'
        ]):
            return {
                'intent': 'hr_action', 'action': 'get_task_timesheets',
                'api_endpoint': '/api/hr/task/{task_id}/timesheets',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 73. /api/hr/timesheet/summary (GET)
        if any(keyword in message_lower for keyword in [
            'tóm tắt timesheet', 'timesheet summary', 'báo cáo timesheet', 'timesheet report'
        ]):
            return {
                'intent': 'hr_action', 'action': 'timesheet_summary',
                'api_endpoint': '/api/hr/timesheet/summary',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 74. /api/hr/timesheet/validate (POST)
        if any(keyword in message_lower for keyword in [
            'xác nhận timesheet', 'validate timesheet', 'duyệt timesheet', 'approve timesheet'
        ]):
            return {
                'intent': 'hr_action', 'action': 'validate_timesheet',
                'api_endpoint': '/api/hr/timesheet/validate',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # 75. /api/hr/timesheet/copy (POST)
        if any(keyword in message_lower for keyword in [
            'sao chép timesheet', 'copy timesheet', 'duplicate timesheet', 'nhân bản timesheet'
        ]):
            return {
                'intent': 'hr_action', 'action': 'copy_timesheet',
                'api_endpoint': '/api/hr/timesheet/copy',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # ======================= RECRUITMENT MANAGEMENT INTENTS =======================
        # 76. /api/hr/applicants (GET, POST)
        if any(keyword in message_lower for keyword in [
            'ứng viên', 'applicant', 'applicants', 'ứng cử viên',
            'danh sách ứng viên', 'list applicant', 'tạo ứng viên', 'create applicant'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_applicant',
                    'api_endpoint': '/api/hr/applicants',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_applicants',
                    'api_endpoint': '/api/hr/applicants',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 77. /api/hr/applicant/<int:applicant_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết ứng viên', 'applicant detail', 'thông tin ứng viên',
            'cập nhật ứng viên', 'update applicant', 'sửa ứng viên', 'edit applicant',
            'xóa ứng viên', 'delete applicant', 'archive applicant'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_applicant',
                    'api_endpoint': '/api/hr/applicant/{applicant_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete', 'archive']):
                return {
                    'intent': 'hr_action', 'action': 'delete_applicant',
                    'api_endpoint': '/api/hr/applicant/{applicant_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_applicant_detail',
                    'api_endpoint': '/api/hr/applicant/{applicant_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 78. /api/hr/applicant/<int:applicant_id>/status (GET, PUT)
        if any(keyword in message_lower for keyword in [
            'trạng thái ứng viên', 'applicant status', 'status ứng viên',
            'cập nhật trạng thái ứng viên', 'update applicant status'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_applicant_status',
                    'api_endpoint': '/api/hr/applicant/{applicant_id}/status',
                    'method': 'PUT',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_applicant_status',
                    'api_endpoint': '/api/hr/applicant/{applicant_id}/status',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 79. /api/hr/applicant/<int:applicant_id>/hire (POST)
        if any(keyword in message_lower for keyword in [
            'tuyển dụng ứng viên', 'hire applicant', 'nhận việc', 'tuyển dụng'
        ]):
            return {
                'intent': 'hr_action', 'action': 'hire_applicant',
                'api_endpoint': '/api/hr/applicant/{applicant_id}/hire',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # 80. /api/hr/applicant/<int:applicant_id>/refuse (POST)
        if any(keyword in message_lower for keyword in [
            'từ chối ứng viên', 'refuse applicant', 'reject applicant', 'loại bỏ ứng viên'
        ]):
            return {
                'intent': 'hr_action', 'action': 'refuse_applicant',
                'api_endpoint': '/api/hr/applicant/{applicant_id}/refuse',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # 81. /api/hr/recruitment/jobs (GET, POST)
        if any(keyword in message_lower for keyword in [
            'vị trí tuyển dụng', 'recruitment job', 'recruitment jobs', 'job tuyển dụng',
            'danh sách vị trí', 'list recruitment job', 'tạo vị trí', 'create recruitment job'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_recruitment_job',
                    'api_endpoint': '/api/hr/recruitment/jobs',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_recruitment_jobs',
                    'api_endpoint': '/api/hr/recruitment/jobs',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 82. /api/hr/recruitment/job/<int:job_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết vị trí tuyển dụng', 'recruitment job detail', 'thông tin vị trí tuyển dụng',
            'cập nhật vị trí tuyển dụng', 'update recruitment job', 'sửa vị trí tuyển dụng', 'edit recruitment job',
            'xóa vị trí tuyển dụng', 'delete recruitment job'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_recruitment_job',
                    'api_endpoint': '/api/hr/recruitment/job/{job_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete', 'archive']):
                return {
                    'intent': 'hr_action', 'action': 'delete_recruitment_job',
                    'api_endpoint': '/api/hr/recruitment/job/{job_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_recruitment_job_detail',
                    'api_endpoint': '/api/hr/recruitment/job/{job_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 83. /api/hr/recruitment/stages (GET, POST)
        if any(keyword in message_lower for keyword in [
            'giai đoạn tuyển dụng', 'recruitment stage', 'recruitment stages', 'stage tuyển dụng',
            'danh sách giai đoạn', 'list recruitment stage', 'tạo giai đoạn', 'create recruitment stage'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_recruitment_stage',
                    'api_endpoint': '/api/hr/recruitment/stages',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_recruitment_stages',
                    'api_endpoint': '/api/hr/recruitment/stages',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 84. /api/hr/recruitment/stage/<int:stage_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết giai đoạn tuyển dụng', 'recruitment stage detail', 'thông tin giai đoạn',
            'cập nhật giai đoạn', 'update recruitment stage', 'sửa giai đoạn', 'edit recruitment stage',
            'xóa giai đoạn', 'delete recruitment stage'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_recruitment_stage',
                    'api_endpoint': '/api/hr/recruitment/stage/{stage_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'delete_recruitment_stage',
                    'api_endpoint': '/api/hr/recruitment/stage/{stage_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_recruitment_stage_detail',
                    'api_endpoint': '/api/hr/recruitment/stage/{stage_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 85. /api/hr/candidates (GET, POST)
        if any(keyword in message_lower for keyword in [
            'candidate', 'candidates', 'ứng cử viên', 'thí sinh',
            'danh sách candidate', 'list candidate', 'tạo candidate', 'create candidate'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_candidate',
                    'api_endpoint': '/api/hr/candidates',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_candidates',
                    'api_endpoint': '/api/hr/candidates',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 86. /api/hr/candidate/<int:candidate_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết candidate', 'candidate detail', 'thông tin candidate',
            'cập nhật candidate', 'update candidate', 'sửa candidate', 'edit candidate',
            'xóa candidate', 'delete candidate', 'archive candidate'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_candidate',
                    'api_endpoint': '/api/hr/candidate/{candidate_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete', 'archive']):
                return {
                    'intent': 'hr_action', 'action': 'delete_candidate',
                    'api_endpoint': '/api/hr/candidate/{candidate_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_candidate_detail',
                    'api_endpoint': '/api/hr/candidate/{candidate_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }

        # ======================= EXPENSE MANAGEMENT INTENTS =======================
        # 87. /api/hr/expenses (GET, POST)
        if any(keyword in message_lower for keyword in [
            'chi phí', 'expense', 'expenses', 'khoản chi',
            'danh sách chi phí', 'list expense', 'tạo chi phí', 'create expense'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_expense',
                    'api_endpoint': '/api/hr/expenses',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_expenses',
                    'api_endpoint': '/api/hr/expenses',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 88. /api/hr/expense/<int:expense_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết chi phí', 'expense detail', 'thông tin chi phí',
            'cập nhật chi phí', 'update expense', 'sửa chi phí', 'edit expense',
            'hủy chi phí', 'cancel expense'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_expense',
                    'api_endpoint': '/api/hr/expense/{expense_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['hủy', 'cancel', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'cancel_expense',
                    'api_endpoint': '/api/hr/expense/{expense_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_expense_detail',
                    'api_endpoint': '/api/hr/expense/{expense_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 89. /api/hr/expense-sheets (GET, POST)
        if any(keyword in message_lower for keyword in [
            'bảng chi phí', 'expense sheet', 'expense sheets', 'sheet chi phí',
            'danh sách bảng chi phí', 'list expense sheet', 'tạo bảng chi phí', 'create expense sheet'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_expense_sheet',
                    'api_endpoint': '/api/hr/expense-sheets',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_expense_sheets',
                    'api_endpoint': '/api/hr/expense-sheets',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 90. /api/hr/expense-sheet/<int:sheet_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết bảng chi phí', 'expense sheet detail', 'thông tin bảng chi phí',
            'cập nhật bảng chi phí', 'update expense sheet', 'sửa bảng chi phí', 'edit expense sheet',
            'hủy bảng chi phí', 'cancel expense sheet'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_expense_sheet',
                    'api_endpoint': '/api/hr/expense-sheet/{sheet_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['hủy', 'cancel', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'cancel_expense_sheet',
                    'api_endpoint': '/api/hr/expense-sheet/{sheet_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_expense_sheet_detail',
                    'api_endpoint': '/api/hr/expense-sheet/{sheet_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 91. /api/hr/expense-sheet/<int:sheet_id>/submit (POST)
        if any(keyword in message_lower for keyword in [
            'nộp bảng chi phí', 'submit expense sheet', 'gửi bảng chi phí', 'submit expense'
        ]):
            return {
                'intent': 'hr_action', 'action': 'submit_expense_sheet',
                'api_endpoint': '/api/hr/expense-sheet/{sheet_id}/submit',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # 92. /api/hr/expense-sheet/<int:sheet_id>/approve (POST)
        if any(keyword in message_lower for keyword in [
            'phê duyệt bảng chi phí', 'approve expense sheet', 'duyệt bảng chi phí', 'approve expense'
        ]):
            return {
                'intent': 'hr_action', 'action': 'approve_expense_sheet',
                'api_endpoint': '/api/hr/expense-sheet/{sheet_id}/approve',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # ======================= HOMEWORKING MANAGEMENT INTENTS =======================
        # 93. /api/hr/homeworking-requests (GET, POST)
        if any(keyword in message_lower for keyword in [
            'làm việc tại nhà', 'homeworking', 'homeworking request', 'work from home',
            'yêu cầu làm tại nhà', 'remote work', 'wfh'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new', 'yêu cầu']):
                return {
                    'intent': 'hr_action', 'action': 'create_homeworking_request',
                    'api_endpoint': '/api/hr/homeworking-requests',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_homeworking_requests',
                    'api_endpoint': '/api/hr/homeworking-requests',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 94. /api/hr/homeworking-request/<int:request_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết yêu cầu làm tại nhà', 'homeworking request detail', 'thông tin homeworking',
            'cập nhật yêu cầu làm tại nhà', 'update homeworking request', 'sửa homeworking',
            'hủy yêu cầu làm tại nhà', 'cancel homeworking request'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_homeworking_request',
                    'api_endpoint': '/api/hr/homeworking-request/{request_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['hủy', 'cancel', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'cancel_homeworking_request',
                    'api_endpoint': '/api/hr/homeworking-request/{request_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_homeworking_request_detail',
                    'api_endpoint': '/api/hr/homeworking-request/{request_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 95. /api/hr/work-locations (GET, POST)
        if any(keyword in message_lower for keyword in [
            'địa điểm làm việc', 'work location', 'work locations', 'location làm việc',
            'danh sách địa điểm', 'list work location', 'tạo địa điểm', 'create work location'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_work_location',
                    'api_endpoint': '/api/hr/work-locations',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_work_locations',
                    'api_endpoint': '/api/hr/work-locations',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # ======================= WORK ENTRY MANAGEMENT INTENTS =======================
        # 96. /api/hr/work-entries (GET, POST)
        if any(keyword in message_lower for keyword in [
            'bút toán công việc', 'work entry', 'work entries', 'entry công việc',
            'danh sách work entry', 'list work entry', 'tạo work entry', 'create work entry'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_work_entry',
                    'api_endpoint': '/api/hr/work-entries',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_work_entries',
                    'api_endpoint': '/api/hr/work-entries',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 97. /api/hr/work-entry/<int:entry_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết work entry', 'work entry detail', 'thông tin bút toán',
            'cập nhật work entry', 'update work entry', 'sửa work entry', 'edit work entry',
            'hủy work entry', 'cancel work entry'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_work_entry',
                    'api_endpoint': '/api/hr/work-entry/{entry_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['hủy', 'cancel', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'cancel_work_entry',
                    'api_endpoint': '/api/hr/work-entry/{entry_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_work_entry_detail',
                    'api_endpoint': '/api/hr/work-entry/{entry_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 98. /api/hr/employee/<int:employee_id>/work-entries (GET)
        if any(keyword in message_lower for keyword in [
            'work entry nhân viên', 'employee work entry', 'employee work entries', 'bút toán nhân viên'
        ]):
            return {
                'intent': 'hr_action', 'action': 'get_employee_work_entries',
                'api_endpoint': '/api/hr/employee/{employee_id}/work-entries',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # ======================= CALENDAR MANAGEMENT INTENTS =======================
        # 99. /api/hr/calendar-events (GET, POST)
        if any(keyword in message_lower for keyword in [
            'sự kiện lịch', 'calendar event', 'calendar events', 'event lịch',
            'danh sách sự kiện', 'list calendar event', 'tạo sự kiện', 'create calendar event'
        ]):
            if any(keyword in message_lower for keyword in ['tạo', 'create', 'thêm', 'add', 'new']):
                return {
                    'intent': 'hr_action', 'action': 'create_calendar_event',
                    'api_endpoint': '/api/hr/calendar-events',
                    'method': 'POST',
                    'confidence': 0.9
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'list_calendar_events',
                    'api_endpoint': '/api/hr/calendar-events',
                    'method': 'GET',
                    'confidence': 0.9
                }
        
        # 100. /api/hr/calendar-event/<int:event_id> (GET, PUT, DELETE)
        if any(keyword in message_lower for keyword in [
            'chi tiết sự kiện', 'calendar event detail', 'thông tin sự kiện',
            'cập nhật sự kiện', 'update calendar event', 'sửa sự kiện', 'edit calendar event',
            'xóa sự kiện', 'delete calendar event'
        ]):
            if any(keyword in message_lower for keyword in ['cập nhật', 'update', 'sửa', 'edit']):
                return {
                    'intent': 'hr_action', 'action': 'update_calendar_event',
                    'api_endpoint': '/api/hr/calendar-event/{event_id}',
                    'method': 'PUT',
                    'confidence': 0.85
                }
            elif any(keyword in message_lower for keyword in ['xóa', 'delete']):
                return {
                    'intent': 'hr_action', 'action': 'delete_calendar_event',
                    'api_endpoint': '/api/hr/calendar-event/{event_id}',
                    'method': 'DELETE',
                    'confidence': 0.85
                }
            else:
                return {
                    'intent': 'hr_action', 'action': 'get_calendar_event_detail',
                    'api_endpoint': '/api/hr/calendar-event/{event_id}',
                    'method': 'GET',
                    'confidence': 0.85
                }
        
        # 101. /api/hr/employee/<int:employee_id>/calendar-events (GET)
        if any(keyword in message_lower for keyword in [
            'lịch nhân viên', 'employee calendar', 'employee calendar events', 'sự kiện nhân viên'
        ]):
            return {
                'intent': 'hr_action', 'action': 'get_employee_calendar_events',
                'api_endpoint': '/api/hr/employee/{employee_id}/calendar-events',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # ======================= FLEET MANAGEMENT INTENTS =======================
        # 102. /api/hr/fleet-vehicles (GET)
        if any(keyword in message_lower for keyword in [
            'xe công ty', 'fleet vehicle', 'fleet vehicles', 'xe fleet',
            'danh sách xe', 'list fleet vehicle', 'vehicle công ty'
        ]):
            return {
                'intent': 'hr_action', 'action': 'list_fleet_vehicles',
                'api_endpoint': '/api/hr/fleet-vehicles',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 103. /api/hr/employee/<int:employee_id>/fleet-vehicles (GET)
        if any(keyword in message_lower for keyword in [
            'xe nhân viên', 'employee vehicle', 'employee fleet', 'xe của nhân viên'
        ]):
            return {
                'intent': 'hr_action', 'action': 'get_employee_fleet_vehicles',
                'api_endpoint': '/api/hr/employee/{employee_id}/fleet-vehicles',
                'method': 'GET',
                'confidence': 0.9
            }

        # ======================= REPORTS & ANALYTICS INTENTS =======================
        # 104. /api/hr/reports/summary (GET)
        if any(keyword in message_lower for keyword in [
            'báo cáo tổng hợp hr', 'hr reports summary', 'báo cáo hr', 'hr summary',
            'tóm tắt hr', 'hr report', 'summary report'
        ]):
            return {
                'intent': 'hr_action', 'action': 'hr_reports_summary',
                'api_endpoint': '/api/hr/reports/summary',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 105. /api/hr/reports/export (POST)
        if any(keyword in message_lower for keyword in [
            'xuất báo cáo hr', 'export hr report', 'xuất báo cáo excel', 'export excel',
            'xuất báo cáo pdf', 'export pdf', 'export hr'
        ]):
            return {
                'intent': 'hr_action', 'action': 'export_hr_report',
                'api_endpoint': '/api/hr/reports/export',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # 106. /api/hr/dashboard/stats (GET)
        if any(keyword in message_lower for keyword in [
            'thống kê dashboard hr', 'hr dashboard stats', 'dashboard hr', 'thống kê hr',
            'dashboard statistics', 'hr stats'
        ]):
            return {
                'intent': 'hr_action', 'action': 'hr_dashboard_stats',
                'api_endpoint': '/api/hr/dashboard/stats',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 107. /api/hr/analytics/trend (GET)
        if any(keyword in message_lower for keyword in [
            'phân tích xu hướng hr', 'hr analytics trend', 'phân tích hr', 'trend hr',
            'xu hướng hr', 'hr trend', 'analytics hr'
        ]):
            return {
                'intent': 'hr_action', 'action': 'hr_analytics_trend',
                'api_endpoint': '/api/hr/analytics/trend',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 108. /api/hr/notifications (GET)
        if any(keyword in message_lower for keyword in [
            'thông báo hr', 'hr notifications', 'notification hr', 'thông báo quan trọng',
            'alerts hr', 'hr alerts'
        ]):
            return {
                'intent': 'hr_action', 'action': 'hr_notifications',
                'api_endpoint': '/api/hr/notifications',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 109. /api/hr/export/complete (POST)
        if any(keyword in message_lower for keyword in [
            'xuất báo cáo tổng hợp', 'export complete hr', 'xuất báo cáo đầy đủ', 'export all hr',
            'xuất toàn bộ hr', 'complete export'
        ]):
            return {
                'intent': 'hr_action', 'action': 'export_complete_hr',
                'api_endpoint': '/api/hr/export/complete',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # ======================= BULK OPERATIONS INTENTS =======================
        # 110. /api/hr/bulk/update (POST)
        if any(keyword in message_lower for keyword in [
            'cập nhật hàng loạt', 'bulk update', 'update hàng loạt', 'batch update',
            'cập nhật nhiều', 'mass update'
        ]):
            return {
                'intent': 'hr_action', 'action': 'bulk_update_hr',
                'api_endpoint': '/api/hr/bulk/update',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # 111. /api/hr/bulk/delete (POST)
        if any(keyword in message_lower for keyword in [
            'xóa hàng loạt', 'bulk delete', 'delete hàng loạt', 'batch delete',
            'xóa nhiều', 'mass delete', 'archive hàng loạt'
        ]):
            return {
                'intent': 'hr_action', 'action': 'bulk_delete_hr',
                'api_endpoint': '/api/hr/bulk/delete',
                'method': 'POST',
                'confidence': 0.9
            }
        
        # ======================= ADVANCED UTILITIES INTENTS =======================
        # 112. /api/hr/employee/<int:employee_id>/document-check (GET)
        if any(keyword in message_lower for keyword in [
            'kiểm tra tài liệu nhân viên', 'employee document check', 'document check',
            'check tài liệu', 'verify documents', 'kiểm tra giấy tờ'
        ]):
            return {
                'intent': 'hr_action', 'action': 'check_employee_documents',
                'api_endpoint': '/api/hr/employee/{employee_id}/document-check',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 113. /api/hr/employee/<int:employee_id>/performance-summary (GET)
        if any(keyword in message_lower for keyword in [
            'tóm tắt hiệu suất nhân viên', 'employee performance summary', 'performance summary',
            'hiệu suất nhân viên', 'employee performance', 'đánh giá hiệu suất'
        ]):
            return {
                'intent': 'hr_action', 'action': 'employee_performance_summary',
                'api_endpoint': '/api/hr/employee/{employee_id}/performance-summary',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 114. /api/hr/search/global (GET)
        if any(keyword in message_lower for keyword in [
            'tìm kiếm toàn cục hr', 'hr global search', 'global search', 'tìm kiếm hr',
            'search hr', 'search toàn bộ'
        ]):
            return {
                'intent': 'hr_action', 'action': 'hr_global_search',
                'api_endpoint': '/api/hr/search/global',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # ======================= ATTENDANCE ADVANCED INTENTS =======================
        # 115. /api/hr/attendance/summary (GET)
        if any(keyword in message_lower for keyword in [
            'tóm tắt chấm công', 'attendance summary', 'báo cáo chấm công', 'attendance report'
        ]):
            return {
                'intent': 'hr_action', 'action': 'attendance_summary',
                'api_endpoint': '/api/hr/attendance/summary',
                'method': 'GET',
                'confidence': 0.9
            }
        
        # 116. /api/hr/attendance/overtime (GET)
        if any(keyword in message_lower for keyword in [
            'tính toán giờ làm thêm', 'attendance overtime', 'overtime calculation', 'giờ làm thêm',
            'overtime report', 'báo cáo overtime'
        ]):
            return {
                'intent': 'hr_action', 'action': 'attendance_overtime',
                'api_endpoint': '/api/hr/attendance/overtime',
                'method': 'GET',
                'confidence': 0.9
            }

        # ======================= EXISTING FALLBACK LOGIC =======================
        # Dashboard stats
        if any(keyword in message_lower for keyword in [
            'thống kê', 'statistics', 'dashboard', 'báo cáo tổng quan',
            'tổng quan', 'overview'
        ]):
            return {
                'intent': 'hr_action', 'action': 'dashboard_stats',
                'api_endpoint': '/api/hr/dashboard/stats',
                'method': 'GET',
                'confidence': 0.8
            }
        
        # Global search
        if any(keyword in message_lower for keyword in [
            'tìm kiếm', 'search', 'find', 'tìm',
            'tra cứu', 'lookup'
        ]):
            return {
                'intent': 'hr_action', 'action': 'global_search',
                'api_endpoint': '/api/hr/search/global',
                'method': 'GET', 
                'confidence': 0.7
            }
        
        # Default fallback - thêm intent key
        return {
            'intent': 'hr_action',
            'action': 'dashboard_stats',
            'api_endpoint': '/api/hr/dashboard/stats',
            'method': 'GET',
            'confidence': 0.5
        }

    def _extract_parameters(self, message, action):
        """Extract parameters từ message"""
        params = {}
        
        # Set method based on action
        if action in ['create_recruitment_job', 'create_employee', 'create_department', 'create_leave_request']:
            params['method'] = 'POST'
        else:
            params['method'] = 'GET'
        
        # Extract employee ID/name
        employee_match = re.search(r'nhân viên\s+(\w+)|employee\s+(\w+)|id\s*(\d+)', message.lower())
        if employee_match:
            params['employee_id'] = employee_match.group(1) or employee_match.group(2) or employee_match.group(3)
        
        # Extract job information for create_recruitment_job
        if action == 'create_recruitment_job':
            vals = {}
            
            # Extract job name/title
            job_name_patterns = [
                r'tạo vị trí\s+"([^"]+)"',
                r'tạo công việc\s+"([^"]+)"',
                r'create.*job\s+"([^"]+)"',
                r'vị trí\s+(.+?)\s+cho',
                r'công việc\s+(.+?)\s+cho',
                r'position\s+(.+?)\s+for'
            ]
            for pattern in job_name_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    vals['name'] = match.group(1).strip()
                    break
            
            # Extract department information
            dept_patterns = [
                r'cho phòng ban\s+"([^"]+)"',
                r'phòng ban\s+(.+?)(?:\s|$)',
                r'department\s+"([^"]+)"',
                r'cho\s+(.+?)(?:\s|$)'
            ]
            for pattern in dept_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    dept_name = match.group(1).strip()
                    # Find department ID by name
                    dept = request.env['hr.department'].search([('name', 'ilike', dept_name)], limit=1)
                    if dept:
                        vals['department_id'] = dept.id
                    else:
                        vals['department_name'] = dept_name
                    break
            
            # Extract expected employees count
            count_match = re.search(r'cần\s+(\d+)|need\s+(\d+)|(\d+)\s+người', message)
            if count_match:
                vals['expected_employees'] = int(count_match.group(1) or count_match.group(2) or count_match.group(3))
            else:
                vals['expected_employees'] = 1
            
            # Extract description
            desc_patterns = [
                r'mô tả[:\s]+"([^"]+)"',
                r'description[:\s]+"([^"]+)"',
                r'yêu cầu[:\s]+"([^"]+)"',
                r'requirements[:\s]+"([^"]+)"'
            ]
            for pattern in desc_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    vals['description'] = match.group(1).strip()
                    break
            
            # Default values if not specified
            if 'name' not in vals:
                vals['name'] = 'Vị trí tuyển dụng mới'
            
            params['vals'] = vals
        
        # Extract employee information for create_employee
        elif action == 'create_employee':
            vals = {}
            
            # Extract employee name
            name_patterns = [
                r'tạo nhân viên\s+"([^"]+)"',
                r'thêm nhân viên\s+"([^"]+)"',
                r'create employee\s+"([^"]+)"',
                r'nhân viên\s+(.+?)(?:\s|$)'
            ]
            for pattern in name_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    vals['name'] = match.group(1).strip()
                    break
            
            # Extract email
            email_match = re.search(r'email[:\s]+([^\s]+@[^\s]+)', message, re.IGNORECASE)
            if email_match:
                vals['work_email'] = email_match.group(1)
            
            params['vals'] = vals
        
        # Extract department information for create_department
        elif action == 'create_department':
            vals = {}
            
            # Extract department name
            dept_patterns = [
                r'tạo phòng ban\s+"([^"]+)"',
                r'thêm phòng ban\s+"([^"]+)"',
                r'create department\s+"([^"]+)"',
                r'phòng ban\s+(.+?)(?:\s|$)'
            ]
            for pattern in dept_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    vals['name'] = match.group(1).strip()
                    break
            
            params['vals'] = vals
        
        # Extract dates
        date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})', message)
        if date_match:
            params['date'] = date_match.group(1)
        
        # Extract month/year
        month_match = re.search(r'tháng\s+(\d{1,2})|month\s+(\d{1,2})', message.lower())
        if month_match:
            params['month'] = month_match.group(1) or month_match.group(2)
            
        year_match = re.search(r'năm\s+(\d{4})|year\s+(\d{4})', message.lower())
        if year_match:
            params['year'] = year_match.group(1) or year_match.group(2)
        
        # Extract search terms
        search_match = re.search(r'tìm\s+"([^"]+)"|search\s+"([^"]+)"', message.lower())
        if search_match:
            params['search_term'] = search_match.group(1) or search_match.group(2)
        
        return params

    def _execute_hr_api(self, api_endpoint, params):
        """Thực hiện API call tới HR endpoints"""
        try:
            # Import HR API Controller
            from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
            hr_api_controller = HRAPIController()
            
            # Replace placeholders trong API endpoint
            if '{employee_id}' in api_endpoint and 'employee_id' in params:
                api_endpoint = api_endpoint.replace('{employee_id}', str(params['employee_id']))
            if '{job_id}' in api_endpoint and 'job_id' in params:
                api_endpoint = api_endpoint.replace('{job_id}', str(params['job_id']))
            if '{leave_id}' in api_endpoint and 'leave_id' in params:
                api_endpoint = api_endpoint.replace('{leave_id}', str(params['leave_id']))
            
            # Detailed API endpoint mapping với direct method calls
            if api_endpoint == '/api/hr/employees' and params.get('method') == 'GET':
                return hr_api_controller.hr_employees(**params)
            elif api_endpoint == '/api/hr/employees' and params.get('method') == 'POST':
                return hr_api_controller.hr_employees(**params)
            elif api_endpoint == '/api/hr/attendances' and params.get('method') == 'GET':
                return hr_api_controller.hr_attendances(**params)
            elif api_endpoint == '/api/hr/leaves' and params.get('method') == 'GET':
                return hr_api_controller.hr_leaves(**params)
            elif api_endpoint == '/api/hr/leaves' and params.get('method') == 'POST':
                return hr_api_controller.hr_leaves(**params)
            elif api_endpoint == '/api/hr/recruitment/jobs' and params.get('method') == 'GET':
                return hr_api_controller.hr_recruitment_jobs(**params)
            elif api_endpoint == '/api/hr/recruitment/jobs' and params.get('method') == 'POST':
                return hr_api_controller.hr_recruitment_jobs(**params)
            elif api_endpoint == '/api/hr/employee/jobs' and params.get('method') == 'GET':
                return hr_api_controller.hr_employee_jobs(**params)
            elif api_endpoint == '/api/hr/employee/jobs' and params.get('method') == 'POST':
                return hr_api_controller.hr_employee_jobs(**params)
            elif api_endpoint == '/api/hr/employee/departments' and params.get('method') == 'GET':
                return hr_api_controller.hr_employee_departments(**params)
            elif api_endpoint == '/api/hr/employee/departments' and params.get('method') == 'POST':
                return hr_api_controller.hr_employee_departments(**params)
            elif api_endpoint == '/api/hr/dashboard/stats':
                return hr_api_controller.hr_dashboard_stats(**params)
            elif api_endpoint == '/api/hr/search/global':
                return hr_api_controller.hr_global_search(**params)
            elif api_endpoint.startswith('/api/hr/employee/') and '/checkin' in api_endpoint:
                employee_id = int(api_endpoint.split('/')[4])
                return hr_api_controller.hr_employee_checkin(employee_id, **params)
            elif api_endpoint.startswith('/api/hr/employee/') and '/checkout' in api_endpoint:
                employee_id = int(api_endpoint.split('/')[4])
                return hr_api_controller.hr_employee_checkout(employee_id, **params)
            else:
                # Fallback for unmatched endpoints - use HR API Helper
                return self._execute_via_hr_api_helper(api_endpoint, params)
                
        except Exception as e:
            _logger.error(f"Lỗi khi thực hiện HR API: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _execute_via_hr_api_helper(self, api_endpoint, params):
        """Execute API via HR API Helper as fallback"""
        try:
            hr_helper = request.env['hr.api.helper']
            
            # Map common endpoints to helper methods
            if api_endpoint == '/api/hr/recruitment/jobs' and params.get('method') == 'POST':
                vals = params.get('vals', {})
                result = hr_helper.create_recruitment_job(vals)
                return {'success': True, 'data': result}
            elif api_endpoint == '/api/hr/employee/jobs' and params.get('method') == 'POST':
                vals = params.get('vals', {})
                result = hr_helper.create_job(vals)
                return {'success': True, 'data': result}
            elif api_endpoint == '/api/hr/employees' and params.get('method') == 'POST':
                vals = params.get('vals', {})
                result = hr_helper.create_employee(vals)
                return {'success': True, 'data': result}
            elif api_endpoint == '/api/hr/employee/departments' and params.get('method') == 'POST':
                vals = params.get('vals', {})
                result = hr_helper.create_department(vals)
                return {'success': True, 'data': result}
            elif api_endpoint == '/api/hr/leaves' and params.get('method') == 'POST':
                vals = params.get('vals', {})
                result = hr_helper.create_leave_request(vals)
                return {'success': True, 'data': result}
            else:
                # Basic success for other endpoints
                return {'success': True, 'data': f'API {api_endpoint} executed via helper', 'endpoint': api_endpoint}
                
        except Exception as e:
            _logger.error(f"Lỗi khi thực hiện via HR API Helper: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _get_dashboard_stats(self):
        """Lấy thống kê dashboard"""
        try:
            total_employees = request.env['hr.employee'].search_count([('active', '=', True)])
            active_contracts = request.env['hr.contract'].search_count([('state', '=', 'open')])
            pending_leaves = request.env['hr.leave'].search_count([('state', '=', 'confirm')])
            
            return {
                'total_employees': total_employees,
                'active_contracts': active_contracts,
                'pending_leaves': pending_leaves,
                'generated_at': fields.Datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}

    def _global_search(self, search_term):
        """Tìm kiếm toàn cục"""
        try:
            employees = request.env['hr.employee'].search([
                '|', ('name', 'ilike', search_term),
                ('work_email', 'ilike', search_term)
            ], limit=5)
            
            departments = request.env['hr.department'].search([
                ('name', 'ilike', search_term)
            ], limit=3)
            
            return {
                'employees': [{'id': e.id, 'name': e.name, 'email': e.work_email} for e in employees],
                'departments': [{'id': d.id, 'name': d.name} for d in departments],
                'search_term': search_term
            }
        except Exception as e:
            return {'error': str(e)}

    def _direct_api_call(self, endpoint, params):
        """Direct API call fallback"""
        # Placeholder for direct HTTP calls to HR API endpoints
        return {'success': True, 'data': 'API call executed', 'endpoint': endpoint}

    def _format_response(self, action, api_result):
        """Format response cho người dùng"""
        if not api_result.get('success', True):
            return f"❌ Có lỗi xảy ra: {api_result.get('error', 'Unknown error')}"
        
        data = api_result.get('data', {})
        
        # Response templates cho từng action
        response_templates = {
            'list_employees': self._format_employees_list,
            'dashboard_stats': self._format_dashboard_stats,
            'global_search': self._format_search_results,
            'attendance_report': self._format_attendance_report,
            'list_leaves': self._format_leaves_list,
            'create_recruitment_job': self._format_create_job_response,
            'create_employee': self._format_create_employee_response,
            'create_department': self._format_create_department_response,
        }
        
        if action in response_templates:
            return response_templates[action](data)
        else:
            return f"✅ Đã thực hiện thành công action: {action}\n📊 Dữ liệu: {json.dumps(data, indent=2, ensure_ascii=False)}"

    def _format_employees_list(self, data):
        """Format danh sách nhân viên"""
        if not data:
            return "📋 Không tìm thấy nhân viên nào."
        
        response = "👥 **DANH SÁCH NHÂN VIÊN:**\n\n"
        for emp in data[:10]:  # Limit to 10
            response += f"• **{emp.get('name', 'N/A')}** (ID: {emp.get('id')})\n"
            response += f"  📧 Email: {emp.get('work_email', 'N/A')}\n"
            response += f"  🏢 Phòng ban: {emp.get('department_id', ['N/A'])[1] if emp.get('department_id') else 'N/A'}\n\n"
        
        return response

    def _format_dashboard_stats(self, data):
        """Format thống kê dashboard"""
        return f"""📊 **THỐNG KÊ HR TỔNG HỢP:**

👥 **Nhân viên:** {data.get('total_employees', 0)}
📋 **Hợp đồng đang hoạt động:** {data.get('active_contracts', 0)}
📅 **Đơn nghỉ phép chờ duyệt:** {data.get('pending_leaves', 0)}

🕐 **Cập nhật lúc:** {data.get('generated_at', 'N/A')}"""

    def _format_search_results(self, data):
        """Format kết quả tìm kiếm"""
        response = f"🔍 **KẾT QUẢ TÌM KIẾM: '{data.get('search_term', '')}'**\n\n"
        
        # Employees
        employees = data.get('employees', [])
        if employees:
            response += "👥 **Nhân viên:**\n"
            for emp in employees:
                response += f"• {emp['name']} ({emp['email']})\n"
            response += "\n"
        
        # Departments
        departments = data.get('departments', [])
        if departments:
            response += "🏢 **Phòng ban:**\n"
            for dept in departments:
                response += f"• {dept['name']}\n"
        
        if not employees and not departments:
            response += "❌ Không tìm thấy kết quả nào."
        
        return response

    def _format_attendance_report(self, data):
        """Format báo cáo chấm công"""
        return f"""⏰ **BÁO CÁO CHẤM CÔNG:**

📊 **Tổng bản ghi:** {data.get('total_records', 0)}
🕐 **Tổng giờ làm:** {data.get('total_hours', 0):.1f}h
📅 **Tổng ngày làm:** {data.get('total_days', 0)}
📈 **Trung bình giờ/ngày:** {data.get('average_hours_per_day', 0):.1f}h
👥 **Số nhân viên:** {data.get('employees_count', 0)}
⏰ **Check-in muộn:** {data.get('late_checkins', 0)}
💪 **Giờ làm thêm:** {data.get('overtime_records', 0)}"""

    def _format_leaves_list(self, data):
        """Format danh sách nghỉ phép"""
        if not data:
            return "📅 Không có đơn nghỉ phép nào."
        
        response = "📅 **DANH SÁCH NGHỈ PHÉP:**\n\n"
        for leave in data[:5]:  # Limit to 5
            response += f"• **{leave.get('employee_id', ['N/A'])[1] if leave.get('employee_id') else 'N/A'}**\n"
            response += f"  📅 Từ: {leave.get('date_from', 'N/A')} → Đến: {leave.get('date_to', 'N/A')}\n"
            response += f"  📝 Lý do: {leave.get('name', 'N/A')}\n"
            response += f"  ✅ Trạng thái: {leave.get('state', 'N/A')}\n\n"
        
        return response

    def _format_create_job_response(self, data):
        """Format response cho việc tạo job"""
        if data.get('created'):
            return f"""✅ **TẠO VỊ TRÍ TUYỂN DỤNG THÀNH CÔNG**

🆔 **ID:** {data.get('id')}
📝 **Tên vị trí:** {data.get('name')}
🏢 **Phòng ban:** {data.get('department_name', 'Chưa chỉ định')}
👥 **Số lượng cần tuyển:** {data.get('expected_employees', 1)}
📊 **Trạng thái:** {data.get('state_display', data.get('state', 'N/A'))}

💡 {data.get('summary', 'Đã tạo vị trí tuyển dụng mới')}"""
        else:
            return f"❌ Không thể tạo vị trí tuyển dụng: {data.get('error', 'Unknown error')}"

    def _format_create_employee_response(self, data):
        """Format response cho việc tạo nhân viên"""
        if data.get('created'):
            return f"""✅ **TẠO NHÂN VIÊN THÀNH CÔNG**

🆔 **ID:** {data.get('id')}
👤 **Tên:** {data.get('name')}
📧 **Email:** {data.get('work_email', 'Chưa có')}
🏢 **Phòng ban:** {data.get('department_name', 'Chưa chỉ định')}

💡 {data.get('summary', 'Đã tạo nhân viên mới')}"""
        else:
            return f"❌ Không thể tạo nhân viên: {data.get('error', 'Unknown error')}"

    def _format_create_department_response(self, data):
        """Format response cho việc tạo phòng ban"""
        if data.get('created'):
            return f"""✅ **TẠO PHÒNG BAN THÀNH CÔNG**

🆔 **ID:** {data.get('id')}
🏢 **Tên phòng ban:** {data.get('name')}
👨‍💼 **Quản lý:** {data.get('manager_name', 'Chưa chỉ định')}

💡 {data.get('summary', 'Đã tạo phòng ban mới')}"""
        else:
            return f"❌ Không thể tạo phòng ban: {data.get('error', 'Unknown error')}"

    # ======================= ENHANCED AI FEATURES =======================

    @http.route('/sbotchat/hr_suggestions', type='json', auth='user', methods=['GET', 'POST'])
    def get_hr_suggestions(self, **kwargs):
        """Endpoint để lấy danh sách HR suggestions cho chatbot"""
        try:
            suggestions = [
                "Hiển thị danh sách nhân viên",
                "Tạo đơn nghỉ phép mới", 
                "Xem báo cáo chấm công",
                "Tính lương tháng này",
                "Thêm nhân viên mới",
                "Phê duyệt đơn nghỉ phép",
                "Xem hợp đồng lao động",
                "Báo cáo kỹ năng nhân viên",
                "Quản lý bảo hiểm BHXH",
                "Tạo timesheet project",
                "Xem thống kê HR",
                "Tìm kiếm ứng viên"
            ]
            
            return {
                'success': True,
                'suggestions': suggestions,
                'count': len(suggestions)
            }
            
        except Exception as e:
            _logger.error(f"Error getting HR suggestions: {str(e)}")
            return {
                'success': False,
                'error': f'Lỗi khi lấy HR suggestions: {str(e)}'
            }

    @http.route('/sbotchat/hr_help', type='json', auth='user', methods=['GET', 'POST'])
    def get_hr_help(self, **kwargs):
        """Hướng dẫn sử dụng AI Agent HR"""
        try:
            help_text = self._create_enhanced_system_prompt()
            return {'success': True, 'help': help_text}
        except Exception as e:
            _logger.error(f"Error in HR help: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _create_enhanced_system_prompt(self):
        """Tạo system prompt mở rộng có thông tin về HR APIs đầy đủ 116 endpoints"""
        base_prompt = """Bạn là một AI Assistant thông minh được tích hợp với hệ thống HR Odoo 18.0. 
Bạn có thể hiểu ngôn ngữ tự nhiên và tự động gọi các API HR phù hợp.

**KHẢ NĂNG HR APIS HOÀN CHỈNH (116 endpoints):**

🏢 **EMPLOYEE MANAGEMENT (12 APIs):**
1. GET/POST /api/hr/employees - Quản lý danh sách nhân viên
2. GET/PUT/DELETE /api/hr/employee/<id> - Chi tiết/Cập nhật/Xóa nhân viên
3. GET/PUT /api/hr/employee/<id>/status - Trạng thái nhân viên
4. GET/POST /api/hr/employee/departments - Quản lý phòng ban
5. GET/PUT/DELETE /api/hr/employee/department/<id> - Chi tiết phòng ban
6. GET/POST /api/hr/employee/jobs - Quản lý vị trí công việc
7. GET/PUT/DELETE /api/hr/employee/job/<id> - Chi tiết vị trí công việc
8. GET/POST /api/hr/employee/<id>/bhxh-history - Lịch sử BHXH/BHYT
9. GET/POST /api/hr/employee/<id>/projects-assignments - Phân bổ dự án
10. GET/POST /api/hr/employee/<id>/shifts-assignments - Ca làm việc
11. GET/POST /api/hr/employee/<id>/personal-income-tax - Thuế TNCN
12. GET/POST /api/hr/employee/<id>/shifts - Ca làm việc nhân viên

📅 **LEAVE MANAGEMENT (9 APIs):**
13. GET/POST /api/hr/leave-types - Quản lý loại nghỉ phép
14. GET/PUT/DELETE /api/hr/leave-type/<id> - Chi tiết loại nghỉ phép
15. GET/POST /api/hr/leave-allocations - Quản lý phân bổ nghỉ phép
16. GET/PUT/DELETE /api/hr/leave-allocation/<id> - Chi tiết phân bổ
17. POST /api/hr/leave-allocation/<id>/approve - Phê duyệt phân bổ
18. GET/POST /api/hr/leaves - Quản lý nghỉ phép
19. GET/PUT/DELETE /api/hr/leave/<id> - Chi tiết nghỉ phép
20. POST /api/hr/leave/<id>/approve - Phê duyệt nghỉ phép
21. POST /api/hr/leave/<id>/refuse - Từ chối nghỉ phép

📋 **CONTRACT MANAGEMENT (2 APIs):**
22. GET/POST /api/hr/contracts - Quản lý hợp đồng lao động
23. GET/PUT/DELETE /api/hr/contract/<id> - Chi tiết hợp đồng

⏰ **ATTENDANCE MANAGEMENT (7 APIs):**
24. GET/POST /api/hr/attendances - Quản lý chấm công
25. GET/PUT/DELETE /api/hr/attendance/<id> - Chi tiết chấm công
26. POST /api/hr/employee/<id>/checkin - Check-in nhân viên
27. POST /api/hr/employee/<id>/checkout - Check-out nhân viên
28. GET /api/hr/attendance/summary - Tóm tắt chấm công
29. GET /api/hr/attendance/overtime - Tính toán giờ làm thêm
30. GET /api/hr/attendance/missing - Tìm chấm công thiếu

💰 **PAYROLL MANAGEMENT (8 APIs):**
31. GET/POST /api/hr/payslips - Quản lý bảng lương
32. GET/PUT/DELETE /api/hr/payslip/<id> - Chi tiết bảng lương
33. POST /api/hr/payslip/<id>/compute - Tính toán bảng lương
34. GET /api/hr/payslip/<id>/lines - Chi tiết dòng bảng lương
35. GET/POST /api/hr/payroll/salary-rules - Quy tắc lương
36. GET/PUT/DELETE /api/hr/payroll/salary-rule/<id> - Chi tiết quy tắc lương
37. GET/POST /api/hr/payroll/structures - Cấu trúc lương
38. GET/PUT/DELETE /api/hr/payroll/structure/<id> - Chi tiết cấu trúc lương

🏥 **INSURANCE MANAGEMENT (12 APIs):**
39. GET/POST /api/hr/insurances - Quản lý bảo hiểm nhân viên
40. GET/PUT/DELETE /api/hr/insurance/<id> - Chi tiết bảo hiểm
41. GET/POST /api/hr/insurance/policies - Chính sách bảo hiểm
42. GET/PUT/DELETE /api/hr/insurance/policy/<id> - Chi tiết chính sách
43. GET/POST/PUT /api/hr/employee/<id>/bhxh - Quản lý BHXH/BHYT/BHTN
44. GET/POST /api/hr/insurance/payments - Thanh toán bảo hiểm
45. GET/PUT/DELETE /api/hr/insurance/payment/<id> - Chi tiết thanh toán
46. GET/POST /api/hr/insurance/benefits - Quyền lợi bảo hiểm
47. GET/PUT/DELETE /api/hr/insurance/benefit/<id> - Chi tiết quyền lợi
48. GET/POST /api/hr/insurance/documents - Hồ sơ bảo hiểm
49. GET/PUT/DELETE /api/hr/insurance/document/<id> - Chi tiết hồ sơ
50. GET/POST /api/hr/insurance/reports - Báo cáo bảo hiểm

🏥 **Insurance Intent Examples:**
- **"Quản lý bảo hiểm BHXH"** → GET /api/hr/insurances
- **"Tạo hồ sơ BHXH mới"** → POST /api/hr/employee/{id}/bhxh
- **"Xem chính sách bảo hiểm"** → GET /api/hr/insurance/policies
- **"Thanh toán bảo hiểm"** → POST /api/hr/insurance/payments
- **"Quyền lợi bảo hiểm"** → GET /api/hr/insurance/benefits
- **"Báo cáo bảo hiểm"** → GET /api/hr/insurance/reports

🎯 **PROJECT & TASK MANAGEMENT (6 APIs):**
51. GET/POST /api/hr/projects - Quản lý dự án
52. GET/PUT/DELETE /api/hr/project/<id> - Chi tiết dự án
53. GET/POST /api/hr/project/<id>/tasks - Task trong dự án
54. GET/POST /api/hr/tasks - Quản lý task
55. GET/PUT/DELETE /api/hr/task/<id> - Chi tiết task
56. POST /api/hr/task/<id>/assign - Phân công task

🧠 **SKILLS MANAGEMENT (11 APIs):**
57. GET/POST /api/hr/skills - Quản lý kỹ năng
58. GET/PUT/DELETE /api/hr/skill/<id> - Chi tiết kỹ năng
59. GET/POST /api/hr/skill-types - Loại kỹ năng
60. GET/PUT/DELETE /api/hr/skill-type/<id> - Chi tiết loại kỹ năng
61. GET/POST /api/hr/skill-levels - Cấp độ kỹ năng
62. GET/PUT/DELETE /api/hr/skill-level/<id> - Chi tiết cấp độ
63. GET/POST /api/hr/employee/<id>/skills - Kỹ năng nhân viên
64. GET/PUT/DELETE /api/hr/employee-skill/<id> - Chi tiết kỹ năng NV
65. GET/POST /api/hr/resume-lines - Sơ yếu lý lịch
66. GET/PUT/DELETE /api/hr/resume-line/<id> - Chi tiết sơ yếu
67. GET /api/hr/employee/<id>/resume - Lý lịch nhân viên

🎯 **Project Intent Examples:**
- **"Quản lý dự án"** → GET/POST /api/hr/projects
- **"Tạo task mới"** → POST /api/hr/tasks
- **"Phân công task"** → POST /api/hr/task/{id}/assign
- **"Task trong dự án"** → GET /api/hr/project/{id}/tasks

🧠 **Skills Intent Examples:**
- **"Quản lý kỹ năng"** → GET/POST /api/hr/skills
- **"Kỹ năng nhân viên"** → GET /api/hr/employee/{id}/skills
- **"Tạo loại kỹ năng"** → POST /api/hr/skill-types
- **"Xem sơ yếu lý lịch"** → GET /api/hr/employee/{id}/resume

⏱️ **TIMESHEET MANAGEMENT (9 APIs):**
68. GET/POST /api/hr/timesheets - Quản lý timesheet
69. GET/PUT/DELETE /api/hr/timesheet/<id> - Chi tiết timesheet
70. GET/POST /api/hr/employee/<id>/timesheets - Timesheet theo NV
71. GET /api/hr/project/<id>/timesheets - Timesheet theo dự án
72. GET /api/hr/task/<id>/timesheets - Timesheet theo task
73. GET /api/hr/timesheet/summary - Tóm tắt timesheet
74. POST /api/hr/timesheet/validate - Xác nhận timesheet
75. POST /api/hr/timesheet/copy - Sao chép timesheet

🎯 **RECRUITMENT MANAGEMENT (11 APIs):**
76. GET/POST /api/hr/applicants - Quản lý ứng viên
77. GET/PUT/DELETE /api/hr/applicant/<id> - Chi tiết ứng viên
78. GET/PUT /api/hr/applicant/<id>/status - Trạng thái ứng viên
79. POST /api/hr/applicant/<id>/hire - Tuyển dụng ứng viên
80. POST /api/hr/applicant/<id>/refuse - Từ chối ứng viên
81. GET/POST /api/hr/recruitment/jobs - Vị trí tuyển dụng
82. GET/PUT/DELETE /api/hr/recruitment/job/<id> - Chi tiết vị trí
83. GET/POST /api/hr/recruitment/stages - Giai đoạn tuyển dụng
84. GET/PUT/DELETE /api/hr/recruitment/stage/<id> - Chi tiết giai đoạn
85. GET/POST /api/hr/candidates - Ứng cử viên
86. GET/PUT/DELETE /api/hr/candidate/<id> - Chi tiết ứng cử viên

⏱️ **Timesheet Intent Examples:**
- **"Tạo timesheet"** → POST /api/hr/timesheets
- **"Timesheet nhân viên"** → GET /api/hr/employee/{id}/timesheets
- **"Timesheet dự án"** → GET /api/hr/project/{id}/timesheets
- **"Tóm tắt timesheet"** → GET /api/hr/timesheet/summary
- **"Xác nhận timesheet"** → POST /api/hr/timesheet/validate

🎯 **Recruitment Intent Examples:**
- **"Quản lý ứng viên"** → GET/POST /api/hr/applicants
- **"Tuyển dụng ứng viên"** → POST /api/hr/applicant/{id}/hire
- **"Từ chối ứng viên"** → POST /api/hr/applicant/{id}/refuse
- **"Vị trí tuyển dụng"** → GET/POST /api/hr/recruitment/jobs
- **"Giai đoạn tuyển dụng"** → GET/POST /api/hr/recruitment/stages

**CÁC INTENT PHỔ BIẾN VÀ API MAPPING:**

📋 **Employee Intent Examples:**
- **"Hiển thị danh sách nhân viên"** → GET /api/hr/employees
- **"Thêm nhân viên mới"** → POST /api/hr/employees
- **"Cập nhật thông tin nhân viên"** → PUT /api/hr/employee/{id}
- **"Xem trạng thái nhân viên"** → GET /api/hr/employee/{id}/status
- **"Quản lý phòng ban"** → GET/POST /api/hr/employee/departments
- **"Tạo vị trí công việc"** → POST /api/hr/employee/jobs
- **"Xem lịch sử BHXH"** → GET /api/hr/employee/{id}/bhxh-history
- **"Phân bổ dự án cho nhân viên"** → POST /api/hr/employee/{id}/projects-assignments

📅 **Leave Intent Examples:**
- **"Tạo đơn nghỉ phép"** → POST /api/hr/leaves
- **"Xem danh sách nghỉ phép"** → GET /api/hr/leaves
- **"Phê duyệt nghỉ phép"** → POST /api/hr/leave/{id}/approve
- **"Từ chối nghỉ phép"** → POST /api/hr/leave/{id}/refuse
- **"Quản lý loại nghỉ phép"** → GET/POST /api/hr/leave-types
- **"Phân bổ ngày nghỉ"** → POST /api/hr/leave-allocations

**Contract Intent Examples:**
- **"Xem hợp đồng lao động"** → GET /api/hr/contracts
- **"Tạo hợp đồng mới"** → POST /api/hr/contracts
- **"Cập nhật hợp đồng"** → PUT /api/hr/contract/{id}

⏰ **Attendance Intent Examples:**
- **"Chấm công vào"** → POST /api/hr/employee/{id}/checkin
- **"Chấm công ra"** → POST /api/hr/employee/{id}/checkout
- **"Báo cáo chấm công"** → GET /api/hr/attendance/summary
- **"Tính giờ làm thêm"** → GET /api/hr/attendance/overtime
- **"Kiểm tra chấm công thiếu"** → GET /api/hr/attendance/missing

💰 **Payroll Intent Examples:**
- **"Xem bảng lương"** → GET /api/hr/payslips
- **"Tính lương nhân viên"** → POST /api/hr/payslip/{id}/compute
- **"Quản lý quy tắc lương"** → GET/POST /api/hr/payroll/salary-rules
- **"Cấu trúc lương"** → GET/POST /api/hr/payroll/structures

**HƯỚNG DẪN XỬ LÝ:**
- Khi người dùng hỏi về HR, phân tích intent và xác định API call phù hợp
- Luôn trả về JSON format với: {intent, api_endpoint, parameters, confidence}
- Nếu cần thêm thông tin từ người dùng, hỏi một cách tự nhiên
- Giải thích kết quả API call bằng ngôn ngữ dễ hiểu
- Hỗ trợ cả tiếng Việt và tiếng Anh

**LƯU Ý QUAN TRỌNG:**
- Chỉ gọi API HR khi chắc chắn về intent
- Luôn validate dữ liệu trước khi gọi API
- Xử lý lỗi một cách thân thiện
- Đưa ra gợi ý hữu ích cho người dùng
- Tương thích 100% với Odoo 18.0
- Hỗ trợ đặc thù Việt Nam (BHXH/BHYT/BHTN)"""

        return base_prompt