# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class SbotchatConfig(models.Model):
    _name = 'sbotchat.config'
    _description = 'Cấu hình SBot Chat'
    _rec_name = 'name'

    name = fields.Char('Tên cấu hình', required=True, default='Cấu hình mặc định')
    api_key = fields.Char('Khóa API DeepSeek', help='Khóa API DeepSeek của bạn từ platform.deepseek.com')
    model_type = fields.Selection([
        ('deepseek-chat', 'DeepSeek Chat'),
        ('deepseek-reasoner', 'DeepSeek Reasoner')
    ], string='Loại mô hình', default='deepseek-chat', required=True, 
       help='Chọn giữa DeepSeek Chat (nhanh) hoặc DeepSeek Reasoner (với quá trình suy nghĩ)')
    
    # Model parameters with proper ranges
    temperature = fields.Float('Nhiệt độ', default=1.0, help='Kiểm soát tính ngẫu nhiên (0.0-2.0)')
    max_tokens = fields.Integer('Số token tối đa', default=4000, help='Số token tối đa trong phản hồi (1-8000)')
    top_p = fields.Float('Top P', default=1.0, help='Tham số nucleus sampling (0.0-1.0)')
    frequency_penalty = fields.Float('Phạt tần suất', default=0.0, help='Phạt các token thường xuyên (-2.0 đến 2.0)')
    presence_penalty = fields.Float('Phạt hiện diện', default=0.0, help='Phạt các token hiện tại (-2.0 đến 2.0)')
    
    # System settings
    system_prompt = fields.Text('Lời nhắc hệ thống', default='Bạn là một trợ lý AI hữu ích.',
                               help='Hướng dẫn cho hành vi của trợ lý AI')
    is_active = fields.Boolean('Hoạt động', default=True)
    user_id = fields.Many2one('res.users', string='Người dùng', default=lambda self: self.env.user, required=True)
    
    @api.model
    def get_active_config(self):
        """Get active configuration for current user"""
        try:
            config = self.search([
                ('user_id', '=', self.env.user.id),
                ('is_active', '=', True)
            ], limit=1)
            
            if not config:
                # Create default config if none exists
                _logger.info(f"Tạo cấu hình mặc định cho người dùng {self.env.user.login} (ID: {self.env.user.id})")
                config = self.create({
                    'name': f'Cấu hình mặc định - {self.env.user.login}',
                    'api_key': '',
                    'model_type': 'deepseek-chat',
                    'temperature': 1.0,
                    'max_tokens': 4000,
                    'top_p': 1.0,
                    'frequency_penalty': 0.0,
                    'presence_penalty': 0.0,
                    'system_prompt': 'Bạn là một trợ lý AI hữu ích.',
                    'user_id': self.env.user.id,
                    'is_active': True,
                })
                _logger.info(f"Đã tạo cấu hình mặc định với ID {config.id} cho người dùng {self.env.user.login}")
            else:
                _logger.info(f"Tìm thấy cấu hình hiện có ID {config.id} cho người dùng {self.env.user.login}")
            
            return config
        except Exception as e:
            _logger.error(f"Lỗi khi lấy cấu hình hoạt động cho người dùng {self.env.user.login}: {str(e)}")
            # Return empty recordset instead of None to prevent crashes
            return self.browse()
    
    @api.constrains('api_key')
    def _check_api_key(self):
        """Validate API key format"""
        for record in self:
            if record.api_key:
                api_key = record.api_key.strip()
                if api_key and not api_key.startswith('sk-'):
                    raise ValidationError("Khóa API DeepSeek phải bắt đầu bằng 'sk-'. Lấy khóa của bạn từ platform.deepseek.com")
    
    @api.constrains('temperature')
    def _check_temperature(self):
        """Validate temperature range"""
        for record in self:
            if record.temperature is not None and (record.temperature < 0.0 or record.temperature > 2.0):
                raise ValidationError("Nhiệt độ phải nằm trong khoảng từ 0.0 đến 2.0")
    
    @api.constrains('max_tokens')
    def _check_max_tokens(self):
        """Validate max tokens range"""
        for record in self:
            if record.max_tokens is not None and (record.max_tokens < 1 or record.max_tokens > 8000):
                raise ValidationError("Số token tối đa phải nằm trong khoảng từ 1 đến 8000")
    
    @api.constrains('top_p')
    def _check_top_p(self):
        """Validate top_p range"""
        for record in self:
            if record.top_p is not None and (record.top_p < 0.0 or record.top_p > 1.0):
                raise ValidationError("Top P phải nằm trong khoảng từ 0.0 đến 1.0")
    
    @api.constrains('frequency_penalty', 'presence_penalty')
    def _check_penalties(self):
        """Validate penalty ranges"""
        for record in self:
            if record.frequency_penalty is not None and (record.frequency_penalty < -2.0 or record.frequency_penalty > 2.0):
                raise ValidationError("Phạt tần suất phải nằm trong khoảng từ -2.0 đến 2.0")
            if record.presence_penalty is not None and (record.presence_penalty < -2.0 or record.presence_penalty > 2.0):
                raise ValidationError("Phạt hiện diện phải nằm trong khoảng từ -2.0 đến 2.0") 