# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
import logging

_logger = logging.getLogger(__name__)

class SbotchatConversation(models.Model):
    _name = 'sbotchat.conversation'
    _description = 'Cuộc trò chuyện SBot Chat'
    _order = 'create_date desc'
    _rec_name = 'title'

    title = fields.Char('Tiêu đề cuộc trò chuyện', required=True, default=lambda self: self._default_title())
    user_id = fields.Many2one('res.users', string='Người dùng', default=lambda self: self.env.user, required=True)
    message_ids = fields.One2many('sbotchat.message', 'conversation_id', string='Tin nhắn')
    message_count = fields.Integer('Số lượng tin nhắn', compute='_compute_message_count', store=True)
    last_message_date = fields.Datetime('Tin nhắn cuối', compute='_compute_last_message_date', store=True)
    is_active = fields.Boolean('Hoạt động', default=True)

    def _default_title(self):
        """Generate default title for conversation"""
        try:
            return f"Chat {fields.Datetime.now().strftime('%Y-%m-%d %H:%M')}"
        except Exception:
            return "Chat mới"

    @api.depends('message_ids')
    def _compute_message_count(self):
        for record in self:
            try:
                record.message_count = len(record.message_ids)
            except Exception as e:
                _logger.error(f"Lỗi khi tính số lượng tin nhắn: {str(e)}")
                record.message_count = 0

    @api.depends('message_ids.create_date')
    def _compute_last_message_date(self):
        for record in self:
            try:
                if record.message_ids:
                    record.last_message_date = max(record.message_ids.mapped('create_date'))
                else:
                    record.last_message_date = record.create_date
            except Exception as e:
                _logger.error(f"Lỗi khi tính ngày tin nhắn cuối: {str(e)}")
                record.last_message_date = record.create_date

    @api.model
    def create_conversation(self, title=None):
        """Create new conversation with proper error handling"""
        try:
            if not title:
                title = f"Chat {fields.Datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Ensure title is not empty
            if not title.strip():
                title = "Chat mới"
            
            conversation = self.create({
                'title': title.strip(),
                'user_id': self.env.user.id,
                'is_active': True,
            })
            
            _logger.info(f"Đã tạo cuộc trò chuyện mới: {conversation.title} cho người dùng {self.env.user.name}")
            return conversation
            
        except Exception as e:
            _logger.error(f"Lỗi khi tạo cuộc trò chuyện: {str(e)}")
            # Try to create with minimal data
            try:
                return self.create({
                    'title': 'Chat khẩn cấp',
                    'user_id': self.env.user.id,
                })
            except Exception as e2:
                _logger.error(f"Không thể tạo cuộc trò chuyện khẩn cấp: {str(e2)}")
                raise e

    def open_chat_interface(self):
        """Open chat interface"""
        try:
            return {
                'type': 'ir.actions.client',
                'tag': 'sbotchat.interface',
                'name': 'Giao diện Chat',
                'target': 'current',
            }
        except Exception as e:
            _logger.error(f"Lỗi khi mở giao diện chat: {str(e)}")
            return {'type': 'ir.actions.act_window_close'}

    def open_configuration(self):
        """Open configuration"""
        try:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Cấu hình',
                'res_model': 'sbotchat.config',
                'view_mode': 'list,form',
                'domain': [('user_id', '=', self.env.user.id)],
                'context': {'default_user_id': self.env.user.id},
                'target': 'current',
            }
        except Exception as e:
            _logger.error(f"Lỗi khi mở cấu hình: {str(e)}")
            return {'type': 'ir.actions.act_window_close'}

    def delete_conversation(self):
        """Delete conversation (soft delete by setting is_active = False)"""
        try:
            if not self.exists():
                _logger.warning("Cố gắng xóa cuộc trò chuyện không tồn tại")
                return False
            
            # Check ownership
            if self.user_id.id != self.env.user.id:
                _logger.warning(f"Người dùng {self.env.user.id} cố gắng xóa cuộc trò chuyện {self.id} của người khác")
                raise ValueError("Bạn không có quyền xóa cuộc trò chuyện này")
            
            # Soft delete by setting is_active = False
            self.write({'is_active': False})
            _logger.info(f"Đã xóa cuộc trò chuyện {self.id}: {self.title}")
            return True
            
        except Exception as e:
            _logger.error(f"Lỗi khi xóa cuộc trò chuyện: {str(e)}")
            raise e

    def permanent_delete_conversation(self):
        """Permanently delete conversation and all messages"""
        try:
            if not self.exists():
                _logger.warning("Cố gắng xóa vĩnh viễn cuộc trò chuyện không tồn tại")
                return False
            
            # Check ownership
            if self.user_id.id != self.env.user.id:
                _logger.warning(f"Người dùng {self.env.user.id} cố gắng xóa vĩnh viễn cuộc trò chuyện {self.id} của người khác")
                raise ValueError("Bạn không có quyền xóa cuộc trò chuyện này")
            
            conversation_title = self.title
            conversation_id = self.id
            message_count = len(self.message_ids)
            
            # Delete all messages first (due to ondelete='cascade', this should happen automatically)
            if self.message_ids:
                self.message_ids.unlink()
            
            # Delete the conversation
            self.unlink()
            
            _logger.info(f"Đã xóa vĩnh viễn cuộc trò chuyện {conversation_id}: {conversation_title} (với {message_count} tin nhắn)")
            return True
            
        except Exception as e:
            _logger.error(f"Lỗi khi xóa vĩnh viễn cuộc trò chuyện: {str(e)}")
            raise e

    def restore_conversation(self):
        """Restore soft-deleted conversation"""
        try:
            if not self.exists():
                _logger.warning("Cố gắng khôi phục cuộc trò chuyện không tồn tại")
                return False
            
            # Check ownership
            if self.user_id.id != self.env.user.id:
                _logger.warning(f"Người dùng {self.env.user.id} cố gắng khôi phục cuộc trò chuyện {self.id} của người khác")
                raise ValueError("Bạn không có quyền khôi phục cuộc trò chuyện này")
            
            # Restore by setting is_active = True
            self.write({'is_active': True})
            _logger.info(f"Đã khôi phục cuộc trò chuyện {self.id}: {self.title}")
            return True
            
        except Exception as e:
            _logger.error(f"Lỗi khi khôi phục cuộc trò chuyện: {str(e)}")
            raise e

    def update_title(self, new_title):
        """Update conversation title"""
        try:
            if not self.exists():
                _logger.warning("Cố gắng cập nhật tiêu đề cuộc trò chuyện không tồn tại")
                return False
            
            # Check ownership
            if self.user_id.id != self.env.user.id:
                _logger.warning(f"Người dùng {self.env.user.id} cố gắng cập nhật cuộc trò chuyện {self.id} của người khác")
                raise ValueError("Bạn không có quyền cập nhật cuộc trò chuyện này")
            
            if not new_title or not new_title.strip():
                raise ValueError("Tiêu đề cuộc trò chuyện không được để trống")
            
            old_title = self.title
            self.write({'title': new_title.strip()})
            _logger.info(f"Đã cập nhật tiêu đề cuộc trò chuyện {self.id} từ '{old_title}' thành '{new_title.strip()}'")
            return True
            
        except Exception as e:
            _logger.error(f"Lỗi khi cập nhật tiêu đề cuộc trò chuyện: {str(e)}")
            raise e

    @api.model
    def get_user_conversations(self, include_inactive=False, limit=50):
        """Get user's conversations with optional inactive ones"""
        try:
            domain = [('user_id', '=', self.env.user.id)]
            if not include_inactive:
                domain.append(('is_active', '=', True))
            
            conversations = self.search(domain, order='last_message_date desc, create_date desc', limit=limit)
            
            result = []
            for conv in conversations:
                try:
                    result.append({
                        'id': conv.id,
                        'title': conv.title or 'Chat không có tiêu đề',
                        'message_count': conv.message_count,
                        'last_message_date': conv.last_message_date.isoformat() if conv.last_message_date else None,
                        'is_active': conv.is_active,
                        'create_date': conv.create_date.isoformat() if conv.create_date else None,
                    })
                except Exception as e:
                    _logger.error(f"Lỗi khi xử lý cuộc trò chuyện {conv.id}: {str(e)}")
                    continue
            
            return result
            
        except Exception as e:
            _logger.error(f"Lỗi khi lấy cuộc trò chuyện: {str(e)}")
            return []

class SbotchatMessage(models.Model):
    _name = 'sbotchat.message'
    _description = 'Tin nhắn SBot Chat'
    _order = 'create_date asc'

    conversation_id = fields.Many2one('sbotchat.conversation', string='Cuộc trò chuyện', required=True, ondelete='cascade')
    role = fields.Selection([
        ('user', 'Người dùng'),
        ('assistant', 'Trợ lý'),
        ('system', 'Hệ thống')
    ], string='Vai trò', required=True)
    content = fields.Text('Nội dung', required=True)
    model_used = fields.Char('Mô hình sử dụng')
    tokens_used = fields.Integer('Token đã sử dụng', default=0)
    response_time = fields.Float('Thời gian phản hồi (giây)', default=0.0)
    
    # For DeepSeek reasoner thinking process
    thinking_content = fields.Text('Quá trình suy nghĩ')
    
    @api.model
    def add_message(self, conversation_id, role, content, **kwargs):
        """Add message to conversation with error handling"""
        try:
            # Validate inputs
            if not conversation_id:
                raise ValueError("conversation_id là bắt buộc")
            if not role:
                raise ValueError("role là bắt buộc")
            if not content:
                content = "[Tin nhắn trống]"
            
            message = self.create({
                'conversation_id': conversation_id,
                'role': role,
                'content': content,
                'model_used': kwargs.get('model_used', ''),
                'tokens_used': kwargs.get('tokens_used', 0),
                'response_time': kwargs.get('response_time', 0.0),
                'thinking_content': kwargs.get('thinking_content', ''),
            })
            
            _logger.info(f"Đã thêm tin nhắn {role} vào cuộc trò chuyện {conversation_id}")
            return message
            
        except Exception as e:
            _logger.error(f"Lỗi khi thêm tin nhắn: {str(e)}")
            raise e 