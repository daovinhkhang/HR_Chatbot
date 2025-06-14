# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import json
from unittest.mock import patch

from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError, ValidationError
from odoo.http import request
from odoo import fields


class TestDashboardAPI(TransactionCase):

    def setUp(self):
        super(TestDashboardAPI, self).setUp()
        
        # Create test data
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
        })
        
        # Create test users with different permissions
        self.hr_manager = self.env['res.users'].create({
            'name': 'HR Manager',
            'login': 'hr_manager@test.com',
            'email': 'hr_manager@test.com',
            'company_id': self.company.id,
            'groups_id': [(6, 0, [
                self.env.ref('hr.group_hr_manager').id,
                self.env.ref('hr_holidays.group_hr_holidays_manager').id
            ])]
        })
        
        self.hr_user = self.env['res.users'].create({
            'name': 'HR User',
            'login': 'hr_user@test.com',
            'email': 'hr_user@test.com',
            'company_id': self.company.id,
            'groups_id': [(6, 0, [self.env.ref('hr.group_hr_user').id])]
        })
        
        self.basic_user = self.env['res.users'].create({
            'name': 'Basic User',
            'login': 'basic@test.com',
            'email': 'basic@test.com',
            'company_id': self.company.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        
        # Create test department
        self.department = self.env['hr.department'].create({
            'name': 'Test Department',
            'company_id': self.company.id,
        })
        
        # Create test job
        self.job = self.env['hr.job'].create({
            'name': 'Test Job',
            'department_id': self.department.id,
            'company_id': self.company.id,
        })
        
        # Create test employees
        self.employee1 = self.env['hr.employee'].create({
            'name': 'Employee 1',
            'department_id': self.department.id,
            'job_id': self.job.id,
            'company_id': self.company.id,
        })
        
        self.employee2 = self.env['hr.employee'].create({
            'name': 'Employee 2',
            'department_id': self.department.id,
            'job_id': self.job.id,
            'company_id': self.company.id,
        })
        
        # Create test leave type
        self.leave_type = self.env['hr.leave.type'].create({
            'name': 'Test Annual Leave',
            'company_id': self.company.id,
            'allocation_type': 'fixed_allocation',
        })
        
        # Import controller
        from odoo.addons.sbotchat.controllers.main import SbotchatController
        self.controller = SbotchatController()

    def test_dashboard_realtime_stats_access_control(self):
        """Test access control for dashboard API"""
        # Test with basic user (should fail)
        with self.assertRaises(AccessError):
            self.controller.dashboard_realtime_stats()
        
        # Test with HR user (should succeed)
        self.controller = self.controller.with_user(self.hr_user)
        response = self.controller.dashboard_realtime_stats()
        self.assertTrue(response.get('success', False))

    def test_employee_overview_stats(self):
        """Test employee overview statistics"""
        self.controller = self.controller.with_user(self.hr_manager)
        
        stats = self.controller._get_employee_overview_stats(
            self.company.id, 
            fields.Date.today()
        )
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_employees', stats)
        self.assertIn('active_employees', stats)
        self.assertIn('departments_count', stats)
        self.assertEqual(stats['total_employees'], 2)  # 2 test employees
        self.assertEqual(stats['departments_count'], 1)  # 1 test department

    def test_leave_management_stats(self):
        """Test leave management statistics"""
        self.controller = self.controller.with_user(self.hr_manager)
        
        # Create test leave request
        leave = self.env['hr.leave'].create({
            'employee_id': self.employee1.id,
            'holiday_status_id': self.leave_type.id,
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today() + timedelta(days=2),
            'name': 'Test leave',
            'state': 'confirm'
        })
        
        stats = self.controller._get_leave_management_stats(
            self.company.id,
            fields.Date.today()
        )
        
        self.assertIsInstance(stats, dict)
        self.assertIn('pending_approvals', stats)
        self.assertEqual(stats['pending_approvals']['count'], 1)

    def test_attendance_stats(self):
        """Test attendance statistics"""
        self.controller = self.controller.with_user(self.hr_manager)
        
        # Create test attendance
        attendance = self.env['hr.attendance'].create({
            'employee_id': self.employee1.id,
            'check_in': datetime.now(),
        })
        
        stats = self.controller._get_realtime_attendance_stats(
            self.company.id,
            fields.Date.today()
        )
        
        self.assertIsInstance(stats, dict)
        self.assertIn('recent_checkins', stats)
        self.assertIn('summary', stats)

    def test_quick_action_approve_leaves(self):
        """Test quick action for approving leaves"""
        self.controller = self.controller.with_user(self.hr_manager)
        
        # Create pending leave
        leave = self.env['hr.leave'].create({
            'employee_id': self.employee1.id,
            'holiday_status_id': self.leave_type.id,
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today() + timedelta(days=1),
            'name': 'Test leave',
            'state': 'confirm'
        })
        
        response = self.controller.quick_action_approve_leaves()
        
        self.assertTrue(response.get('success', False))
        self.assertIn('approved_count', response)

    def test_quick_action_add_employee(self):
        """Test quick action for adding employee"""
        self.controller = self.controller.with_user(self.hr_user)
        
        response = self.controller.quick_action_add_employee()
        
        self.assertTrue(response.get('success', False))
        self.assertIn('action', response)
        self.assertEqual(response['action']['res_model'], 'hr.employee')

    def test_fallback_data_methods(self):
        """Test fallback data methods"""
        self.controller = self.controller.with_user(self.hr_user)
        
        # Test all fallback methods
        fallback_data = self.controller._get_fallback_dashboard_data()
        self.assertIsInstance(fallback_data, dict)
        
        employee_stats = self.controller._get_fallback_employee_stats()
        self.assertIsInstance(employee_stats, dict)
        self.assertEqual(employee_stats['total_employees'], 0)
        
        attendance_stats = self.controller._get_fallback_attendance_stats()
        self.assertIsInstance(attendance_stats, dict)
        
        leave_stats = self.controller._get_fallback_leave_stats()
        self.assertIsInstance(leave_stats, dict)

    def test_dashboard_notifications(self):
        """Test dashboard notifications"""
        self.controller = self.controller.with_user(self.hr_manager)
        
        # Create pending leave for notification
        leave = self.env['hr.leave'].create({
            'employee_id': self.employee1.id,
            'holiday_status_id': self.leave_type.id,
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today() + timedelta(days=1),
            'name': 'Test leave',
            'state': 'confirm'
        })
        
        notifications = self.controller._get_dashboard_notifications(
            self.company.id,
            self.hr_manager
        )
        
        self.assertIsInstance(notifications, dict)
        self.assertIn('high_priority', notifications)
        self.assertIn('total_unread', notifications)
        self.assertGreater(notifications['total_unread'], 0)

    def test_quick_actions_config(self):
        """Test quick actions configuration based on user permissions"""
        # Test with HR Manager
        self.controller = self.controller.with_user(self.hr_manager)
        actions = self.controller._get_quick_actions_config(self.hr_manager)
        
        self.assertIsInstance(actions, list)
        action_ids = [action['id'] for action in actions]
        self.assertIn('approve_leaves', action_ids)
        self.assertIn('add_employee', action_ids)
        
        # Test with basic HR user
        self.controller = self.controller.with_user(self.hr_user)
        actions = self.controller._get_quick_actions_config(self.hr_user)
        
        action_ids = [action['id'] for action in actions]
        self.assertIn('add_employee', action_ids)
        self.assertNotIn('approve_leaves', action_ids)  # No permission

    def test_error_handling(self):
        """Test error handling in dashboard API"""
        self.controller = self.controller.with_user(self.hr_user)
        
        # Test with invalid company_id
        with patch.object(self.controller.env.user, 'company_id') as mock_company:
            mock_company.id = 99999  # Non-existent company
            
            stats = self.controller._get_employee_overview_stats(99999, fields.Date.today())
            # Should return fallback data or handle gracefully
            self.assertIsInstance(stats, dict)

    def test_recruitment_stats(self):
        """Test recruitment statistics"""
        self.controller = self.controller.with_user(self.hr_manager)
        
        # Create recruitment job
        job = self.env['hr.job'].create({
            'name': 'Recruitment Job',
            'department_id': self.department.id,
            'company_id': self.company.id,
            'state': 'recruit',
            'no_of_recruitment': 2,
        })
        
        stats = self.controller._get_recruitment_stats(self.company.id)
        
        self.assertIsInstance(stats, dict)
        self.assertIn('open_positions', stats)
        self.assertIn('applicants', stats)

    def test_data_integrity(self):
        """Test data integrity in dashboard responses"""
        self.controller = self.controller.with_user(self.hr_manager)
        
        response = self.controller.dashboard_realtime_stats()
        
        # Verify response structure
        self.assertIn('success', response)
        self.assertIn('data', response)
        
        data = response['data']
        required_sections = [
            'employee_overview',
            'realtime_attendance', 
            'leave_management',
            'recruitment',
            'payroll',
            'notifications',
            'quick_actions',
            'permissions'
        ]
        
        for section in required_sections:
            self.assertIn(section, data)

    def tearDown(self):
        super(TestDashboardAPI, self).tearDown() 