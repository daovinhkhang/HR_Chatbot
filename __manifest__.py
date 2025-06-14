# -*- coding: utf-8 -*-
{
    'name': 'SBot Chat - Chatbot AI DeepSeek với HR Assistant',
    'version': '1.0.0',
    'category': 'Công cụ',
    'summary': 'Chatbot AI được hỗ trợ bởi DeepSeek API với lịch sử cuộc trò chuyện và HR Assistant thông minh',
    'description': """
SBot Chat - Chatbot AI DeepSeek với HR Assistant
===============================================

Một module chatbot AI toàn diện được hỗ trợ bởi DeepSeek API với các tính năng:
* Hỗ trợ các mô hình deepseek-chat và deepseek-reasoner
* Cài đặt API có thể tùy chỉnh
* Lịch sử cuộc trò chuyện với thanh bên
* Truy cập nút nổi toàn cục
* Giao diện chat thời gian thực

**HR Assistant Integration** 🤖:
* Xử lý yêu cầu HR bằng ngôn ngữ tự nhiên (Tiếng Việt/English)
* 116+ API endpoints cho toàn bộ hệ thống HR
* Quản lý nhân viên, chấm công, nghỉ phép, lương bổng
* Tuyển dụng, kỹ năng, dự án, bảo hiểm BHXH/BHYT/BHTN
* Báo cáo analytics và dashboard thống kê
* Smart intent recognition và auto parameter extraction

Tương thích với Odoo 18.0
    """,
    'author': 'Công ty của bạn',
    'website': 'https://www.congtyban.com',
    'depends': [
        'base', 
        'web', 
        'mail',
        # HR Core Dependencies
        'hr',
        'hr_contract',
        'hr_attendance', 
        'hr_holidays',
        'hr_payroll_community',
        'hr_recruitment',
        'hr_skills',
        'hr_timesheet',
        # HR Extended Dependencies (optional but recommended)
        'hr_expense',
        'hr_homeworking',
        'project',
        'calendar',
        'fleet',
        # Analytics
        'analytic',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sbotchat_views.xml',
        'views/sbotchat_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sbotchat/static/src/xml/sbotchat_templates.xml',
            'sbotchat/static/src/css/sbotchat.css',
            'sbotchat/static/src/css/ai_response_formatter.css',
            'sbotchat/static/src/js/ai_response_formatter.js',
            'sbotchat/static/src/js/sbotchat_widget.js',
            'sbotchat/static/src/js/sbotchat_floating.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
} 