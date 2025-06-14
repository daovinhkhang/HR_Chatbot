# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo.addons.sbotchat.controllers.hr_functions_schema import HRFunctionsSchema
from odoo.addons.sbotchat.controllers.main import SbotchatController
from unittest.mock import MagicMock


class TestHRFunctionsSchemaImport(TransactionCase):
    """Test HR Functions Schema Import and Usage"""

    def setUp(self):
        super(TestHRFunctionsSchemaImport, self).setUp()
        self.controller = SbotchatController()
        
        # Create test data
        self.test_department = self.env['hr.department'].create({
            'name': 'Test Department'
        })
        
        self.test_employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
            'department_id': self.test_department.id,
            'work_email': 'test@example.com'
        })

    def test_import_hr_functions_schema(self):
        """Test importing HRFunctionsSchema class"""
        # Test that the class can be imported
        self.assertTrue(HRFunctionsSchema, "HRFunctionsSchema class should be importable")
        
    def test_get_schema_method(self):
        """Test get_schema static method"""
        # Test that get_schema method exists and returns data
        schema = HRFunctionsSchema.get_schema()
        
        self.assertIsInstance(schema, list, "Schema should return a list")
        self.assertGreater(len(schema), 0, "Schema should not be empty")
        
        # Check first function structure
        first_function = schema[0]
        self.assertIn('type', first_function, "Function should have 'type' field")
        self.assertIn('function', first_function, "Function should have 'function' field")
        self.assertEqual(first_function['type'], 'function', "Type should be 'function'")
        
        # Check function details
        function_details = first_function['function']
        self.assertIn('name', function_details, "Function should have 'name'")
        self.assertIn('description', function_details, "Function should have 'description'")
        self.assertIn('parameters', function_details, "Function should have 'parameters'")
        
    def test_schema_structure_integrity(self):
        """Test that schema structure is valid"""
        schema = HRFunctionsSchema.get_schema()
        
        # Test each function in schema
        for i, func in enumerate(schema):
            with self.subTest(function_index=i):
                self.assertIn('type', func)
                self.assertIn('function', func)
                
                function_def = func['function']
                self.assertIn('name', function_def)
                self.assertIn('description', function_def)
                self.assertIn('parameters', function_def)
                
                # Check parameters structure
                params = function_def['parameters']
                self.assertIn('type', params)
                self.assertEqual(params['type'], 'object')
                self.assertIn('properties', params)
                
    def test_main_controller_integration(self):
        """Test that main controller can use HRFunctionsSchema"""
        # This test ensures that the import in main.py works
        schema = HRFunctionsSchema.get_schema()
        self.assertIsInstance(schema, list)
        self.assertGreater(len(schema), 0)
        
    def test_specific_hr_functions_present(self):
        """Test that specific HR functions are present in schema"""
        schema = HRFunctionsSchema.get_schema()
        function_names = [func['function']['name'] for func in schema]
        
        # Test core HR functions are present
        expected_functions = [
            'get_employees',
            'create_employee', 
            'get_departments',
            'get_contracts',
            'get_attendance_records',
            'get_leave_requests',
            'get_payslips'
        ]
        
        for expected_func in expected_functions:
            with self.subTest(function=expected_func):
                self.assertIn(expected_func, function_names, 
                             f"Function '{expected_func}' should be present in schema")

    def test_get_employees_function_with_name_parameter(self):
        """Test get_employees function với parameter name"""
        # Test case 1: get_employees with name parameter
        function_args = {
            'name': 'Test Employee',
            'active': True,
            'limit': 10
        }
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            result = self.controller._execute_hr_function('get_employees', function_args)
        
        self.assertTrue(result.get('success'))
        self.assertIn('data', result)
        self.assertIsInstance(result['data'], list)

    def test_get_employees_function_parameter_filtering(self):
        """Test filtering unexpected parameters in get_employees"""
        # Test case 2: get_employees with unexpected parameter
        function_args = {
            'name': 'Test Employee',
            'department': 'Test Department', 
            'active': True,
            'limit': 10,
            'unexpected_param': 'should_be_filtered'  # This should be filtered out
        }
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            # This should not raise an error anymore
            result = self.controller._execute_hr_function('get_employees', function_args)
        
        self.assertTrue(result.get('success'))
        self.assertIn('data', result)

    def test_hr_get_employees_direct_call(self):
        """Test _hr_get_employees method directly với name parameter"""
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            result = self.controller._hr_get_employees(name='Test Employee')
        
        self.assertTrue(result.get('success'))
        self.assertIn('data', result)

    def test_hr_get_employees_search_functionality(self):
        """Test search functionality với name parameter"""
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            
            # Test search by partial name
            result = self.controller._hr_get_employees(name='Test')
            self.assertTrue(result.get('success'))
            
            # Test search by department
            result = self.controller._hr_get_employees(department='Test Department')
            self.assertTrue(result.get('success'))
            
            # Test combined search
            result = self.controller._hr_get_employees(name='Test', department='Test Department')
            self.assertTrue(result.get('success'))

    def test_get_employees_error_handling(self):
        """Test error handling trong get_employees function"""
        function_args = {
            'name': 'Non-existent Employee',
            'active': True
        }
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            result = self.controller._execute_hr_function('get_employees', function_args)
        
        # Should return success with empty data, not error
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('count'), 0)
        self.assertEqual(len(result.get('data', [])), 0) 