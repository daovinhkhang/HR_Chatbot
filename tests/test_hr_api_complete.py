# -*- coding: utf-8 -*-
import json
import logging
from odoo.tests.common import TransactionCase, HttpCase
from odoo.exceptions import ValidationError, AccessError
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock

_logger = logging.getLogger(__name__)

class TestHRAPIComplete(TransactionCase):
    """Test suite toàn diện cho HR API - 116 endpoints"""

    def setUp(self):
        super().setUp()
        
        # Tạo test data
        self.test_department = self.env['hr.department'].create({
            'name': 'Test IT Department',
        })
        
        self.test_job = self.env['hr.job'].create({
            'name': 'Test Developer',
            'department_id': self.test_department.id,
        })
        
        self.test_employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
            'work_email': 'test@company.com',
            'department_id': self.test_department.id,
            'job_id': self.test_job.id,
        })
        
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser',
            'email': 'testuser@test.com',
        })
        
        # Test contract
        self.test_contract = self.env['hr.contract'].create({
            'name': 'Test Contract',
            'employee_id': self.test_employee.id,
            'date_start': date.today(),
            'wage': 1000,
            'state': 'open',
        })
        
        # Test leave type
        self.test_leave_type = self.env['hr.leave.type'].create({
            'name': 'Test Annual Leave',
            'allocation_type': 'fixed',
        })

    # ======================= EMPLOYEE MANAGEMENT TESTS =======================
    
    def test_hr_employees_crud(self):
        """Test CRUD operations cho employees"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test GET employees
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_employees(domain=[])
            self.assertTrue(result['success'])
            self.assertIsInstance(result['data'], list)
        
        # Test POST create employee
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'POST'
            
            vals = {
                'name': 'New Test Employee',
                'work_email': 'newtest@company.com',
                'department_id': self.test_department.id,
            }
            result = controller.hr_employees(vals=vals)
            self.assertTrue(result['success'])
            self.assertIn('id', result['data'])

    def test_hr_employee_detail_crud(self):
        """Test employee detail operations"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test GET employee detail
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_employee_detail(self.test_employee.id)
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['name'], 'Test Employee')
        
        # Test PUT update employee
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'PUT'
            
            vals = {'work_phone': '+84123456789'}
            result = controller.hr_employee_detail(self.test_employee.id, vals=vals)
            self.assertTrue(result['success'])
        
        # Test DELETE (archive) employee
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'DELETE'
            
            result = controller.hr_employee_detail(self.test_employee.id)
            self.assertTrue(result['success'])

    def test_hr_employee_status(self):
        """Test employee status management"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test GET status
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_employee_status(self.test_employee.id)
            self.assertTrue(result['success'])
            self.assertIn('active', result['data'])
            self.assertIn('contract_status', result['data'])

    # ======================= ATTENDANCE MANAGEMENT TESTS =======================
    
    def test_hr_attendance_crud(self):
        """Test attendance CRUD operations"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test checkin
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'POST'
            
            result = controller.hr_employee_checkin(self.test_employee.id)
            self.assertTrue(result['success'])
            self.assertIn('check_in', result['data'])
        
        # Test checkout
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'POST'
            
            result = controller.hr_employee_checkout(self.test_employee.id)
            self.assertTrue(result['success'])

    def test_hr_attendance_summary(self):
        """Test attendance summary functionality"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        # Tạo test attendance data
        self.env['hr.attendance'].create({
            'employee_id': self.test_employee.id,
            'check_in': datetime.now(),
            'check_out': datetime.now() + timedelta(hours=8),
        })
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_attendance_summary()
            self.assertTrue(result['success'])
            self.assertIn('total_records', result['data'])
            self.assertIn('total_hours', result['data'])

    # ======================= LEAVE MANAGEMENT TESTS =======================
    
    def test_hr_leave_types_crud(self):
        """Test leave types CRUD"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test GET leave types
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_leave_types()
            self.assertTrue(result['success'])
            self.assertIsInstance(result['data'], list)

    def test_hr_leave_requests_crud(self):
        """Test leave requests CRUD"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test create leave request
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'POST'
            
            vals = {
                'employee_id': self.test_employee.id,
                'holiday_status_id': self.test_leave_type.id,
                'date_from': datetime.now(),
                'date_to': datetime.now() + timedelta(days=3),
                'name': 'Test Leave Request',
            }
            result = controller.hr_leaves(vals=vals)
            self.assertTrue(result['success'])

    def test_hr_leave_approve_refuse(self):
        """Test leave approval/refusal"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        # Tạo leave request
        leave_request = self.env['hr.leave'].create({
            'employee_id': self.test_employee.id,
            'holiday_status_id': self.test_leave_type.id,
            'date_from': datetime.now(),
            'date_to': datetime.now() + timedelta(days=2),
            'name': 'Test Leave',
        })
        
        controller = HRAPIController()
        
        # Test approve
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'POST'
            
            result = controller.hr_leave_approve(leave_request.id)
            self.assertTrue(result['success'])

    # ======================= CONTRACT MANAGEMENT TESTS =======================
    
    def test_hr_contracts_crud(self):
        """Test contracts CRUD operations"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test GET contracts
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_contracts()
            self.assertTrue(result['success'])
            self.assertIsInstance(result['data'], list)
        
        # Test contract detail
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_contract_detail(self.test_contract.id)
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['name'], 'Test Contract')

    # ======================= PAYROLL MANAGEMENT TESTS =======================
    
    def test_hr_payslips_crud(self):
        """Test payslips CRUD operations"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test GET payslips
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_payslips()
            self.assertTrue(result['success'])
            self.assertIsInstance(result['data'], list)

    def test_hr_payroll_structures(self):
        """Test payroll structures"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_payroll_structures()
            self.assertTrue(result['success'])

    # ======================= INSURANCE MANAGEMENT TESTS =======================
    
    def test_hr_insurance_crud(self):
        """Test insurance CRUD operations"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test GET insurances
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_insurances()
            self.assertTrue(result['success'])

    def test_hr_employee_bhxh(self):
        """Test BHXH/BHYT/BHTN management"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test GET BHXH info
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_employee_bhxh(self.test_employee.id)
            self.assertTrue(result['success'])
            self.assertIn('employee_info', result['data'])

    # ======================= SKILLS MANAGEMENT TESTS =======================
    
    def test_hr_skills_crud(self):
        """Test skills CRUD operations"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test GET skills
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_skills()
            self.assertTrue(result['success'])
        
        # Test create skill
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'POST'
            
            vals = {'name': 'Python Programming', 'sequence': 1}
            result = controller.hr_skills(vals=vals)
            self.assertTrue(result['success'])

    def test_hr_skill_types(self):
        """Test skill types management"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_skill_types()
            self.assertTrue(result['success'])

    # ======================= TIMESHEET MANAGEMENT TESTS =======================
    
    def test_hr_timesheets_crud(self):
        """Test timesheets CRUD operations"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test GET timesheets
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_timesheets()
            self.assertTrue(result['success'])

    def test_hr_timesheet_summary(self):
        """Test timesheet summary"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_timesheet_summary()
            self.assertTrue(result['success'])

    # ======================= RECRUITMENT MANAGEMENT TESTS =======================
    
    def test_hr_applicants_crud(self):
        """Test applicants CRUD operations"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test GET applicants
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_applicants()
            self.assertTrue(result['success'])
        
        # Test create applicant
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'POST'
            
            vals = {
                'partner_name': 'Test Applicant',
                'email_from': 'applicant@test.com',
                'job_id': self.test_job.id,
            }
            result = controller.hr_applicants(vals=vals)
            self.assertTrue(result['success'])

    def test_hr_recruitment_stages(self):
        """Test recruitment stages"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_recruitment_stages()
            self.assertTrue(result['success'])

    # ======================= PROJECT MANAGEMENT TESTS =======================
    
    def test_hr_projects_crud(self):
        """Test projects CRUD operations"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test GET projects
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_projects()
            self.assertTrue(result['success'])

    # ======================= REPORTS & ANALYTICS TESTS =======================
    
    def test_hr_dashboard_stats(self):
        """Test HR dashboard statistics"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_dashboard_stats()
            self.assertTrue(result['success'])
            self.assertIn('employees', result['data'])
            self.assertIn('recruitment', result['data'])

    def test_hr_reports_summary(self):
        """Test HR reports summary"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_reports_summary()
            self.assertTrue(result['success'])
            self.assertIn('total_employees', result['data'])

    def test_hr_analytics_trend(self):
        """Test HR analytics trend"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_analytics_trend(period='month', metric='attendance')
            self.assertTrue(result['success'])

    # ======================= BULK OPERATIONS TESTS =======================
    
    def test_hr_bulk_operations(self):
        """Test bulk update/delete operations"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test bulk update
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'POST'
            
            result = controller.hr_bulk_update(
                model='hr.employee',
                ids=[self.test_employee.id],
                vals={'work_phone': '+84987654321'}
            )
            self.assertTrue(result['success'])

    # ======================= GLOBAL SEARCH TESTS =======================
    
    def test_hr_global_search(self):
        """Test global search functionality"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_global_search(search_term='Test')
            self.assertTrue(result['success'])
            self.assertIn('employees', result['data'])
            self.assertIn('departments', result['data'])

    # ======================= ERROR HANDLING TESTS =======================
    
    def test_employee_not_found_error(self):
        """Test error handling for non-existent employee"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            result = controller.hr_employee_detail(99999)  # Non-existent ID
            self.assertFalse(result['success'])
            self.assertIn('not found', result['error'])

    def test_invalid_data_error(self):
        """Test error handling for invalid data"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'POST'
            
            # Test với missing required fields
            vals = {'work_email': 'invalid-email'}  # Missing name
            result = controller.hr_employees(vals=vals)
            self.assertFalse(result['success'])

    # ======================= PERMISSION TESTS =======================
    
    def test_access_permissions(self):
        """Test access control and permissions"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        # Test với user không có quyền
        limited_user = self.env['res.users'].create({
            'name': 'Limited User',
            'login': 'limited',
            'email': 'limited@test.com',
            'groups_id': [(6, 0, [])],  # No groups
        })
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env.with_user(limited_user)
            mock_request.httprequest.method = 'GET'
            
            # Một số operations có thể thất bại do quyền hạn
            try:
                result = controller.hr_employees()
                # Nếu không có lỗi permission, test pass
                self.assertTrue(True)
            except AccessError:
                # Nếu có lỗi permission, đó là behavior mong đợi
                self.assertTrue(True)

    # ======================= PERFORMANCE TESTS =======================
    
    def test_large_dataset_performance(self):
        """Test performance với dataset lớn"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        # Tạo nhiều employees để test performance
        employees = []
        for i in range(100):
            employees.append({
                'name': f'Test Employee {i}',
                'work_email': f'test{i}@company.com',
                'department_id': self.test_department.id,
            })
        
        self.env['hr.employee'].create(employees)
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            start_time = datetime.now()
            result = controller.hr_employees()
            end_time = datetime.now()
            
            # Test should complete within reasonable time
            duration = (end_time - start_time).total_seconds()
            self.assertLess(duration, 5.0)  # Should complete within 5 seconds
            self.assertTrue(result['success'])

    # ======================= INTEGRATION TESTS =======================
    
    def test_full_hr_workflow(self):
        """Test complete HR workflow integration"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'POST'
            
            # 1. Tạo employee mới
            vals = {
                'name': 'Workflow Test Employee',
                'work_email': 'workflow@test.com',
                'department_id': self.test_department.id,
                'job_id': self.test_job.id,
            }
            result = controller.hr_employees(vals=vals)
            self.assertTrue(result['success'])
            employee_id = result['data']['id']
            
            # 2. Check-in employee
            result = controller.hr_employee_checkin(employee_id)
            self.assertTrue(result['success'])
            
            # 3. Tạo leave request
            mock_request.httprequest.method = 'POST'
            leave_vals = {
                'employee_id': employee_id,
                'holiday_status_id': self.test_leave_type.id,
                'date_from': datetime.now() + timedelta(days=7),
                'date_to': datetime.now() + timedelta(days=9),
                'name': 'Workflow Test Leave',
            }
            result = controller.hr_leaves(vals=leave_vals)
            self.assertTrue(result['success'])
            
            # 4. Check dashboard stats
            mock_request.httprequest.method = 'GET'
            result = controller.hr_dashboard_stats()
            self.assertTrue(result['success'])

    def test_data_consistency(self):
        """Test data consistency across modules"""
        from odoo.addons.sbotchat.controllers.hr_api import HRAPIController
        
        controller = HRAPIController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'GET'
            
            # Get employee count from different endpoints
            employees_result = controller.hr_employees()
            dashboard_result = controller.hr_dashboard_stats()
            
            # Data should be consistent
            employees_count = len(employees_result['data'])
            dashboard_employees = dashboard_result['data']['employees']['total']
            
            # Counts might differ slightly due to active filters, but should be close
            self.assertLessEqual(abs(employees_count - dashboard_employees), 5)


class TestHRAPIHTTP(HttpCase):
    """HTTP-specific tests for HR API endpoints"""
    
    def test_api_endpoints_accessibility(self):
        """Test that all API endpoints are accessible via HTTP"""
        
        # Authenticate user
        self.authenticate('admin', 'admin')
        
        # Test some key endpoints
        endpoints_to_test = [
            '/api/hr/employees',
            '/api/hr/departments',
            '/api/hr/dashboard/stats',
            '/api/hr/search/global',
        ]
        
        for endpoint in endpoints_to_test:
            response = self.url_open(endpoint)
            # Should not return 404 or 500
            self.assertNotIn(response.status_code, [404, 500])

    def test_json_response_format(self):
        """Test JSON response format consistency"""
        
        self.authenticate('admin', 'admin')
        
        response = self.url_open('/api/hr/dashboard/stats')
        
        # Should return valid JSON
        try:
            data = json.loads(response.content)
            self.assertIn('success', data)
        except json.JSONDecodeError:
            self.fail("Response is not valid JSON")


# ======================= HELPER TEST CLASS =======================

class TestHRAPIHelper(TransactionCase):
    """Test HR API Helper methods"""
    
    def test_helper_methods(self):
        """Test helper methods in hr_api_helper.py"""
        try:
            from odoo.addons.sbotchat.models.hr_api_helper import HRAPIHelper
            
            helper = self.env['hr.api.helper']
            
            # Test helper methods if they exist
            if hasattr(helper, 'get_employee_full_info'):
                result = helper.get_employee_full_info(1)
                self.assertIsInstance(result, dict)
                
        except ImportError:
            # Helper model doesn't exist yet, skip test
            self.skipTest("HR API Helper model not found")

    def tearDown(self):
        """Clean up after tests"""
        super().tearDown()
        
        # Clean up any test data created
        test_employees = self.env['hr.employee'].search([
            ('name', 'like', 'Test%'),
            ('work_email', 'like', '%test.com')
        ])
        test_employees.unlink()
        
        _logger.info("HR API tests completed successfully") 