# -*- coding: utf-8 -*-
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class SbotchatHRAIAgent(models.Model):
    _name = 'sbotchat.hr_ai_agent'
    _description = 'HR AI Agent Model'

    @api.model  
    def hr_ai_agent(self, message, conversation_id=None, **kwargs):
        """Main AI Agent method để xử lý yêu cầu HR bằng ngôn ngữ tự nhiên"""
        try:
            # Import controller để sử dụng logic
            from odoo.addons.sbotchat.controllers.hr_ai_agent import HRAIAgentController
            
            # Tạo instance controller và gọi method
            controller = HRAIAgentController()
            result = controller.hr_ai_agent(message, conversation_id, **kwargs)
            
            return result
                
        except Exception as e:
            _logger.error(f"Lỗi trong HR AI Agent Model: {str(e)}")
            return {'success': False, 'error': str(e)} 