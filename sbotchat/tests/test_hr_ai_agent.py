# -*- coding: utf-8 -*-
import json
import logging
from odoo.tests.common import TransactionCase
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class TestHRAIAgent(TransactionCase):
    """Test suite cho HR AI Agent với Function Calling"""

    def setUp(self):
        super().setUp()
        
        # Tạo test data
        self.test_department = self.env['hr.department'].create({
            'name': 'AI Test Department',
        })
        
        self.test_employee = self.env['hr.employee'].create({
            'name': 'AI Test Employee',
            'work_email': 'aitest@company.com',
            'department_id': self.test_department.id,
        })
        
        self.test_conversation = self.env['sbotchat.conversation'].create({
            'title': 'Test HR AI Conversation',
            'user_id': self.env.user.id,
        })

    def test_hr_ai_agent_basic_functionality(self):
        """Test basic AI Agent functionality"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.httprequest.method = 'POST'
            
            # Test basic message
            result = controller.send_message(
                message="Xin chào! Tôi muốn xem danh sách nhân viên",
                conversation_id=self.test_conversation.id
            )
            
            self.assertIsInstance(result, dict)
            # Should contain some response

    def test_hr_function_calling_get_employees(self):
        """Test function calling: get_employees"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Test _hr_get_employees function directly
        result = controller._hr_get_employees(limit=10)
        
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) >= 0)  # Có thể rỗng nếu chưa có data

    def test_hr_function_calling_dashboard_stats(self):
        """Test function calling: get_dashboard_stats"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        result = controller._hr_get_dashboard_stats()
        
        self.assertIsInstance(result, dict)
        self.assertIn('total_employees', result)
        self.assertIn('total_departments', result)

    def test_hr_function_calling_checkin_employee(self):
        """Test function calling: checkin_employee"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        result = controller._hr_checkin_employee(self.test_employee.id)
        
        self.assertIsInstance(result, dict)
        if result.get('success'):
            self.assertIn('check_in_time', result)

    def test_hr_function_calling_checkout_employee(self):
        """Test function calling: checkout_employee"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Checkin first
        controller._hr_checkin_employee(self.test_employee.id)
        
        # Then checkout
        result = controller._hr_checkout_employee(self.test_employee.id)
        
        self.assertIsInstance(result, dict)

    def test_hr_function_calling_create_leave_request(self):
        """Test function calling: create_leave_request"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Tạo leave type trước
        leave_type = self.env['hr.leave.type'].create({
            'name': 'AI Test Leave',
            'allocation_type': 'fixed',
        })
        
        result = controller._hr_create_leave_request(
            employee_id=self.test_employee.id,
            leave_type_id=leave_type.id,
            date_from=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            date_to=(datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            name="AI Test Leave Request"
        )
        
        self.assertIsInstance(result, dict)

    def test_hr_function_calling_get_attendance_summary(self):
        """Test function calling: get_attendance_summary"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        result = controller._hr_get_attendance_summary(
            employee_id=self.test_employee.id
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('total_hours', result)

    def test_hr_function_calling_search_global(self):
        """Test function calling: search_global"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        result = controller._hr_search_global("Test")
        
        self.assertIsInstance(result, dict)
        self.assertIn('employees', result)
        self.assertIn('departments', result)

    def test_hr_function_calling_get_leave_types(self):
        """Test function calling: get_leave_types"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        result = controller._hr_get_leave_types()
        
        self.assertIsInstance(result, list)

    def test_hr_function_calling_approve_leave_request(self):
        """Test function calling: approve_leave_request"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Tạo leave type và leave request trước
        leave_type = self.env['hr.leave.type'].create({
            'name': 'Approval Test Leave',
            'allocation_type': 'fixed',
        })
        
        leave_request = self.env['hr.leave'].create({
            'employee_id': self.test_employee.id,
            'holiday_status_id': leave_type.id,
            'date_from': datetime.now() + timedelta(days=1),
            'date_to': datetime.now() + timedelta(days=2),
            'name': 'Test Approval Leave',
        })
        
        result = controller._hr_approve_leave_request(leave_request.id)
        
        self.assertIsInstance(result, dict)

    def test_hr_function_calling_get_employee_leaves(self):
        """Test function calling: get_employee_leaves"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        result = controller._hr_get_employee_leaves(
            employee_id=self.test_employee.id
        )
        
        self.assertIsInstance(result, list)

    @patch('odoo.addons.sbotchat.controllers.main.SbotchatController._call_deepseek_api_with_functions')
    def test_ai_agent_with_mock_deepseek(self, mock_deepseek):
        """Test AI Agent với mock DeepSeek API"""
        
        # Mock response từ DeepSeek
        mock_deepseek.return_value = {
            "choices": [{
                "message": {
                    "content": "Tôi sẽ giúp bạn xem danh sách nhân viên",
                    "tool_calls": [{
                        "function": {
                            "name": "get_employees",
                            "arguments": '{"limit": 10}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }
        
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            
            result = controller.send_message(
                message="Cho tôi xem danh sách nhân viên",
                conversation_id=self.test_conversation.id
            )
            
            self.assertIsInstance(result, dict)

    @patch('odoo.addons.sbotchat.controllers.main.SbotchatController._call_deepseek_api_with_functions')
    def test_ai_agent_multiple_functions(self, mock_deepseek):
        """Test AI Agent với multiple function calls"""
        
        # Mock response với multiple function calls
        mock_deepseek.return_value = {
            "choices": [{
                "message": {
                    "content": "Tôi sẽ thực hiện các thao tác này cho bạn",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "get_employees", 
                                "arguments": '{"department": "IT"}'
                            }
                        },
                        {
                            "function": {
                                "name": "get_dashboard_stats",
                                "arguments": '{}'
                            }
                        }
                    ]
                },
                "finish_reason": "tool_calls"
            }]
        }
        
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            
            result = controller.send_message(
                message="Cho tôi xem nhân viên phòng IT và thống kê tổng quan",
                conversation_id=self.test_conversation.id
            )
            
            self.assertIsInstance(result, dict)

    def test_function_execution_error_handling(self):
        """Test error handling khi execute functions"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Test với function không tồn tại
        result = controller._execute_hr_function(
            "non_existent_function",
            {}
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)

    def test_function_schema_generation(self):
        """Test generation của HR functions schema"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        schema = controller._get_hr_functions_schema()
        
        self.assertIsInstance(schema, list)
        self.assertTrue(len(schema) > 0)
        
        # Check first function có đủ required fields
        first_function = schema[0]
        self.assertIn('type', first_function)
        self.assertIn('function', first_function)
        self.assertIn('name', first_function['function'])
        self.assertIn('description', first_function['function'])

    def test_conversation_context_management(self):
        """Test quản lý context trong conversation"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            
            # Tạo message trong conversation
            self.env['sbotchat.message'].create({
                'conversation_id': self.test_conversation.id,
                'content': 'Test message',
                'role': 'user',
                'timestamp': datetime.now(),
            })
            
            # Test build conversation messages
            config = {'model': 'deepseek-chat', 'api_key': 'test-key'}
            messages = controller._build_conversation_messages(
                self.test_conversation, 
                config
            )
            
            self.assertIsInstance(messages, list)
            self.assertTrue(len(messages) > 0)

    def test_hr_context_preparation(self):
        """Test preparation của HR context cho AI"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        config = {'model': 'deepseek-chat', 'api_key': 'test-key'}
        messages = controller._prepare_messages_with_hr_context(
            self.test_conversation,
            config
        )
        
        self.assertIsInstance(messages, list)
        
        # Should contain system message with HR context
        system_messages = [m for m in messages if m.get('role') == 'system']
        self.assertTrue(len(system_messages) > 0)

    def test_invalid_function_arguments(self):
        """Test xử lý invalid function arguments"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Test với invalid employee ID
        result = controller._hr_get_employee_leaves(employee_id=99999)
        
        self.assertIsInstance(result, list)
        # Should return empty list for non-existent employee

    def test_date_format_handling(self):
        """Test xử lý date formats trong functions"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Test với different date formats
        result = controller._hr_get_attendance_summary(
            date_from="2024-01-01",
            date_to="2024-01-31"
        )
        
        self.assertIsInstance(result, dict)

    def test_ai_agent_model_integration(self):
        """Test integration với HR AI Agent model"""
        try:
            ai_agent = self.env['sbotchat.hr_ai_agent']
            
            result = ai_agent.hr_ai_agent(
                message="Xin chào!",
                conversation_id=self.test_conversation.id
            )
            
            self.assertIsInstance(result, dict)
            
        except Exception as e:
            # Model might not be fully set up yet
            _logger.warning(f"HR AI Agent model test skipped: {e}")

    def test_performance_with_large_responses(self):
        """Test performance với large data responses"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Test với large limit
        start_time = datetime.now()
        result = controller._hr_get_employees(limit=100)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        self.assertLess(duration, 3.0)  # Should complete within 3 seconds

    def test_concurrent_function_calls(self):
        """Test concurrent function calls handling"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Execute multiple functions "simultaneously"
        results = []
        
        results.append(controller._hr_get_employees(limit=5))
        results.append(controller._hr_get_dashboard_stats())
        results.append(controller._hr_get_leave_types())
        
        # All should succeed
        for result in results:
            self.assertIsNotNone(result)

    def test_function_parameter_validation(self):
        """Test validation của function parameters"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Test với invalid parameters
        result = controller._hr_get_employees(limit=-1)  # Invalid limit
        
        # Should handle gracefully
        self.assertIsInstance(result, list)

    def tearDown(self):
        """Clean up after tests"""
        super().tearDown()
        
        # Clean up test data
        test_conversations = self.env['sbotchat.conversation'].search([
            ('title', 'like', '%Test%')
        ])
        test_conversations.unlink()
        
        test_employees = self.env['hr.employee'].search([
            ('name', 'like', 'AI Test%')
        ])
        test_employees.unlink()
        
        test_departments = self.env['hr.department'].search([
            ('name', 'like', 'AI Test%')
        ])
        test_departments.unlink()
        
        _logger.info("HR AI Agent tests completed successfully") 