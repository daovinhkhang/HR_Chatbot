# -*- coding: utf-8 -*-

import json
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError
from odoo import fields


class TestDashboardFrontend(TransactionCase):

    def setUp(self):
        super(TestDashboardFrontend, self).setUp()
        
        # Create test data
        self.company = self.env['res.company'].create({
            'name': 'Test Company Dashboard',
        })
        
        # Create test user with HR permissions
        self.hr_user = self.env['res.users'].create({
            'name': 'HR Dashboard User',
            'login': 'hr_dashboard_user',
            'email': 'hr_dashboard@test.com',
            'company_id': self.company.id,
            'company_ids': [(6, 0, [self.company.id])],
            'groups_id': [(6, 0, [
                self.env.ref('hr.group_hr_user').id,
                self.env.ref('base.group_user').id,
            ])]
        })
        
        # Create test employees
        self.employee1 = self.env['hr.employee'].create({
            'name': 'Test Employee 1',
            'company_id': self.company.id,
            'user_id': self.hr_user.id,
        })
        
        self.employee2 = self.env['hr.employee'].create({
            'name': 'Test Employee 2', 
            'company_id': self.company.id,
        })
        
        # Create test attendance records
        today = fields.Date.today()
        self.attendance1 = self.env['hr.attendance'].create({
            'employee_id': self.employee1.id,
            'check_in': f'{today} 08:00:00',
        })
        
        # Create test leave type
        self.leave_type = self.env['hr.leave.type'].create({
            'name': 'Test Leave Type',
            'allocation_type': 'no',
            'company_id': self.company.id,
        })
        
        # Create test leave request
        self.leave_request = self.env['hr.leave'].create({
            'name': 'Test Leave Request',
            'employee_id': self.employee1.id,
            'holiday_status_id': self.leave_type.id,
            'date_from': today,
            'date_to': today,
            'number_of_days': 1,
            'state': 'confirm',
        })

    def test_dashboard_data_structure(self):
        """Test dashboard data structure is correct"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Mock request context
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.user = self.hr_user
            mock_request.env.company = self.company
            
            # Test dashboard data loading
            response = controller.dashboard_realtime_stats()
            
            # Verify response structure
            self.assertTrue(response.get('success'))
            self.assertIn('data', response)
            
            data = response['data']
            
            # Check all required sections exist
            required_sections = [
                'employee_overview',
                'realtime_attendance', 
                'leave_management',
                'recruitment',
                'payroll',
                'quick_actions',
                'notifications',
                'last_updated'
            ]
            
            for section in required_sections:
                self.assertIn(section, data, f"Missing section: {section}")

    def test_dashboard_employee_overview(self):
        """Test employee overview widget data"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.user = self.hr_user
            mock_request.env.company = self.company
            
            today = fields.Date.today()
            overview = controller._get_employee_overview_stats(self.company.id, today)
            
            # Verify overview data structure
            required_fields = [
                'total_employees',
                'active_employees', 
                'attendance_rate',
                'late_arrivals',
                'overtime_workers'
            ]
            
            for field in required_fields:
                self.assertIn(field, overview, f"Missing field: {field}")
            
            # Verify data types
            self.assertIsInstance(overview['total_employees'], int)
            self.assertIsInstance(overview['active_employees'], int)
            self.assertIsInstance(overview['late_arrivals'], int)
            self.assertIsInstance(overview['overtime_workers'], int)
            self.assertTrue(overview['attendance_rate'].endswith('%'))

    def test_dashboard_realtime_attendance(self):
        """Test realtime attendance widget data"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.user = self.hr_user
            mock_request.env.company = self.company
            
            today = fields.Date.today()
            attendance_data = controller._get_realtime_attendance_stats(self.company.id, today)
            
            # Verify attendance data structure
            self.assertIn('recent_checkins', attendance_data)
            self.assertIsInstance(attendance_data['recent_checkins'], list)
            
            # If there are checkins, verify structure
            if attendance_data['recent_checkins']:
                checkin = attendance_data['recent_checkins'][0]
                required_fields = ['id', 'employee_name', 'check_in_time', 'status']
                
                for field in required_fields:
                    self.assertIn(field, checkin, f"Missing field in checkin: {field}")

    def test_dashboard_leave_management(self):
        """Test leave management widget data"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.user = self.hr_user
            mock_request.env.company = self.company
            
            today = fields.Date.today()
            leave_data = controller._get_leave_management_stats(self.company.id, today)
            
            # Verify leave data structure
            required_fields = [
                'pending_approvals',
                'approved_today',
                'on_leave_today',
                'pending_requests'
            ]
            
            for field in required_fields:
                self.assertIn(field, leave_data, f"Missing field: {field}")
            
            # Verify data types
            self.assertIsInstance(leave_data['pending_approvals'], int)
            self.assertIsInstance(leave_data['approved_today'], int)
            self.assertIsInstance(leave_data['on_leave_today'], int)
            self.assertIsInstance(leave_data['pending_requests'], list)
            
            # Should have at least one pending request from setUp
            self.assertGreaterEqual(leave_data['pending_approvals'], 1)

    def test_dashboard_quick_actions(self):
        """Test quick actions configuration"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.user = self.hr_user
            mock_request.env.company = self.company
            
            quick_actions = controller._get_quick_actions_config(self.hr_user)
            
            # Verify quick actions structure
            self.assertIsInstance(quick_actions, list)
            
            if quick_actions:
                action = quick_actions[0]
                required_fields = ['id', 'label', 'icon', 'type', 'description']
                
                for field in required_fields:
                    self.assertIn(field, action, f"Missing field in quick action: {field}")

    def test_dashboard_fallback_data(self):
        """Test fallback data methods"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Test all fallback methods
        fallback_methods = [
            '_get_fallback_dashboard_data',
            '_get_fallback_employee_stats',
            '_get_fallback_attendance_stats',
            '_get_fallback_leave_stats',
            '_get_fallback_recruitment_stats',
            '_get_fallback_payroll_stats'
        ]
        
        for method_name in fallback_methods:
            method = getattr(controller, method_name)
            result = method()
            
            # Verify fallback data is not None and has expected structure
            self.assertIsNotNone(result, f"Fallback method {method_name} returned None")
            self.assertIsInstance(result, dict, f"Fallback method {method_name} should return dict")

    def test_dashboard_error_handling(self):
        """Test dashboard error handling"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Test with invalid company
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.user = self.hr_user
            mock_request.env.company = self.company
            
            # Mock database error
            with patch.object(self.env['hr.employee'], 'search_count', side_effect=Exception("Database error")):
                today = fields.Date.today()
                result = controller._get_employee_overview_stats(self.company.id, today)
                
                # Should return fallback data on error
                self.assertIsInstance(result, dict)
                self.assertIn('total_employees', result)

    def test_dashboard_permissions(self):
        """Test dashboard access permissions"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        # Create user without HR permissions
        basic_user = self.env['res.users'].create({
            'name': 'Basic User',
            'login': 'basic_user',
            'email': 'basic@test.com',
            'company_id': self.company.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.user = basic_user
            mock_request.env.company = self.company
            
            # Should still work but with limited data
            response = controller.dashboard_realtime_stats()
            
            # Should return success with fallback data
            self.assertTrue(response.get('success'))
            self.assertIn('data', response)

    def test_dashboard_real_time_updates(self):
        """Test dashboard real-time update capability"""
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.user = self.hr_user
            mock_request.env.company = self.company
            
            # Get initial data
            response1 = controller.dashboard_realtime_stats()
            initial_data = response1['data']
            
            # Create new attendance record
            today = fields.Date.today()
            new_attendance = self.env['hr.attendance'].create({
                'employee_id': self.employee2.id,
                'check_in': f'{today} 09:00:00',
            })
            
            # Get updated data
            response2 = controller.dashboard_realtime_stats()
            updated_data = response2['data']
            
            # Verify data has been updated
            self.assertNotEqual(
                initial_data['realtime_attendance'],
                updated_data['realtime_attendance']
            )

    def test_dashboard_responsive_behavior(self):
        """Test dashboard responsive behavior"""
        # This would typically be tested with frontend testing tools
        # For now, we verify the data structure supports responsive design
        
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        
        controller = SbotchatController()
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.user = self.hr_user
            mock_request.env.company = self.company
            
            response = controller.dashboard_realtime_stats()
            data = response['data']
            
            # Verify data structure supports different screen sizes
            # All widgets should have compact data representation
            
            # Employee overview should have limited metrics
            overview = data['employee_overview']
            self.assertLessEqual(len(overview), 10, "Too many metrics for mobile view")
            
            # Attendance should limit recent checkins
            attendance = data['realtime_attendance']
            if 'recent_checkins' in attendance:
                self.assertLessEqual(len(attendance['recent_checkins']), 10, "Too many checkins for mobile view")

    def tearDown(self):
        """Clean up test data"""
        # Clean up is handled automatically by TransactionCase
        super(TestDashboardFrontend, self).tearDown() 