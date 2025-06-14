# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import json
import logging
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)

class HRAPIController(http.Controller):
    """
    API Controller tổng hợp toàn bộ chức năng HR
    Bao gồm: Employee, Contract, Attendance, Leave, Payroll, Insurance, Projects, Skills
    """

    # ======================= EMPLOYEE MANAGEMENT =======================
    
    @http.route('/api/hr/employees', type='json', auth='user', methods=['GET', 'POST'])
    def hr_employees(self, **kwargs):
        """API quản lý nhân viên - GET (list), POST (create)"""
        try:
            if request.httprequest.method == 'GET':
                # Lấy danh sách nhân viên
                domain = kwargs.get('domain', [])
                fields_list = kwargs.get('fields', ['name', 'department_id', 'job_id', 'work_email', 'active'])
                employees = request.env['hr.employee'].search_read(domain, fields_list)
                return {'success': True, 'data': employees}
            
            elif request.httprequest.method == 'POST':
                # Tạo nhân viên mới
                vals = kwargs.get('vals', {})
                employee = request.env['hr.employee'].create(vals)
                return {'success': True, 'data': {'id': employee.id, 'name': employee.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_employee_detail(self, employee_id, **kwargs):
        """API chi tiết nhân viên - GET, PUT (update), DELETE"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            if request.httprequest.method == 'GET':
                # Lấy thông tin chi tiết
                data = employee.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                # Cập nhật thông tin
                vals = kwargs.get('vals', {})
                employee.write(vals)
                return {'success': True, 'data': {'id': employee.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                # Xóa nhân viên (archive)
                employee.write({'active': False})
                return {'success': True, 'data': {'id': employee.id, 'archived': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/status', type='json', auth='user', methods=['GET', 'PUT'])
    def hr_employee_status(self, employee_id, **kwargs):
        """API trạng thái nhân viên"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            if request.httprequest.method == 'GET':
                status = {
                    'active': employee.active,
                    'hr_presence_state': employee.hr_presence_state,
                    'departure_date': employee.departure_date,
                    'contract_status': 'active' if employee.contract_ids.filtered(lambda c: c.state == 'open') else 'inactive'
                }
                return {'success': True, 'data': status}
            
            elif request.httprequest.method == 'PUT':
                new_status = kwargs.get('status', {})
                employee.write(new_status)
                return {'success': True, 'data': {'id': employee.id, 'status_updated': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= EMPLOYEE EXTENDED MANAGEMENT =======================

    @http.route('/api/hr/employee/departments', type='json', auth='user', methods=['GET', 'POST'])
    def hr_employee_departments(self, **kwargs):
        """API quản lý phòng ban"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                departments = request.env['hr.department'].search_read(domain)
                return {'success': True, 'data': departments}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                department = request.env['hr.department'].create(vals)
                return {'success': True, 'data': {'id': department.id, 'name': department.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/department/<int:department_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_employee_department_detail(self, department_id, **kwargs):
        """API chi tiết phòng ban"""
        try:
            department = request.env['hr.department'].browse(department_id)
            if not department.exists():
                return {'success': False, 'error': 'Department not found'}

            if request.httprequest.method == 'GET':
                data = department.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                department.write(vals)
                return {'success': True, 'data': {'id': department.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                department.write({'active': False})
                return {'success': True, 'data': {'id': department.id, 'archived': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/jobs', type='json', auth='user', methods=['GET', 'POST'])
    def hr_employee_jobs(self, **kwargs):
        """API quản lý vị trí công việc với hỗ trợ description và requirements"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                jobs = request.env['hr.job'].search_read(domain)
                # Thêm thông tin bổ sung
                for job in jobs:
                    job['description'] = job.get('description', '')
                    job['requirements'] = job.get('requirements', '')
                    job['expected_employees'] = job.get('no_of_recruitment', 1)
                return {'success': True, 'data': jobs}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                # Hỗ trợ expected_employees hoặc no_of_recruitment
                if 'expected_employees' in vals and 'no_of_recruitment' not in vals:
                    vals['no_of_recruitment'] = vals.pop('expected_employees')
                
                job = request.env['hr.job'].create(vals)
                return {
                    'success': True, 
                    'data': {
                        'id': job.id, 
                        'name': job.name,
                        'department': job.department_id.name if job.department_id else '',
                        'description': job.description or '',
                        'requirements': job.requirements or '',
                        'expected_employees': job.no_of_recruitment
                    }
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/job/<int:job_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_employee_job_detail(self, job_id, **kwargs):
        """API chi tiết vị trí công việc với hỗ trợ đầy đủ description và requirements"""
        try:
            job = request.env['hr.job'].browse(job_id)
            if not job.exists():
                return {'success': False, 'error': 'Job not found'}

            if request.httprequest.method == 'GET':
                data = job.read()[0]
                # Thêm thông tin bổ sung
                data['description'] = data.get('description', '')
                data['requirements'] = data.get('requirements', '')
                data['expected_employees'] = data.get('no_of_recruitment', 1)
                # Đếm số nhân viên hiện tại
                employees_count = request.env['hr.employee'].search_count([('job_id', '=', job_id), ('active', '=', True)])
                data['current_employees'] = employees_count
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                # Hỗ trợ expected_employees hoặc no_of_recruitment
                if 'expected_employees' in vals and 'no_of_recruitment' not in vals:
                    vals['no_of_recruitment'] = vals.pop('expected_employees')
                    
                job.write(vals)
                return {
                    'success': True, 
                    'data': {
                        'id': job.id, 
                        'updated': True,
                        'name': job.name,
                        'department': job.department_id.name if job.department_id else '',
                        'description': job.description or '',
                        'requirements': job.requirements or '',
                        'expected_employees': job.no_of_recruitment
                    }
                }
            
            elif request.httprequest.method == 'DELETE':
                job.write({'active': False})
                return {'success': True, 'data': {'id': job.id, 'archived': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/bhxh-history', type='json', auth='user', methods=['GET', 'POST'])
    def hr_employee_bhxh_history(self, employee_id, **kwargs):
        """API lịch sử giao dịch BHXH/BHYT"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            if request.httprequest.method == 'GET':
                history = request.env['hr.employee.bhxh.history'].search([('employee_id', '=', employee_id)])
                history_data = []
                for h in history:
                    history_data.append({
                        'id': h.id,
                        'action_type': h.action_type,
                        'date_action': h.date_action.isoformat() if h.date_action else '',
                        'status': h.status,
                        'transaction_code': h.transaction_code,
                        'response_note': h.response_note,
                    })
                return {'success': True, 'data': history_data}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                vals['employee_id'] = employee_id
                history = request.env['hr.employee.bhxh.history'].create(vals)
                return {'success': True, 'data': {'id': history.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/projects-assignments', type='json', auth='user', methods=['GET', 'POST'])
    def hr_employee_project_assignments(self, employee_id, **kwargs):
        """API phân bổ dự án cho nhân viên - đã cập nhật hoàn chỉnh"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            if request.httprequest.method == 'GET':
                assignments = request.env['hr.employee.project.assignment'].search([('employee_id', '=', employee_id)])
                assignments_data = []
                for assignment in assignments:
                    assignments_data.append({
                        'id': assignment.id,
                        'project_id': assignment.project_id.name if assignment.project_id else '',
                        'role': assignment.role,
                        'date_start': assignment.date_start.isoformat() if assignment.date_start else '',
                        'date_end': assignment.date_end.isoformat() if assignment.date_end else '',
                        'progress': assignment.progress,
                        'performance_score': assignment.performance_score,
                        'note': assignment.note,
                    })
                return {'success': True, 'data': assignments_data}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                vals['employee_id'] = employee_id
                assignment = request.env['hr.employee.project.assignment'].create(vals)
                return {'success': True, 'data': {'id': assignment.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/shifts-assignments', type='json', auth='user', methods=['GET', 'POST'])
    def hr_employee_shifts_assignments(self, employee_id, **kwargs):
        """API ca làm việc cho nhân viên - đã cập nhật hoàn chỉnh"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            if request.httprequest.method == 'GET':
                shifts = request.env['hr.employee.shift'].search([('employee_id', '=', employee_id)])
                shifts_data = []
                for shift in shifts:
                    shifts_data.append({
                        'id': shift.id,
                        'shift_name': shift.shift_name,
                        'shift_type': shift.shift_type,
                        'time_start': shift.time_start,
                        'time_end': shift.time_end,
                        'date_apply': shift.date_apply.isoformat() if shift.date_apply else '',
                        'note': shift.note,
                    })
                return {'success': True, 'data': shifts_data}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                vals['employee_id'] = employee_id
                shift = request.env['hr.employee.shift'].create(vals)
                return {'success': True, 'data': {'id': shift.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/personal-income-tax', type='json', auth='user', methods=['GET', 'POST'])
    def hr_employee_personal_income_tax(self, employee_id, **kwargs):
        """API quyết toán thuế TNCN cho nhân viên"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            if request.httprequest.method == 'GET':
                tax_records = request.env['hr.employee.personal.income.tax'].search([('employee_id', '=', employee_id)])
                tax_data = []
                for tax in tax_records:
                    tax_data.append({
                        'id': tax.id,
                        'year': tax.year,
                        'total_income': tax.total_income,
                        'self_deduction': tax.self_deduction,
                        'dependent_deduction': tax.dependent_deduction,
                        'taxable_income': tax.taxable_income,
                        'tax_amount': tax.tax_amount,
                        'state': tax.state,
                    })
                return {'success': True, 'data': tax_data}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                vals['employee_id'] = employee_id
                tax_record = request.env['hr.employee.personal.income.tax'].create(vals)
                return {'success': True, 'data': {'id': tax_record.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= LEAVE TYPES & ALLOCATIONS =======================

    @http.route('/api/hr/leave-types', type='json', auth='user', methods=['GET', 'POST'])
    def hr_leave_types(self, **kwargs):
        """API quản lý loại nghỉ phép"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                leave_types = request.env['hr.leave.type'].search_read(domain)
                return {'success': True, 'data': leave_types}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                leave_type = request.env['hr.leave.type'].create(vals)
                return {'success': True, 'data': {'id': leave_type.id, 'name': leave_type.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/leave-type/<int:leave_type_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_leave_type_detail(self, leave_type_id, **kwargs):
        """API chi tiết loại nghỉ phép"""
        try:
            leave_type = request.env['hr.leave.type'].browse(leave_type_id)
            if not leave_type.exists():
                return {'success': False, 'error': 'Leave type not found'}

            if request.httprequest.method == 'GET':
                data = leave_type.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                leave_type.write(vals)
                return {'success': True, 'data': {'id': leave_type.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                leave_type.write({'active': False})
                return {'success': True, 'data': {'id': leave_type.id, 'archived': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/leave-allocations', type='json', auth='user', methods=['GET', 'POST'])
    def hr_leave_allocations(self, **kwargs):
        """API quản lý phân bổ nghỉ phép"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                allocations = request.env['hr.leave.allocation'].search_read(domain)
                return {'success': True, 'data': allocations}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                allocation = request.env['hr.leave.allocation'].create(vals)
                return {'success': True, 'data': {'id': allocation.id, 'name': allocation.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/leave-allocation/<int:allocation_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_leave_allocation_detail(self, allocation_id, **kwargs):
        """API chi tiết phân bổ nghỉ phép"""
        try:
            allocation = request.env['hr.leave.allocation'].browse(allocation_id)
            if not allocation.exists():
                return {'success': False, 'error': 'Leave allocation not found'}

            if request.httprequest.method == 'GET':
                data = allocation.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                allocation.write(vals)
                return {'success': True, 'data': {'id': allocation.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                allocation.write({'state': 'cancel'})
                return {'success': True, 'data': {'id': allocation.id, 'cancelled': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/leave-allocation/<int:allocation_id>/approve', type='json', auth='user', methods=['POST'])
    def hr_leave_allocation_approve(self, allocation_id, **kwargs):
        """API phê duyệt phân bổ nghỉ phép"""
        try:
            allocation = request.env['hr.leave.allocation'].browse(allocation_id)
            if not allocation.exists():
                return {'success': False, 'error': 'Leave allocation not found'}

            allocation.action_approve()
            return {'success': True, 'data': {'id': allocation.id, 'state': allocation.state}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= CONTRACT MANAGEMENT =======================

    @http.route('/api/hr/contracts', type='json', auth='user', methods=['GET', 'POST'])
    def hr_contracts(self, **kwargs):
        """API quản lý hợp đồng"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                contracts = request.env['hr.contract'].search_read(domain)
                return {'success': True, 'data': contracts}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                contract = request.env['hr.contract'].create(vals)
                return {'success': True, 'data': {'id': contract.id, 'name': contract.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/contract/<int:contract_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_contract_detail(self, contract_id, **kwargs):
        """API chi tiết hợp đồng"""
        try:
            contract = request.env['hr.contract'].browse(contract_id)
            if not contract.exists():
                return {'success': False, 'error': 'Contract not found'}

            if request.httprequest.method == 'GET':
                data = contract.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                contract.write(vals)
                return {'success': True, 'data': {'id': contract.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                contract.write({'state': 'cancel'})
                return {'success': True, 'data': {'id': contract.id, 'cancelled': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= ATTENDANCE MANAGEMENT =======================

    @http.route('/api/hr/attendances', type='json', auth='user', methods=['GET', 'POST'])
    def hr_attendances(self, **kwargs):
        """API quản lý chấm công"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                attendances = request.env['hr.attendance'].search_read(domain)
                return {'success': True, 'data': attendances}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                attendance = request.env['hr.attendance'].create(vals)
                return {'success': True, 'data': {'id': attendance.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/attendance/<int:attendance_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_attendance_detail(self, attendance_id, **kwargs):
        """API chi tiết chấm công"""
        try:
            attendance = request.env['hr.attendance'].browse(attendance_id)
            if not attendance.exists():
                return {'success': False, 'error': 'Attendance not found'}

            if request.httprequest.method == 'GET':
                data = attendance.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                attendance.write(vals)
                return {'success': True, 'data': {'id': attendance.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                attendance.unlink()
                return {'success': True, 'data': {'id': attendance_id, 'deleted': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/checkin', type='json', auth='user', methods=['POST'])
    def hr_employee_checkin(self, employee_id, **kwargs):
        """API check-in nhân viên"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            # Tạo attendance check-in
            vals = {
                'employee_id': employee_id,
                'check_in': fields.Datetime.now(),
            }
            attendance = request.env['hr.attendance'].create(vals)
            return {'success': True, 'data': {'id': attendance.id, 'check_in': attendance.check_in}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/checkout', type='json', auth='user', methods=['POST'])
    def hr_employee_checkout(self, employee_id, **kwargs):
        """API check-out nhân viên"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            # Tìm attendance chưa check-out
            attendance = request.env['hr.attendance'].search([
                ('employee_id', '=', employee_id),
                ('check_out', '=', False)
            ], limit=1)
            
            if attendance:
                attendance.write({'check_out': fields.Datetime.now()})
                return {'success': True, 'data': {'id': attendance.id, 'check_out': attendance.check_out}}
            else:
                return {'success': False, 'error': 'No active check-in found'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= LEAVE MANAGEMENT =======================

    @http.route('/api/hr/leaves', type='json', auth='user', methods=['GET', 'POST'])
    def hr_leaves(self, **kwargs):
        """API quản lý nghỉ phép"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                leaves = request.env['hr.leave'].search_read(domain)
                return {'success': True, 'data': leaves}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                leave = request.env['hr.leave'].create(vals)
                return {'success': True, 'data': {'id': leave.id, 'name': leave.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/leave/<int:leave_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_leave_detail(self, leave_id, **kwargs):
        """API chi tiết nghỉ phép"""
        try:
            leave = request.env['hr.leave'].browse(leave_id)
            if not leave.exists():
                return {'success': False, 'error': 'Leave not found'}

            if request.httprequest.method == 'GET':
                data = leave.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                leave.write(vals)
                return {'success': True, 'data': {'id': leave.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                leave.write({'state': 'cancel'})
                return {'success': True, 'data': {'id': leave.id, 'cancelled': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/leave/<int:leave_id>/approve', type='json', auth='user', methods=['POST'])
    def hr_leave_approve(self, leave_id, **kwargs):
        """API phê duyệt nghỉ phép"""
        try:
            leave = request.env['hr.leave'].browse(leave_id)
            if not leave.exists():
                return {'success': False, 'error': 'Leave not found'}

            leave.action_approve()
            return {'success': True, 'data': {'id': leave.id, 'state': leave.state}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/leave/<int:leave_id>/refuse', type='json', auth='user', methods=['POST'])
    def hr_leave_refuse(self, leave_id, **kwargs):
        """API từ chối nghỉ phép"""
        try:
            leave = request.env['hr.leave'].browse(leave_id)
            if not leave.exists():
                return {'success': False, 'error': 'Leave not found'}

            leave.action_refuse()
            return {'success': True, 'data': {'id': leave.id, 'state': leave.state}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= PAYROLL MANAGEMENT =======================

    @http.route('/api/hr/payslips', type='json', auth='user', methods=['GET', 'POST'])
    def hr_payslips(self, **kwargs):
        """API quản lý bảng lương"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                payslips = request.env['hr.payslip'].search_read(domain)
                return {'success': True, 'data': payslips}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                payslip = request.env['hr.payslip'].create(vals)
                return {'success': True, 'data': {'id': payslip.id, 'name': payslip.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/payslip/<int:payslip_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_payslip_detail(self, payslip_id, **kwargs):
        """API chi tiết bảng lương"""
        try:
            payslip = request.env['hr.payslip'].browse(payslip_id)
            if not payslip.exists():
                return {'success': False, 'error': 'Payslip not found'}

            if request.httprequest.method == 'GET':
                data = payslip.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                payslip.write(vals)
                return {'success': True, 'data': {'id': payslip.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                payslip.write({'state': 'cancel'})
                return {'success': True, 'data': {'id': payslip.id, 'cancelled': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/payslip/<int:payslip_id>/compute', type='json', auth='user', methods=['POST'])
    def hr_payslip_compute(self, payslip_id, **kwargs):
        """API tính toán bảng lương"""
        try:
            payslip = request.env['hr.payslip'].browse(payslip_id)
            if not payslip.exists():
                return {'success': False, 'error': 'Payslip not found'}

            payslip.compute_sheet()
            return {'success': True, 'data': {'id': payslip.id, 'computed': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= INSURANCE MANAGEMENT (VN SPECIFIC) =======================

    @http.route('/api/hr/insurances', type='json', auth='user', methods=['GET', 'POST'])
    def hr_insurances(self, **kwargs):
        """API quản lý bảo hiểm nhân viên - GET (list), POST (create)"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                fields_list = kwargs.get('fields', ['name', 'employee_id', 'policy_id', 'state', 'start_date', 'end_date'])
                insurances = request.env['hr.insurance'].search_read(domain, fields_list)
                return {'success': True, 'data': insurances}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                insurance = request.env['hr.insurance'].create(vals)
                return {'success': True, 'data': {'id': insurance.id, 'name': insurance.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/insurance/<int:insurance_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_insurance_detail(self, insurance_id, **kwargs):
        """API chi tiết bảo hiểm"""
        try:
            insurance = request.env['hr.insurance'].browse(insurance_id)
            if not insurance.exists():
                return {'success': False, 'error': 'Insurance not found'}

            if request.httprequest.method == 'GET':
                data = insurance.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                insurance.write(vals)
                return {'success': True, 'data': {'id': insurance.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                insurance.write({'state': 'cancelled'})
                return {'success': True, 'data': {'id': insurance.id, 'cancelled': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/insurance/policies', type='json', auth='user', methods=['GET', 'POST'])
    def hr_insurance_policies(self, **kwargs):
        """API quản lý chính sách bảo hiểm"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                policies = request.env['insurance.policy'].search_read(domain)
                return {'success': True, 'data': policies}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                policy = request.env['insurance.policy'].create(vals)
                return {'success': True, 'data': {'id': policy.id, 'name': policy.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/insurance/policy/<int:policy_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_insurance_policy_detail(self, policy_id, **kwargs):
        """API chi tiết chính sách bảo hiểm"""
        try:
            policy = request.env['insurance.policy'].browse(policy_id)
            if not policy.exists():
                return {'success': False, 'error': 'Insurance policy not found'}

            if request.httprequest.method == 'GET':
                data = policy.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                policy.write(vals)
                return {'success': True, 'data': {'id': policy.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                policy.unlink()
                return {'success': True, 'data': {'id': policy_id, 'deleted': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/bhxh', type='json', auth='user', methods=['GET', 'POST', 'PUT'])
    def hr_employee_bhxh(self, employee_id, **kwargs):
        """API quản lý BHXH/BHYT/BHTN cho nhân viên - đã cập nhật hoàn chỉnh"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            if request.httprequest.method == 'GET':
                social_insurances = request.env['hr.insurance'].search([
                    ('employee_id', '=', employee_id),
                    ('policy_id.type', 'in', ['bhxh', 'bhyt', 'bhtn'])
                ])
                
                insurance_data = []
                for insurance in social_insurances:
                    insurance_data.append({
                        'id': insurance.id,
                        'name': insurance.name,
                        'policy_type': insurance.policy_id.type,
                        'policy_name': insurance.policy_id.name,
                        'state': insurance.state,
                        'start_date': insurance.start_date.isoformat() if insurance.start_date else '',
                        'end_date': insurance.end_date.isoformat() if insurance.end_date else '',
                        'premium_amount': insurance.premium_amount,
                        'company_contribution': insurance.company_contribution,
                        'employee_contribution': insurance.employee_contribution,
                    })
                
                data = {
                    'employee_info': {
                        'bhxh_code': employee.bhxh_code,
                        'bhyt_code': employee.bhyt_code,
                        'bhtn_code': employee.bhtn_code,
                        'personal_tax_code': employee.personal_tax_code,
                        'minimum_wage_region': employee.minimum_wage_region,
                    },
                    'insurances': insurance_data,
                    'summary': {
                        'total_active': len(social_insurances.filtered(lambda i: i.state == 'active')),
                        'total_premium': sum(social_insurances.mapped('premium_amount')),
                    }
                }
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'POST':
                # Tạo hồ sơ BHXH mới
                insurance_type = kwargs.get('insurance_type', 'bhxh')  # bhxh, bhyt, bhtn
                policy = request.env['insurance.policy'].search([('type', '=', insurance_type)], limit=1)
                
                if not policy:
                    return {'success': False, 'error': f'No {insurance_type.upper()} policy found'}
                
                vals = {
                    'employee_id': employee_id,
                    'policy_id': policy.id,
                    'start_date': kwargs.get('start_date', fields.Date.today()),
                    'state': 'active',
                }
                insurance = request.env['hr.insurance'].create(vals)
                return {'success': True, 'data': {'id': insurance.id, 'insurance_type': insurance_type}}
            
            elif request.httprequest.method == 'PUT':
                # Cập nhật thông tin BHXH
                vals = kwargs.get('vals', {})
                employee.write(vals)
                return {'success': True, 'data': {'id': employee.id, 'updated': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/insurance/payments', type='json', auth='user', methods=['GET', 'POST'])
    def hr_insurance_payments(self, **kwargs):
        """API quản lý thanh toán bảo hiểm"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                payments = request.env['insurance.payment'].search_read(domain)
                return {'success': True, 'data': payments}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                payment = request.env['insurance.payment'].create(vals)
                return {'success': True, 'data': {'id': payment.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/insurance/payment/<int:payment_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_insurance_payment_detail(self, payment_id, **kwargs):
        """API chi tiết thanh toán bảo hiểm"""
        try:
            payment = request.env['insurance.payment'].browse(payment_id)
            if not payment.exists():
                return {'success': False, 'error': 'Insurance payment not found'}

            if request.httprequest.method == 'GET':
                data = payment.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                payment.write(vals)
                return {'success': True, 'data': {'id': payment.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                payment.write({'state': 'cancelled'})
                return {'success': True, 'data': {'id': payment.id, 'cancelled': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/insurance/benefits', type='json', auth='user', methods=['GET', 'POST'])
    def hr_insurance_benefits(self, **kwargs):
        """API quản lý quyền lợi bảo hiểm xã hội"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                benefits = request.env['social.insurance.benefit'].search_read(domain)
                return {'success': True, 'data': benefits}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                benefit = request.env['social.insurance.benefit'].create(vals)
                return {'success': True, 'data': {'id': benefit.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/insurance/benefit/<int:benefit_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_insurance_benefit_detail(self, benefit_id, **kwargs):
        """API chi tiết quyền lợi bảo hiểm"""
        try:
            benefit = request.env['social.insurance.benefit'].browse(benefit_id)
            if not benefit.exists():
                return {'success': False, 'error': 'Insurance benefit not found'}

            if request.httprequest.method == 'GET':
                data = benefit.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                benefit.write(vals)
                return {'success': True, 'data': {'id': benefit.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                benefit.write({'state': 'cancelled'})
                return {'success': True, 'data': {'id': benefit.id, 'cancelled': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/insurance/documents', type='json', auth='user', methods=['GET', 'POST'])
    def hr_insurance_documents(self, **kwargs):
        """API quản lý hồ sơ bảo hiểm xã hội"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                documents = request.env['social.insurance.document'].search_read(domain)
                return {'success': True, 'data': documents}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                document = request.env['social.insurance.document'].create(vals)
                return {'success': True, 'data': {'id': document.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/insurance/document/<int:document_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_insurance_document_detail(self, document_id, **kwargs):
        """API chi tiết hồ sơ bảo hiểm"""
        try:
            document = request.env['social.insurance.document'].browse(document_id)
            if not document.exists():
                return {'success': False, 'error': 'Insurance document not found'}

            if request.httprequest.method == 'GET':
                data = document.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                document.write(vals)
                return {'success': True, 'data': {'id': document.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                document.write({'state': 'cancelled'})
                return {'success': True, 'data': {'id': document.id, 'cancelled': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/insurance/reports', type='json', auth='user', methods=['GET', 'POST'])
    def hr_insurance_reports(self, **kwargs):
        """API báo cáo bảo hiểm"""
        try:
            if request.httprequest.method == 'GET':
                report_type = kwargs.get('report_type', 'summary')
                date_from = kwargs.get('date_from')
                date_to = kwargs.get('date_to')
                
                if report_type == 'summary':
                    # Báo cáo tổng hợp
                    domain = []
                    if date_from:
                        domain.append(('start_date', '>=', date_from))
                    if date_to:
                        domain.append(('start_date', '<=', date_to))
                    
                    insurances = request.env['hr.insurance'].search(domain)
                    payments = request.env['insurance.payment'].search(domain)
                    
                    summary = {
                        'total_insurances': len(insurances),
                        'active_insurances': len(insurances.filtered(lambda i: i.state == 'active')),
                        'total_premium': sum(insurances.mapped('premium_amount')),
                        'total_payments': sum(payments.mapped('amount')),
                        'employees_covered': len(insurances.mapped('employee_id')),
                    }
                    
                    return {'success': True, 'data': summary}
                    
                elif report_type == 'by_policy':
                    # Báo cáo theo chính sách
                    policies_data = []
                    policies = request.env['insurance.policy'].search([])
                    
                    for policy in policies:
                        insurances = request.env['hr.insurance'].search([('policy_id', '=', policy.id)])
                        policies_data.append({
                            'policy_name': policy.name,
                            'policy_type': policy.type,
                            'total_insurances': len(insurances),
                            'active_insurances': len(insurances.filtered(lambda i: i.state == 'active')),
                            'total_premium': sum(insurances.mapped('premium_amount')),
                        })
                    
                    return {'success': True, 'data': policies_data}
                
                return {'success': False, 'error': 'Invalid report type'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= PROJECT & TASK MANAGEMENT =======================

    @http.route('/api/hr/projects', type='json', auth='user', methods=['GET', 'POST'])
    def hr_projects(self, **kwargs):
        """API quản lý dự án"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                projects = request.env['project.project'].search_read(domain)
                return {'success': True, 'data': projects}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                project = request.env['project.project'].create(vals)
                return {'success': True, 'data': {'id': project.id, 'name': project.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/project/<int:project_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_project_detail(self, project_id, **kwargs):
        """API chi tiết dự án"""
        try:
            project = request.env['project.project'].browse(project_id)
            if not project.exists():
                return {'success': False, 'error': 'Project not found'}

            if request.httprequest.method == 'GET':
                data = project.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                project.write(vals)
                return {'success': True, 'data': {'id': project.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                project.write({'active': False})
                return {'success': True, 'data': {'id': project.id, 'archived': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/project/<int:project_id>/tasks', type='json', auth='user', methods=['GET', 'POST'])
    def hr_project_tasks(self, project_id, **kwargs):
        """API quản lý task trong dự án"""
        try:
            project = request.env['project.project'].browse(project_id)
            if not project.exists():
                return {'success': False, 'error': 'Project not found'}

            if request.httprequest.method == 'GET':
                domain = [('project_id', '=', project_id)]
                tasks = request.env['project.task'].search_read(domain)
                return {'success': True, 'data': tasks}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                vals['project_id'] = project_id
                task = request.env['project.task'].create(vals)
                return {'success': True, 'data': {'id': task.id, 'name': task.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/tasks', type='json', auth='user', methods=['GET', 'POST'])
    def hr_tasks(self, **kwargs):
        """API quản lý task"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                tasks = request.env['project.task'].search_read(domain)
                return {'success': True, 'data': tasks}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                task = request.env['project.task'].create(vals)
                return {'success': True, 'data': {'id': task.id, 'name': task.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/task/<int:task_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_task_detail(self, task_id, **kwargs):
        """API chi tiết task"""
        try:
            task = request.env['project.task'].browse(task_id)
            if not task.exists():
                return {'success': False, 'error': 'Task not found'}

            if request.httprequest.method == 'GET':
                data = task.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                task.write(vals)
                return {'success': True, 'data': {'id': task.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                task.write({'active': False})
                return {'success': True, 'data': {'id': task.id, 'archived': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/task/<int:task_id>/assign', type='json', auth='user', methods=['POST'])
    def hr_task_assign(self, task_id, **kwargs):
        """API phân công task cho nhân viên"""
        try:
            task = request.env['project.task'].browse(task_id)
            if not task.exists():
                return {'success': False, 'error': 'Task not found'}

            user_ids = kwargs.get('user_ids', [])
            if user_ids:
                task.write({'user_ids': [(6, 0, user_ids)]})
                
            return {'success': True, 'data': {'id': task.id, 'assigned_users': len(user_ids)}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/projects-assignments', type='json', auth='user', methods=['GET', 'POST'])
    def hr_employee_project_assignments(self, employee_id, **kwargs):
        """API phân bổ dự án cho nhân viên - đã cập nhật hoàn chỉnh"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            if request.httprequest.method == 'GET':
                assignments = request.env['hr.employee.project.assignment'].search([('employee_id', '=', employee_id)])
                assignments_data = []
                for assignment in assignments:
                    assignments_data.append({
                        'id': assignment.id,
                        'project_id': assignment.project_id.name if assignment.project_id else '',
                        'role': assignment.role,
                        'date_start': assignment.date_start.isoformat() if assignment.date_start else '',
                        'date_end': assignment.date_end.isoformat() if assignment.date_end else '',
                        'progress': assignment.progress,
                        'performance_score': assignment.performance_score,
                        'note': assignment.note,
                    })
                return {'success': True, 'data': assignments_data}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                vals['employee_id'] = employee_id
                assignment = request.env['hr.employee.project.assignment'].create(vals)
                return {'success': True, 'data': {'id': assignment.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/shifts-assignments', type='json', auth='user', methods=['GET', 'POST'])
    def hr_employee_shifts_assignments(self, employee_id, **kwargs):
        """API ca làm việc cho nhân viên - đã cập nhật hoàn chỉnh"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            if request.httprequest.method == 'GET':
                shifts = request.env['hr.employee.shift'].search([('employee_id', '=', employee_id)])
                shifts_data = []
                for shift in shifts:
                    shifts_data.append({
                        'id': shift.id,
                        'shift_name': shift.shift_name,
                        'shift_type': shift.shift_type,
                        'time_start': shift.time_start,
                        'time_end': shift.time_end,
                        'date_apply': shift.date_apply.isoformat() if shift.date_apply else '',
                        'note': shift.note,
                    })
                return {'success': True, 'data': shifts_data}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                vals['employee_id'] = employee_id
                shift = request.env['hr.employee.shift'].create(vals)
                return {'success': True, 'data': {'id': shift.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= SKILLS MANAGEMENT =======================

    @http.route('/api/hr/skills', type='json', auth='user', methods=['GET', 'POST'])
    def hr_skills(self, **kwargs):
        """API quản lý kỹ năng - GET (list), POST (create)"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                fields_list = kwargs.get('fields', ['name', 'skill_type_id', 'sequence', 'color'])
                skills = request.env['hr.skill'].search_read(domain, fields_list)
                return {'success': True, 'data': skills}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                skill = request.env['hr.skill'].create(vals)
                return {'success': True, 'data': {'id': skill.id, 'name': skill.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/skill/<int:skill_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_skill_detail(self, skill_id, **kwargs):
        """API chi tiết kỹ năng"""
        try:
            skill = request.env['hr.skill'].browse(skill_id)
            if not skill.exists():
                return {'success': False, 'error': 'Skill not found'}

            if request.httprequest.method == 'GET':
                data = skill.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                skill.write(vals)
                return {'success': True, 'data': {'id': skill.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                skill.unlink()
                return {'success': True, 'data': {'id': skill_id, 'deleted': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/skill-types', type='json', auth='user', methods=['GET', 'POST'])
    def hr_skill_types(self, **kwargs):
        """API quản lý loại kỹ năng"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                skill_types = request.env['hr.skill.type'].search_read(domain)
                return {'success': True, 'data': skill_types}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                skill_type = request.env['hr.skill.type'].create(vals)
                return {'success': True, 'data': {'id': skill_type.id, 'name': skill_type.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/skill-type/<int:skill_type_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_skill_type_detail(self, skill_type_id, **kwargs):
        """API chi tiết loại kỹ năng"""
        try:
            skill_type = request.env['hr.skill.type'].browse(skill_type_id)
            if not skill_type.exists():
                return {'success': False, 'error': 'Skill type not found'}

            if request.httprequest.method == 'GET':
                data = skill_type.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                skill_type.write(vals)
                return {'success': True, 'data': {'id': skill_type.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                skill_type.unlink()
                return {'success': True, 'data': {'id': skill_type_id, 'deleted': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/skill-levels', type='json', auth='user', methods=['GET', 'POST'])
    def hr_skill_levels(self, **kwargs):
        """API quản lý cấp độ kỹ năng"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                skill_levels = request.env['hr.skill.level'].search_read(domain)
                return {'success': True, 'data': skill_levels}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                skill_level = request.env['hr.skill.level'].create(vals)
                return {'success': True, 'data': {'id': skill_level.id, 'name': skill_level.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/skill-level/<int:skill_level_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_skill_level_detail(self, skill_level_id, **kwargs):
        """API chi tiết cấp độ kỹ năng"""
        try:
            skill_level = request.env['hr.skill.level'].browse(skill_level_id)
            if not skill_level.exists():
                return {'success': False, 'error': 'Skill level not found'}

            if request.httprequest.method == 'GET':
                data = skill_level.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                skill_level.write(vals)
                return {'success': True, 'data': {'id': skill_level.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                skill_level.unlink()
                return {'success': True, 'data': {'id': skill_level_id, 'deleted': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/skills', type='json', auth='user', methods=['GET', 'POST'])
    def hr_employee_skills(self, employee_id, **kwargs):
        """API quản lý kỹ năng nhân viên - đã cập nhật hoàn chỉnh"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            if request.httprequest.method == 'GET':
                skills = request.env['hr.employee.skill'].search([('employee_id', '=', employee_id)])
                skills_data = []
                for skill in skills:
                    skills_data.append({
                        'id': skill.id,
                        'skill_id': skill.skill_id.name,
                        'skill_type_id': skill.skill_type_id.name,
                        'skill_level_id': skill.skill_level_id.name,
                        'level_progress': skill.level_progress,
                        'color': skill.color,
                    })
                return {'success': True, 'data': skills_data}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                vals['employee_id'] = employee_id
                employee_skill = request.env['hr.employee.skill'].create(vals)
                return {'success': True, 'data': {'id': employee_skill.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee-skill/<int:employee_skill_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_employee_skill_detail(self, employee_skill_id, **kwargs):
        """API chi tiết kỹ năng nhân viên"""
        try:
            employee_skill = request.env['hr.employee.skill'].browse(employee_skill_id)
            if not employee_skill.exists():
                return {'success': False, 'error': 'Employee skill not found'}

            if request.httprequest.method == 'GET':
                data = employee_skill.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                employee_skill.write(vals)
                return {'success': True, 'data': {'id': employee_skill.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                employee_skill.unlink()
                return {'success': True, 'data': {'id': employee_skill_id, 'deleted': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/resume-lines', type='json', auth='user', methods=['GET', 'POST'])
    def hr_resume_lines(self, **kwargs):
        """API quản lý sơ yếu lý lịch"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                resume_lines = request.env['hr.resume.line'].search_read(domain)
                return {'success': True, 'data': resume_lines}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                resume_line = request.env['hr.resume.line'].create(vals)
                return {'success': True, 'data': {'id': resume_line.id, 'name': resume_line.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/resume-line/<int:resume_line_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_resume_line_detail(self, resume_line_id, **kwargs):
        """API chi tiết sơ yếu lý lịch"""
        try:
            resume_line = request.env['hr.resume.line'].browse(resume_line_id)
            if not resume_line.exists():
                return {'success': False, 'error': 'Resume line not found'}

            if request.httprequest.method == 'GET':
                data = resume_line.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                resume_line.write(vals)
                return {'success': True, 'data': {'id': resume_line.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                resume_line.unlink()
                return {'success': True, 'data': {'id': resume_line_id, 'deleted': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/resume', type='json', auth='user', methods=['GET'])
    def hr_employee_resume(self, employee_id, **kwargs):
        """API lấy sơ yếu lý lịch nhân viên"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            resume_lines = request.env['hr.resume.line'].search([('employee_id', '=', employee_id)])
            resume_data = []
            for line in resume_lines:
                resume_data.append({
                    'id': line.id,
                    'name': line.name,
                    'line_type_id': line.line_type_id.name if line.line_type_id else '',
                    'date_start': line.date_start.isoformat() if line.date_start else '',
                    'date_end': line.date_end.isoformat() if line.date_end else '',
                    'description': line.description,
                })
            return {'success': True, 'data': resume_data}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= SHIFTS MANAGEMENT =======================

    @http.route('/api/hr/employee/<int:employee_id>/shifts', type='json', auth='user', methods=['GET', 'POST'])
    def hr_employee_shifts(self, employee_id, **kwargs):
        """API quản lý ca làm việc nhân viên"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            if request.httprequest.method == 'GET':
                shifts = employee.shift_ids.read()
                return {'success': True, 'data': shifts}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                vals['employee_id'] = employee_id
                shift = request.env['hr.employee.shift'].create(vals)
                return {'success': True, 'data': {'id': shift.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= TIMESHEET MANAGEMENT =======================

    @http.route('/api/hr/timesheets', type='json', auth='user', methods=['GET', 'POST'])
    def hr_timesheets(self, **kwargs):
        """API quản lý timesheet - GET (list), POST (create)"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                fields_list = kwargs.get('fields', ['name', 'employee_id', 'project_id', 'task_id', 'date', 'unit_amount', 'amount'])
                timesheets = request.env['account.analytic.line'].search_read(domain, fields_list)
                return {'success': True, 'data': timesheets}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                timesheet = request.env['account.analytic.line'].create(vals)
                return {'success': True, 'data': {'id': timesheet.id, 'name': timesheet.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/timesheet/<int:timesheet_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_timesheet_detail(self, timesheet_id, **kwargs):
        """API chi tiết timesheet - GET, PUT (update), DELETE"""
        try:
            timesheet = request.env['account.analytic.line'].browse(timesheet_id)
            if not timesheet.exists():
                return {'success': False, 'error': 'Timesheet not found'}

            if request.httprequest.method == 'GET':
                data = timesheet.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                timesheet.write(vals)
                return {'success': True, 'data': {'id': timesheet.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                timesheet.unlink()
                return {'success': True, 'data': {'id': timesheet_id, 'deleted': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/timesheets', type='json', auth='user', methods=['GET', 'POST'])
    def hr_employee_timesheets(self, employee_id, **kwargs):
        """API timesheet theo nhân viên"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            if request.httprequest.method == 'GET':
                date_from = kwargs.get('date_from')
                date_to = kwargs.get('date_to')
                domain = [('employee_id', '=', employee_id)]
                
                if date_from:
                    domain.append(('date', '>=', date_from))
                if date_to:
                    domain.append(('date', '<=', date_to))

                timesheets = request.env['account.analytic.line'].search_read(domain)
                total_hours = sum(ts.get('unit_amount', 0) for ts in timesheets)
                
                return {
                    'success': True,
                    'data': {
                        'timesheets': timesheets,
                        'total_hours': total_hours,
                        'employee_name': employee.name
                    }
                }
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                vals['employee_id'] = employee_id
                timesheet = request.env['account.analytic.line'].create(vals)
                return {'success': True, 'data': {'id': timesheet.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/project/<int:project_id>/timesheets', type='json', auth='user', methods=['GET'])
    def hr_project_timesheets(self, project_id, **kwargs):
        """API timesheet theo dự án"""
        try:
            project = request.env['project.project'].browse(project_id)
            if not project.exists():
                return {'success': False, 'error': 'Project not found'}

            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            domain = [('project_id', '=', project_id)]
            
            if date_from:
                domain.append(('date', '>=', date_from))
            if date_to:
                domain.append(('date', '<=', date_to))

            timesheets = request.env['account.analytic.line'].search_read(domain)
            total_hours = sum(ts.get('unit_amount', 0) for ts in timesheets)
            total_cost = sum(ts.get('amount', 0) for ts in timesheets)
            
            return {
                'success': True,
                'data': {
                    'timesheets': timesheets,
                    'total_hours': total_hours,
                    'total_cost': total_cost,
                    'project_name': project.name
                }
            }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/task/<int:task_id>/timesheets', type='json', auth='user', methods=['GET'])
    def hr_task_timesheets(self, task_id, **kwargs):
        """API timesheet theo task"""
        try:
            task = request.env['project.task'].browse(task_id)
            if not task.exists():
                return {'success': False, 'error': 'Task not found'}

            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            domain = [('task_id', '=', task_id)]
            
            if date_from:
                domain.append(('date', '>=', date_from))
            if date_to:
                domain.append(('date', '<=', date_to))

            timesheets = request.env['account.analytic.line'].search_read(domain)
            total_hours = sum(ts.get('unit_amount', 0) for ts in timesheets)
            total_cost = sum(ts.get('amount', 0) for ts in timesheets)
            
            return {
                'success': True,
                'data': {
                    'timesheets': timesheets,
                    'total_hours': total_hours,
                    'total_cost': total_cost,
                    'task_name': task.name,
                    'project_name': task.project_id.name if task.project_id else ''
                }
            }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/timesheet/summary', type='json', auth='user', methods=['GET'])
    def hr_timesheet_summary(self, **kwargs):
        """API tóm tắt timesheet"""
        try:
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            employee_id = kwargs.get('employee_id')
            project_id = kwargs.get('project_id')
            
            domain = []
            if date_from:
                domain.append(('date', '>=', date_from))
            if date_to:
                domain.append(('date', '<=', date_to))
            if employee_id:
                domain.append(('employee_id', '=', employee_id))
            if project_id:
                domain.append(('project_id', '=', project_id))

            timesheets = request.env['account.analytic.line'].search(domain)
            
            summary = {
                'total_entries': len(timesheets),
                'total_hours': sum(timesheets.mapped('unit_amount')),
                'total_cost': sum(timesheets.mapped('amount')),
                'employees_count': len(timesheets.mapped('employee_id')),
                'projects_count': len(timesheets.mapped('project_id')),
                'tasks_count': len(timesheets.mapped('task_id')),
                'date_range': {
                    'from': date_from,
                    'to': date_to
                }
            }
            
            return {'success': True, 'data': summary}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/timesheet/validate', type='json', auth='user', methods=['POST'])
    def hr_timesheet_validate(self, **kwargs):
        """API xác nhận timesheet"""
        try:
            timesheet_ids = kwargs.get('timesheet_ids', [])
            if not timesheet_ids:
                return {'success': False, 'error': 'No timesheet IDs provided'}

            timesheets = request.env['account.analytic.line'].browse(timesheet_ids)
            valid_timesheets = timesheets.filtered(lambda t: not t._is_readonly())
            
            if len(valid_timesheets) != len(timesheets):
                return {'success': False, 'error': 'Some timesheets are readonly and cannot be validated'}

            # Custom validation logic can be added here
            for timesheet in valid_timesheets:
                if not timesheet.project_id or not timesheet.employee_id:
                    return {'success': False, 'error': f'Timesheet {timesheet.id} is missing required fields'}

            return {'success': True, 'data': {'validated_count': len(valid_timesheets)}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/timesheet/copy', type='json', auth='user', methods=['POST'])
    def hr_timesheet_copy(self, **kwargs):
        """API sao chép timesheet"""
        try:
            timesheet_id = kwargs.get('timesheet_id')
            copy_data = kwargs.get('copy_data', {})
            
            if not timesheet_id:
                return {'success': False, 'error': 'Timesheet ID is required'}

            original_timesheet = request.env['account.analytic.line'].browse(timesheet_id)
            if not original_timesheet.exists():
                return {'success': False, 'error': 'Original timesheet not found'}

            new_timesheet = original_timesheet.copy(copy_data)
            
            return {'success': True, 'data': {'new_timesheet_id': new_timesheet.id}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= RECRUITMENT MANAGEMENT =======================

    @http.route('/api/hr/applicants', type='json', auth='user', methods=['GET', 'POST'])
    def hr_applicants(self, **kwargs):
        """API quản lý ứng viên - GET (list), POST (create)"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                fields_list = kwargs.get('fields', ['partner_name', 'email_from', 'partner_phone', 'job_id', 'stage_id', 'application_status'])
                applicants = request.env['hr.applicant'].search_read(domain, fields_list)
                return {'success': True, 'data': applicants}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                applicant = request.env['hr.applicant'].create(vals)
                return {'success': True, 'data': {'id': applicant.id, 'name': applicant.partner_name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/applicant/<int:applicant_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_applicant_detail(self, applicant_id, **kwargs):
        """API chi tiết ứng viên - GET, PUT (update), DELETE"""
        try:
            applicant = request.env['hr.applicant'].browse(applicant_id)
            if not applicant.exists():
                return {'success': False, 'error': 'Applicant not found'}

            if request.httprequest.method == 'GET':
                data = applicant.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                applicant.write(vals)
                return {'success': True, 'data': {'id': applicant.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                applicant.write({'active': False})
                return {'success': True, 'data': {'id': applicant.id, 'archived': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/applicant/<int:applicant_id>/status', type='json', auth='user', methods=['GET', 'PUT'])
    def hr_applicant_status(self, applicant_id, **kwargs):
        """API trạng thái ứng viên"""
        try:
            applicant = request.env['hr.applicant'].browse(applicant_id)
            if not applicant.exists():
                return {'success': False, 'error': 'Applicant not found'}

            if request.httprequest.method == 'GET':
                status = {
                    'active': applicant.active,
                    'stage_id': applicant.stage_id.name if applicant.stage_id else '',
                    'application_status': applicant.application_status,
                    'kanban_state': applicant.kanban_state,
                    'refuse_reason_id': applicant.refuse_reason_id.name if applicant.refuse_reason_id else '',
                    'priority': applicant.priority,
                }
                return {'success': True, 'data': status}
            
            elif request.httprequest.method == 'PUT':
                new_status = kwargs.get('status', {})
                applicant.write(new_status)
                return {'success': True, 'data': {'id': applicant.id, 'status_updated': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/applicant/<int:applicant_id>/hire', type='json', auth='user', methods=['POST'])
    def hr_applicant_hire(self, applicant_id, **kwargs):
        """API tuyển dụng ứng viên (tạo employee)"""
        try:
            applicant = request.env['hr.applicant'].browse(applicant_id)
            if not applicant.exists():
                return {'success': False, 'error': 'Applicant not found'}

            employee = applicant.create_employee_from_applicant()
            return {'success': True, 'data': {'employee_id': employee.id, 'employee_name': employee.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/applicant/<int:applicant_id>/refuse', type='json', auth='user', methods=['POST'])
    def hr_applicant_refuse(self, applicant_id, **kwargs):
        """API từ chối ứng viên"""
        try:
            applicant = request.env['hr.applicant'].browse(applicant_id)
            if not applicant.exists():
                return {'success': False, 'error': 'Applicant not found'}

            refuse_reason_id = kwargs.get('refuse_reason_id')
            if refuse_reason_id:
                applicant.write({'refuse_reason_id': refuse_reason_id, 'refuse_date': fields.Datetime.now()})
            
            applicant.archive_applicant()
            return {'success': True, 'data': {'id': applicant.id, 'refused': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/recruitment/jobs', type='json', auth='user', methods=['GET', 'POST'])
    def hr_recruitment_jobs(self, **kwargs):
        """API quản lý vị trí tuyển dụng"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                jobs = request.env['hr.job'].search_read(domain)
                return {'success': True, 'data': jobs}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                job = request.env['hr.job'].create(vals)
                return {'success': True, 'data': {'id': job.id, 'name': job.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/recruitment/job/<int:job_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_recruitment_job_detail(self, job_id, **kwargs):
        """API chi tiết vị trí tuyển dụng"""
        try:
            job = request.env['hr.job'].browse(job_id)
            if not job.exists():
                return {'success': False, 'error': 'Job not found'}

            if request.httprequest.method == 'GET':
                data = job.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                job.write(vals)
                return {'success': True, 'data': {'id': job.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                job.write({'active': False})
                return {'success': True, 'data': {'id': job.id, 'archived': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/recruitment/stages', type='json', auth='user', methods=['GET', 'POST'])
    def hr_recruitment_stages(self, **kwargs):
        """API quản lý giai đoạn tuyển dụng"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                stages = request.env['hr.recruitment.stage'].search_read(domain)
                return {'success': True, 'data': stages}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                stage = request.env['hr.recruitment.stage'].create(vals)
                return {'success': True, 'data': {'id': stage.id, 'name': stage.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/recruitment/stage/<int:stage_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_recruitment_stage_detail(self, stage_id, **kwargs):
        """API chi tiết giai đoạn tuyển dụng"""
        try:
            stage = request.env['hr.recruitment.stage'].browse(stage_id)
            if not stage.exists():
                return {'success': False, 'error': 'Stage not found'}

            if request.httprequest.method == 'GET':
                data = stage.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                stage.write(vals)
                return {'success': True, 'data': {'id': stage.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                stage.unlink()
                return {'success': True, 'data': {'id': stage_id, 'deleted': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/candidates', type='json', auth='user', methods=['GET', 'POST'])
    def hr_candidates(self, **kwargs):
        """API quản lý ứng cử viên"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                candidates = request.env['hr.candidate'].search_read(domain)
                return {'success': True, 'data': candidates}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                candidate = request.env['hr.candidate'].create(vals)
                return {'success': True, 'data': {'id': candidate.id, 'name': candidate.partner_name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/candidate/<int:candidate_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_candidate_detail(self, candidate_id, **kwargs):
        """API chi tiết ứng cử viên"""
        try:
            candidate = request.env['hr.candidate'].browse(candidate_id)
            if not candidate.exists():
                return {'success': False, 'error': 'Candidate not found'}

            if request.httprequest.method == 'GET':
                data = candidate.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                candidate.write(vals)
                return {'success': True, 'data': {'id': candidate.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                candidate.write({'active': False})
                return {'success': True, 'data': {'id': candidate.id, 'archived': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= REPORTS & ANALYTICS =======================

    @http.route('/api/hr/reports/summary', type='json', auth='user', methods=['GET'])
    def hr_reports_summary(self, **kwargs):
        """API báo cáo tổng hợp HR"""
        try:
            # Thống kê tổng quan
            total_employees = request.env['hr.employee'].search_count([('active', '=', True)])
            active_contracts = request.env['hr.contract'].search_count([('state', '=', 'open')])
            pending_leaves = request.env['hr.leave'].search_count([('state', '=', 'confirm')])
            active_insurances = request.env['hr.insurance'].search_count([('state', '=', 'active')])
            total_applicants = request.env['hr.applicant'].search_count([('active', '=', True)])
            
            summary = {
                'total_employees': total_employees,
                'active_contracts': active_contracts,
                'pending_leaves': pending_leaves,
                'active_insurances': active_insurances,
                'total_applicants': total_applicants,
                'generated_at': fields.Datetime.now().isoformat()
            }
            
            return {'success': True, 'data': summary}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/reports/export', type='json', auth='user', methods=['POST'])
    def hr_reports_export(self, **kwargs):
        """API xuất báo cáo Excel/PDF"""
        try:
            report_type = kwargs.get('report_type', 'employee_list')
            export_format = kwargs.get('format', 'excel')
            
            if report_type == 'employee_list':
                employees = request.env['hr.employee'].search([('active', '=', True)])
                if export_format == 'excel':
                    result = employees[0].export_employee_list_excel() if employees else None
                else:
                    result = employees[0].export_employee_list_pdf() if employees else None
                
                return {'success': True, 'data': {'exported': True, 'format': export_format}}
            
            return {'success': False, 'error': 'Unsupported report type'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= BULK OPERATIONS =======================

    @http.route('/api/hr/bulk/update', type='json', auth='user', methods=['POST'])
    def hr_bulk_update(self, **kwargs):
        """API cập nhật hàng loạt"""
        try:
            model_name = kwargs.get('model', 'hr.employee')
            record_ids = kwargs.get('ids', [])
            vals = kwargs.get('vals', {})
            
            records = request.env[model_name].browse(record_ids)
            records.write(vals)
            
            return {'success': True, 'data': {'updated_count': len(records)}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/bulk/delete', type='json', auth='user', methods=['POST'])
    def hr_bulk_delete(self, **kwargs):
        """API xóa hàng loạt (archive)"""
        try:
            model_name = kwargs.get('model', 'hr.employee')
            record_ids = kwargs.get('ids', [])
            
            records = request.env[model_name].browse(record_ids)
            if hasattr(records, 'active'):
                records.write({'active': False})
            else:
                records.unlink()
            
            return {'success': True, 'data': {'archived_count': len(records)}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= ATTENDANCE ADVANCED MANAGEMENT =======================

    @http.route('/api/hr/attendance/summary', type='json', auth='user', methods=['GET'])
    def hr_attendance_summary(self, **kwargs):
        """API tóm tắt chấm công"""
        try:
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            employee_id = kwargs.get('employee_id')
            
            domain = []
            if date_from:
                domain.append(('check_in', '>=', date_from))
            if date_to:
                domain.append(('check_in', '<=', date_to))
            if employee_id:
                domain.append(('employee_id', '=', employee_id))

            attendances = request.env['hr.attendance'].search(domain)
            
            total_hours = sum(attendances.mapped('worked_hours'))
            total_days = len(attendances.mapped('check_in').mapped(lambda d: d.date()))
            
            summary = {
                'total_records': len(attendances),
                'total_hours': total_hours,
                'total_days': total_days,
                'average_hours_per_day': total_hours / total_days if total_days > 0 else 0,
                'employees_count': len(attendances.mapped('employee_id')),
                'late_checkins': len(attendances.filtered(lambda a: a.check_in and a.check_in.hour > 8)),
                'overtime_records': len(attendances.filtered(lambda a: a.worked_hours > 8)),
            }
            
            return {'success': True, 'data': summary}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/attendance/overtime', type='json', auth='user', methods=['GET'])
    def hr_attendance_overtime(self, **kwargs):
        """API tính toán giờ làm thêm"""
        try:
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            employee_id = kwargs.get('employee_id')
            
            domain = [('worked_hours', '>', 8)]
            if date_from:
                domain.append(('check_in', '>=', date_from))
            if date_to:
                domain.append(('check_in', '<=', date_to))
            if employee_id:
                domain.append(('employee_id', '=', employee_id))

            overtime_records = request.env['hr.attendance'].search(domain)
            
            overtime_data = []
            for record in overtime_records:
                overtime_hours = record.worked_hours - 8 if record.worked_hours > 8 else 0
                overtime_data.append({
                    'id': record.id,
                    'employee_name': record.employee_id.name,
                    'date': record.check_in.date().isoformat(),
                    'total_hours': record.worked_hours,
                    'overtime_hours': overtime_hours,
                    'check_in': record.check_in.isoformat(),
                    'check_out': record.check_out.isoformat() if record.check_out else '',
                })
            
            total_overtime = sum(r['overtime_hours'] for r in overtime_data)
            
            return {
                'success': True, 
                'data': {
                    'overtime_records': overtime_data,
                    'total_overtime_hours': total_overtime,
                    'total_records': len(overtime_data)
                }
            }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/attendance/missing', type='json', auth='user', methods=['GET'])
    def hr_attendance_missing(self, **kwargs):
        """API tìm kiếm chấm công thiếu"""
        try:
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            employee_id = kwargs.get('employee_id')
            
            # Tìm những ngày không có chấm công
            domain = []
            if date_from:
                domain.append(('check_in', '>=', date_from))
            if date_to:
                domain.append(('check_in', '<=', date_to))
            if employee_id:
                domain.append(('employee_id', '=', employee_id))

            attendances = request.env['hr.attendance'].search(domain)
            
            # Logic tìm missing attendance (có thể phức tạp hơn tùy theo business rules)
            missing_checkout = attendances.filtered(lambda a: not a.check_out)
            
            missing_data = []
            for record in missing_checkout:
                missing_data.append({
                    'id': record.id,
                    'employee_name': record.employee_id.name,
                    'check_in': record.check_in.isoformat(),
                    'missing_type': 'checkout',
                    'date': record.check_in.date().isoformat(),
                })
            
            return {'success': True, 'data': missing_data}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= PAYROLL ADVANCED MANAGEMENT =======================

    @http.route('/api/hr/payroll/salary-rules', type='json', auth='user', methods=['GET', 'POST'])
    def hr_payroll_salary_rules(self, **kwargs):
        """API quản lý quy tắc lương"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                salary_rules = request.env['hr.salary.rule'].search_read(domain)
                return {'success': True, 'data': salary_rules}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                salary_rule = request.env['hr.salary.rule'].create(vals)
                return {'success': True, 'data': {'id': salary_rule.id, 'name': salary_rule.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/payroll/salary-rule/<int:rule_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_payroll_salary_rule_detail(self, rule_id, **kwargs):
        """API chi tiết quy tắc lương"""
        try:
            salary_rule = request.env['hr.salary.rule'].browse(rule_id)
            if not salary_rule.exists():
                return {'success': False, 'error': 'Salary rule not found'}

            if request.httprequest.method == 'GET':
                data = salary_rule.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                salary_rule.write(vals)
                return {'success': True, 'data': {'id': salary_rule.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                salary_rule.write({'active': False})
                return {'success': True, 'data': {'id': salary_rule.id, 'archived': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/payroll/structures', type='json', auth='user', methods=['GET', 'POST'])
    def hr_payroll_structures(self, **kwargs):
        """API quản lý cấu trúc lương"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                structures = request.env['hr.payroll.structure'].search_read(domain)
                return {'success': True, 'data': structures}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                structure = request.env['hr.payroll.structure'].create(vals)
                return {'success': True, 'data': {'id': structure.id, 'name': structure.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/payroll/structure/<int:structure_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_payroll_structure_detail(self, structure_id, **kwargs):
        """API chi tiết cấu trúc lương"""
        try:
            structure = request.env['hr.payroll.structure'].browse(structure_id)
            if not structure.exists():
                return {'success': False, 'error': 'Payroll structure not found'}

            if request.httprequest.method == 'GET':
                data = structure.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                structure.write(vals)
                return {'success': True, 'data': {'id': structure.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                structure.write({'active': False})
                return {'success': True, 'data': {'id': structure.id, 'archived': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/payslip/<int:payslip_id>/lines', type='json', auth='user', methods=['GET'])
    def hr_payslip_lines(self, payslip_id, **kwargs):
        """API chi tiết dòng bảng lương"""
        try:
            payslip = request.env['hr.payslip'].browse(payslip_id)
            if not payslip.exists():
                return {'success': False, 'error': 'Payslip not found'}

            lines_data = []
            for line in payslip.line_ids:
                lines_data.append({
                    'id': line.id,
                    'name': line.name,
                    'code': line.code,
                    'category_id': line.category_id.name if line.category_id else '',
                    'sequence': line.sequence,
                    'appears_on_payslip': line.appears_on_payslip,
                    'condition_select': line.condition_select,
                    'condition_python': line.condition_python,
                    'condition_range': line.condition_range,
                    'condition_range_min': line.condition_range_min,
                    'condition_range_max': line.condition_range_max,
                    'amount_select': line.amount_select,
                    'amount_fix': line.amount_fix,
                    'amount_python_compute': line.amount_python_compute,
                    'amount_percentage': line.amount_percentage,
                    'amount_percentage_base': line.amount_percentage_base,
                    'quantity': line.quantity,
                    'rate': line.rate,
                    'total': line.total,
                })
            
            return {'success': True, 'data': lines_data}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= LEAVE MANAGEMENT =======================

    # ======================= FINAL ADVANCED FEATURES =======================

    @http.route('/api/hr/dashboard/stats', type='json', auth='user', methods=['GET'])
    def hr_dashboard_stats(self, **kwargs):
        """API thống kê dashboard HR tổng hợp"""
        try:
            # Thống kê nhân viên
            total_employees = request.env['hr.employee'].search_count([('active', '=', True)])
            employees_on_leave = request.env['hr.leave'].search_count([
                ('state', '=', 'validate'),
                ('date_from', '<=', fields.Date.today()),
                ('date_to', '>=', fields.Date.today())
            ])
            
            # Thống kê chấm công hôm nay
            today_attendances = request.env['hr.attendance'].search_count([
                ('check_in', '>=', fields.Datetime.now().replace(hour=0, minute=0, second=0)),
                ('check_in', '<', fields.Datetime.now().replace(hour=23, minute=59, second=59))
            ])
            
            # Thống kê tuyển dụng
            pending_applicants = request.env['hr.applicant'].search_count([
                ('active', '=', True),
                ('stage_id.hired_stage', '=', False)
            ])
            
            # Thống kê bảo hiểm
            active_insurances = request.env['hr.insurance'].search_count([('state', '=', 'active')])
            
            # Thống kê project
            active_projects = request.env['project.project'].search_count([('active', '=', True)])
            
            stats = {
                'employees': {
                    'total': total_employees,
                    'on_leave_today': employees_on_leave,
                    'attendance_today': today_attendances,
                    'attendance_rate': (today_attendances / total_employees * 100) if total_employees > 0 else 0
                },
                'recruitment': {
                    'pending_applicants': pending_applicants
                },
                'insurance': {
                    'active_policies': active_insurances
                },
                'projects': {
                    'active_projects': active_projects
                },
                'generated_at': fields.Datetime.now().isoformat()
            }
            
            return {'success': True, 'data': stats}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/analytics/trend', type='json', auth='user', methods=['GET', 'POST'])
    def hr_analytics_trend(self, **kwargs):
        """API phân tích xu hướng HR"""
        try:
            period = kwargs.get('period', 'month')  # week, month, quarter, year
            metric = kwargs.get('metric', 'attendance')  # attendance, leave, recruitment
            
            # Tính toán trend dựa trên period và metric
            if metric == 'attendance':
                # Trend chấm công
                domain = []
                if period == 'month':
                    domain.append(('check_in', '>=', fields.Datetime.now().replace(day=1)))
                
                attendances = request.env['hr.attendance'].search(domain)
                trend_data = {
                    'total_records': len(attendances),
                    'total_hours': sum(attendances.mapped('worked_hours')),
                    'avg_hours_per_day': sum(attendances.mapped('worked_hours')) / 30 if len(attendances) > 0 else 0
                }
                
            elif metric == 'leave':
                # Trend nghỉ phép
                domain = []
                if period == 'month':
                    domain.append(('date_from', '>=', fields.Date.today().replace(day=1)))
                
                leaves = request.env['hr.leave'].search(domain)
                trend_data = {
                    'total_leaves': len(leaves),
                    'approved_leaves': len(leaves.filtered(lambda l: l.state == 'validate')),
                    'pending_leaves': len(leaves.filtered(lambda l: l.state == 'confirm'))
                }
                
            elif metric == 'recruitment':
                # Trend tuyển dụng
                domain = []
                if period == 'month':
                    domain.append(('create_date', '>=', fields.Datetime.now().replace(day=1)))
                
                applicants = request.env['hr.applicant'].search(domain)
                trend_data = {
                    'total_applicants': len(applicants),
                    'hired': len(applicants.filtered(lambda a: a.stage_id.hired_stage == True)),
                    'rejected': len(applicants.filtered(lambda a: a.active == False))
                }
            
            return {'success': True, 'data': {'metric': metric, 'period': period, 'trend': trend_data}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/notifications', type='json', auth='user', methods=['GET'])
    def hr_notifications(self, **kwargs):
        """API thông báo HR quan trọng"""
        try:
            notifications = []
            
            # Kiểm tra hợp đồng sắp hết hạn
            contracts_expiring = request.env['hr.contract'].search([
                ('date_end', '<=', fields.Date.today() + timedelta(days=30)),
                ('date_end', '>=', fields.Date.today()),
                ('state', '=', 'open')
            ])
            
            if contracts_expiring:
                notifications.append({
                    'type': 'warning',
                    'title': 'Hợp đồng sắp hết hạn',
                    'message': f'{len(contracts_expiring)} hợp đồng sẽ hết hạn trong 30 ngày tới',
                    'count': len(contracts_expiring)
                })
            
            # Kiểm tra nghỉ phép chờ duyệt
            pending_leaves = request.env['hr.leave'].search([('state', '=', 'confirm')])
            if pending_leaves:
                notifications.append({
                    'type': 'info',
                    'title': 'Nghỉ phép chờ duyệt',
                    'message': f'{len(pending_leaves)} đơn nghỉ phép đang chờ phê duyệt',
                    'count': len(pending_leaves)
                })
            
            # Kiểm tra bảo hiểm cần xử lý
            pending_insurance = request.env['hr.insurance'].search([('state', '=', 'draft')])
            if pending_insurance:
                notifications.append({
                    'type': 'info',
                    'title': 'Bảo hiểm cần xử lý',
                    'message': f'{len(pending_insurance)} hồ sơ bảo hiểm cần xử lý',
                    'count': len(pending_insurance)
                })
            
            return {'success': True, 'data': notifications}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/export/complete', type='json', auth='user', methods=['POST'])
    def hr_export_complete(self, **kwargs):
        """API xuất báo cáo tổng hợp toàn bộ HR"""
        try:
            export_type = kwargs.get('type', 'excel')  # excel, pdf, csv
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            
            # Thu thập dữ liệu từ tất cả modules
            employees = request.env['hr.employee'].search([('active', '=', True)])
            contracts = request.env['hr.contract'].search([('state', '=', 'open')])
            attendances = request.env['hr.attendance'].search([])
            leaves = request.env['hr.leave'].search([])
            insurances = request.env['hr.insurance'].search([])
            
            # Tạo export data
            export_data = {
                'employees': len(employees),
                'contracts': len(contracts),
                'attendances': len(attendances),
                'leaves': len(leaves),
                'insurances': len(insurances),
                'export_date': fields.Datetime.now().isoformat(),
                'date_range': {'from': date_from, 'to': date_to}
            }
            
            # Thực hiện export (placeholder - cần implement thực tế)
            result = {
                'exported': True,
                'format': export_type,
                'records_count': sum([len(employees), len(contracts), len(attendances), len(leaves), len(insurances)]),
                'download_url': f'/hr/export/download/{export_type}'  # Placeholder URL
            }
            
            return {'success': True, 'data': result}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= HR EXPENSE MANAGEMENT =======================

    @http.route('/api/hr/expenses', type='json', auth='user', methods=['GET', 'POST'])
    def hr_expenses(self, **kwargs):
        """API quản lý chi phí"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                expenses = request.env['hr.expense'].search_read(domain)
                return {'success': True, 'data': expenses}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                expense = request.env['hr.expense'].create(vals)
                return {'success': True, 'data': {'id': expense.id, 'name': expense.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/expense/<int:expense_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_expense_detail(self, expense_id, **kwargs):
        """API chi tiết chi phí"""
        try:
            expense = request.env['hr.expense'].browse(expense_id)
            if not expense.exists():
                return {'success': False, 'error': 'Expense not found'}

            if request.httprequest.method == 'GET':
                data = expense.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                expense.write(vals)
                return {'success': True, 'data': {'id': expense.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                expense.write({'state': 'cancel'})
                return {'success': True, 'data': {'id': expense.id, 'cancelled': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/expense-sheets', type='json', auth='user', methods=['GET', 'POST'])
    def hr_expense_sheets(self, **kwargs):
        """API quản lý bảng chi phí"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                sheets = request.env['hr.expense.sheet'].search_read(domain)
                return {'success': True, 'data': sheets}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                sheet = request.env['hr.expense.sheet'].create(vals)
                return {'success': True, 'data': {'id': sheet.id, 'name': sheet.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/expense-sheet/<int:sheet_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_expense_sheet_detail(self, sheet_id, **kwargs):
        """API chi tiết bảng chi phí"""
        try:
            sheet = request.env['hr.expense.sheet'].browse(sheet_id)
            if not sheet.exists():
                return {'success': False, 'error': 'Expense sheet not found'}

            if request.httprequest.method == 'GET':
                data = sheet.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                sheet.write(vals)
                return {'success': True, 'data': {'id': sheet.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                sheet.write({'state': 'cancel'})
                return {'success': True, 'data': {'id': sheet.id, 'cancelled': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/expense-sheet/<int:sheet_id>/submit', type='json', auth='user', methods=['POST'])
    def hr_expense_sheet_submit(self, sheet_id, **kwargs):
        """API nộp bảng chi phí"""
        try:
            sheet = request.env['hr.expense.sheet'].browse(sheet_id)
            if not sheet.exists():
                return {'success': False, 'error': 'Expense sheet not found'}

            sheet.action_submit_sheet()
            return {'success': True, 'data': {'id': sheet.id, 'state': sheet.state}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/expense-sheet/<int:sheet_id>/approve', type='json', auth='user', methods=['POST'])
    def hr_expense_sheet_approve(self, sheet_id, **kwargs):
        """API phê duyệt bảng chi phí"""
        try:
            sheet = request.env['hr.expense.sheet'].browse(sheet_id)
            if not sheet.exists():
                return {'success': False, 'error': 'Expense sheet not found'}

            sheet.approve_expense_sheets()
            return {'success': True, 'data': {'id': sheet.id, 'state': sheet.state}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= HR HOMEWORKING MANAGEMENT =======================

    @http.route('/api/hr/homeworking-requests', type='json', auth='user', methods=['GET', 'POST'])
    def hr_homeworking_requests(self, **kwargs):
        """API quản lý yêu cầu làm việc tại nhà"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                requests = request.env['hr.homeworking'].search_read(domain)
                return {'success': True, 'data': requests}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                homeworking = request.env['hr.homeworking'].create(vals)
                return {'success': True, 'data': {'id': homeworking.id, 'name': homeworking.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/homeworking-request/<int:request_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_homeworking_request_detail(self, request_id, **kwargs):
        """API chi tiết yêu cầu làm việc tại nhà"""
        try:
            homeworking = request.env['hr.homeworking'].browse(request_id)
            if not homeworking.exists():
                return {'success': False, 'error': 'Homeworking request not found'}

            if request.httprequest.method == 'GET':
                data = homeworking.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                homeworking.write(vals)
                return {'success': True, 'data': {'id': homeworking.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                homeworking.write({'state': 'cancel'})
                return {'success': True, 'data': {'id': homeworking.id, 'cancelled': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/work-locations', type='json', auth='user', methods=['GET', 'POST'])
    def hr_work_locations(self, **kwargs):
        """API quản lý địa điểm làm việc"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                locations = request.env['hr.work.location'].search_read(domain)
                return {'success': True, 'data': locations}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                location = request.env['hr.work.location'].create(vals)
                return {'success': True, 'data': {'id': location.id, 'name': location.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= HR WORK ENTRY MANAGEMENT =======================

    @http.route('/api/hr/work-entries', type='json', auth='user', methods=['GET', 'POST'])
    def hr_work_entries(self, **kwargs):
        """API quản lý bút toán công việc"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                work_entries = request.env['hr.work.entry'].search_read(domain)
                return {'success': True, 'data': work_entries}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                work_entry = request.env['hr.work.entry'].create(vals)
                return {'success': True, 'data': {'id': work_entry.id, 'name': work_entry.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/work-entry/<int:entry_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_work_entry_detail(self, entry_id, **kwargs):
        """API chi tiết bút toán công việc"""
        try:
            work_entry = request.env['hr.work.entry'].browse(entry_id)
            if not work_entry.exists():
                return {'success': False, 'error': 'Work entry not found'}

            if request.httprequest.method == 'GET':
                data = work_entry.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                work_entry.write(vals)
                return {'success': True, 'data': {'id': work_entry.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                work_entry.write({'state': 'cancelled'})
                return {'success': True, 'data': {'id': work_entry.id, 'cancelled': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/work-entries', type='json', auth='user', methods=['GET'])
    def hr_employee_work_entries(self, employee_id, **kwargs):
        """API bút toán công việc theo nhân viên"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            domain = [('employee_id', '=', employee_id)]
            
            if date_from:
                domain.append(('date_start', '>=', date_from))
            if date_to:
                domain.append(('date_stop', '<=', date_to))

            work_entries = request.env['hr.work.entry'].search_read(domain)
            return {'success': True, 'data': work_entries}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= HR CALENDAR MANAGEMENT =======================

    @http.route('/api/hr/calendar-events', type='json', auth='user', methods=['GET', 'POST'])
    def hr_calendar_events(self, **kwargs):
        """API quản lý sự kiện lịch"""
        try:
            if request.httprequest.method == 'GET':
                domain = kwargs.get('domain', [])
                events = request.env['calendar.event'].search_read(domain)
                return {'success': True, 'data': events}
            
            elif request.httprequest.method == 'POST':
                vals = kwargs.get('vals', {})
                event = request.env['calendar.event'].create(vals)
                return {'success': True, 'data': {'id': event.id, 'name': event.name}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/calendar-event/<int:event_id>', type='json', auth='user', methods=['GET', 'PUT', 'DELETE'])
    def hr_calendar_event_detail(self, event_id, **kwargs):
        """API chi tiết sự kiện lịch"""
        try:
            event = request.env['calendar.event'].browse(event_id)
            if not event.exists():
                return {'success': False, 'error': 'Calendar event not found'}

            if request.httprequest.method == 'GET':
                data = event.read()[0]
                return {'success': True, 'data': data}
            
            elif request.httprequest.method == 'PUT':
                vals = kwargs.get('vals', {})
                event.write(vals)
                return {'success': True, 'data': {'id': event.id, 'updated': True}}
            
            elif request.httprequest.method == 'DELETE':
                event.unlink()
                return {'success': True, 'data': {'id': event_id, 'deleted': True}}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/calendar-events', type='json', auth='user', methods=['GET'])
    def hr_employee_calendar_events(self, employee_id, **kwargs):
        """API sự kiện lịch theo nhân viên"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            
            domain = [('partner_ids', 'in', [employee.user_id.partner_id.id])]
            if date_from:
                domain.append(('start', '>=', date_from))
            if date_to:
                domain.append(('stop', '<=', date_to))

            events = request.env['calendar.event'].search_read(domain)
            return {'success': True, 'data': events}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= HR FLEET MANAGEMENT =======================

    @http.route('/api/hr/fleet-vehicles', type='json', auth='user', methods=['GET'])
    def hr_fleet_vehicles(self, **kwargs):
        """API quản lý xe công ty cho HR"""
        try:
            domain = kwargs.get('domain', [])
            vehicles = request.env['fleet.vehicle'].search_read(domain)
            return {'success': True, 'data': vehicles}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/fleet-vehicles', type='json', auth='user', methods=['GET'])
    def hr_employee_fleet_vehicles(self, employee_id, **kwargs):
        """API xe công ty theo nhân viên"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            vehicles = request.env['fleet.vehicle'].search_read([
                ('driver_id', '=', employee.user_id.partner_id.id)
            ])
            return {'success': True, 'data': vehicles}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= ADVANCED HR UTILITIES =======================

    @http.route('/api/hr/employee/<int:employee_id>/document-check', type='json', auth='user', methods=['GET'])
    def hr_employee_document_check(self, employee_id, **kwargs):
        """API kiểm tra tài liệu nhân viên"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            documents_status = {
                'has_work_permit': bool(employee.work_permit_scheduled_activity),
                'work_permit_expiry': employee.work_permit_expiration_date.isoformat() if employee.work_permit_expiration_date else '',
                'has_id_card': bool(employee.id_card),
                'has_driving_license': bool(employee.driving_license),
                'documents_complete': True,  # Logic check
            }
            
            # Check if documents are complete
            missing_docs = []
            if not employee.work_permit_scheduled_activity:
                missing_docs.append('work_permit')
            if not employee.id_card:
                missing_docs.append('id_card')
            
            documents_status['missing_documents'] = missing_docs
            documents_status['documents_complete'] = len(missing_docs) == 0
            
            return {'success': True, 'data': documents_status}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/employee/<int:employee_id>/performance-summary', type='json', auth='user', methods=['GET'])
    def hr_employee_performance_summary(self, employee_id, **kwargs):
        """API tóm tắt hiệu suất nhân viên"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'success': False, 'error': 'Employee not found'}

            # Attendance summary
            current_month_attendances = request.env['hr.attendance'].search([
                ('employee_id', '=', employee_id),
                ('check_in', '>=', fields.Date.today().replace(day=1)),
            ])
            
            # Timesheet summary 
            current_month_timesheets = request.env['account.analytic.line'].search([
                ('employee_id', '=', employee_id),
                ('date', '>=', fields.Date.today().replace(day=1)),
            ])
            
            # Leave summary
            current_month_leaves = request.env['hr.leave'].search([
                ('employee_id', '=', employee_id),
                ('date_from', '>=', fields.Date.today().replace(day=1)),
                ('state', '=', 'validate'),
            ])
            
            performance_summary = {
                'attendance': {
                    'total_days': len(current_month_attendances),
                    'total_hours': sum(current_month_attendances.mapped('worked_hours')),
                    'avg_hours_per_day': sum(current_month_attendances.mapped('worked_hours')) / len(current_month_attendances) if current_month_attendances else 0,
                },
                'timesheet': {
                    'total_entries': len(current_month_timesheets),
                    'total_hours': sum(current_month_timesheets.mapped('unit_amount')),
                    'projects_count': len(current_month_timesheets.mapped('project_id')),
                },
                'leaves': {
                    'total_leaves': len(current_month_leaves),
                    'total_days': sum(current_month_leaves.mapped('number_of_days')),
                },
                'period': f"{fields.Date.today().strftime('%B %Y')}",
            }
            
            return {'success': True, 'data': performance_summary}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/hr/search/global', type='json', auth='user', methods=['GET'])
    def hr_global_search(self, **kwargs):
        """API tìm kiếm toàn cục trong HR"""
        try:
            search_term = kwargs.get('search_term', '')
            if not search_term:
                return {'success': False, 'error': 'Search term is required'}
            
            results = {
                'employees': [],
                'departments': [],
                'jobs': [],
                'projects': [],
                'leaves': [],
                'expenses': [],
            }
            
            # Search employees
            employees = request.env['hr.employee'].search([
                '|', ('name', 'ilike', search_term),
                ('work_email', 'ilike', search_term)
            ], limit=10)
            results['employees'] = [{'id': e.id, 'name': e.name, 'email': e.work_email} for e in employees]
            
            # Search departments
            departments = request.env['hr.department'].search([
                ('name', 'ilike', search_term)
            ], limit=5)
            results['departments'] = [{'id': d.id, 'name': d.name} for d in departments]
            
            # Search jobs
            jobs = request.env['hr.job'].search([
                ('name', 'ilike', search_term)
            ], limit=5)
            results['jobs'] = [{'id': j.id, 'name': j.name} for j in jobs]
            
            # Search projects
            projects = request.env['project.project'].search([
                ('name', 'ilike', search_term)
            ], limit=5)
            results['projects'] = [{'id': p.id, 'name': p.name} for p in projects]
            
            return {'success': True, 'data': results}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ======================= END OF HR API CONTROLLER =======================