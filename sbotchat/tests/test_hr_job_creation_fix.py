# -*- coding: utf-8 -*-
import json
import logging
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)

class TestHRJobCreationFix(TransactionCase):
    """Test for HR Job Creation Permission Fix"""

    def setUp(self):
        super(TestHRJobCreationFix, self).setUp()
        
        # Tạo user thông thường
        self.user_employee = self.env['res.users'].create({
            'name': 'Test Employee',
            'login': 'test_employee',
            'email': 'test@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        
        # Tạo HR user
        self.user_hr = self.env['res.users'].create({
            'name': 'Test HR User',
            'login': 'test_hr_user',
            'email': 'hr@example.com',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('hr.group_hr_user').id
            ])]
        })
        
        # Tạo department để test
        self.department = self.env['hr.department'].create({
            'name': 'Test Department'
        })

    def test_hr_create_job_permission_basic_user(self):
        """Test tạo job position với user thông thường"""
        _logger.info("=== Test tạo job position với user thông thường ===")
        
        # Switch to basic user
        hr_helper = self.env['hr.api.helper'].with_user(self.user_employee)
        
        vals = {
            'name': 'Software Developer',
            'department_id': self.department.id,
            'no_of_recruitment': 2
        }
        
        try:
            result = hr_helper.create_job(vals)
            _logger.info(f"✅ Tạo job thành công: {result}")
            
            # Kiểm tra kết quả
            self.assertTrue(result.get('id'), "Job ID should be returned")
            self.assertEqual(result.get('name'), 'Software Developer')
            self.assertTrue(result.get('created'), "Created flag should be True")
            
        except Exception as e:
            _logger.error(f"❌ Lỗi khi tạo job với user thông thường: {str(e)}")
            self.fail(f"Không thể tạo job với user thông thường: {str(e)}")

    def test_hr_create_job_via_controller(self):
        """Test tạo job position thông qua controller method"""
        _logger.info("=== Test tạo job position thông qua controller ===")
        
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        controller = SbotchatController()
        
        # Simulate request environment
        with self.env.registry.cursor() as cr:
            env = self.env(cr=cr, user=self.user_employee.id)
            
            # Mock request.env
            import odoo.http as http
            original_env = getattr(http.request, 'env', None)
            http.request.env = env
            
            try:
                result = controller._hr_create_job(
                    name='Python Developer',
                    department_id=self.department.id,
                    expected_employees=3
                )
                
                _logger.info(f"✅ Controller result: {result}")
                
                # Kiểm tra kết quả
                if result.get('error'):
                    _logger.error(f"❌ Controller error: {result['error']}")
                    self.fail(f"Controller trả về lỗi: {result['error']}")
                else:
                    self.assertTrue(result.get('success'), "Success should be True")
                    self.assertTrue(result.get('job_id'), "Job ID should be returned")
                    
            finally:
                # Restore original request.env
                if original_env:
                    http.request.env = original_env

    def test_hr_create_job_function_calling(self):
        """Test tạo job position thông qua AI function calling"""
        _logger.info("=== Test AI Function Calling tạo job position ===")
        
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        controller = SbotchatController()
        
        # Test function execution
        function_args = {
            'name': 'AI Engineer',
            'department_id': self.department.id,
            'expected_employees': 1
        }
        
        with self.env.registry.cursor() as cr:
            env = self.env(cr=cr, user=self.user_employee.id)
            
            import odoo.http as http
            original_env = getattr(http.request, 'env', None)
            http.request.env = env
            
            try:
                result = controller._execute_hr_function('hr_create_job', function_args)
                
                _logger.info(f"✅ Function calling result: {result}")
                
                # Kiểm tra kết quả
                if result.get('error'):
                    _logger.error(f"❌ Function calling error: {result['error']}")
                    self.fail(f"Function calling trả về lỗi: {result['error']}")
                else:
                    self.assertTrue(result.get('success'), "Success should be True")
                    
            finally:
                if original_env:
                    http.request.env = original_env

    def test_permission_validation(self):
        """Test validation quyền truy cập"""
        _logger.info("=== Test validation quyền truy cập ===")
        
        # Test với user không có quyền (nếu có)
        try:
            # Kiểm tra user thông thường có thể đọc hr.job
            jobs = self.env['hr.job'].with_user(self.user_employee).search([], limit=1)
            _logger.info(f"✅ User thông thường có thể đọc hr.job: {len(jobs)} records")
            
            # Kiểm tra user thông thường có thể tạo hr.job
            job_vals = {
                'name': 'Test Job Permission',
                'no_of_recruitment': 1
            }
            new_job = self.env['hr.job'].with_user(self.user_employee).create(job_vals)
            _logger.info(f"✅ User thông thường có thể tạo hr.job: ID {new_job.id}")
            
        except AccessError as e:
            _logger.error(f"❌ Access error: {str(e)}")
            self.fail(f"User không có quyền cần thiết: {str(e)}")

    def test_hr_api_helper_integration(self):
        """Test integration với hr_api_helper"""
        _logger.info("=== Test hr_api_helper integration ===")
        
        # Test với HR user
        hr_helper = self.env['hr.api.helper'].with_user(self.user_hr)
        
        vals = {
            'name': 'QA Engineer',
            'department_id': self.department.id,
            'no_of_recruitment': 2,
            'description': 'Quality Assurance Engineer position',
            'requirements': 'Experience with testing frameworks'
        }
        
        try:
            result = hr_helper.create_job(vals)
            _logger.info(f"✅ HR Helper result: {result}")
            
            # Kiểm tra extended features
            self.assertEqual(result.get('description'), vals['description'])
            self.assertEqual(result.get('requirements'), vals['requirements'])
            self.assertEqual(result.get('expected_employees'), 2)
            
        except Exception as e:
            _logger.error(f"❌ HR Helper error: {str(e)}")
            self.fail(f"HR Helper failed: {str(e)}")

    def tearDown(self):
        """Clean up test data"""
        # Cleanup sẽ được tự động xử lý bởi TransactionCase
        super(TestHRJobCreationFix, self).tearDown() 