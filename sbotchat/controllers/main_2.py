# -*- coding: utf-8 -*-

from odoo import http, fields
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class SbotchatControllerExtended(http.Controller):
    """
    Extended Controller cho SBot Chat - Quản lý cuộc trò chuyện
    Bổ sung cho main.py để tránh file quá dài
    """

    @http.route('/sbotchat/conversation/<int:conversation_id>/delete', type='json', auth='user', methods=['POST'])
    def delete_conversation(self, conversation_id):
        """Delete conversation (soft delete)"""
        try:
            conversation = request.env['sbotchat.conversation'].browse(conversation_id)
            if not conversation.exists():
                return {'success': False, 'error': 'Không tìm thấy cuộc trò chuyện'}
            
            # Delete the conversation (this will check ownership inside the method)
            result = conversation.delete_conversation()
            
            if result:
                return {'success': True, 'message': f'Đã xóa cuộc trò chuyện "{conversation.title}"'}
            else:
                return {'success': False, 'error': 'Không thể xóa cuộc trò chuyện'}
                
        except ValueError as e:
            _logger.warning(f"Permission denied in delete_conversation: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Lỗi khi xóa cuộc trò chuyện: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'}

    @http.route('/sbotchat/conversation/<int:conversation_id>/permanent_delete', type='json', auth='user', methods=['POST'])
    def permanent_delete_conversation(self, conversation_id):
        """Permanently delete conversation and all messages"""
        try:
            conversation = request.env['sbotchat.conversation'].browse(conversation_id)
            if not conversation.exists():
                return {'success': False, 'error': 'Không tìm thấy cuộc trò chuyện'}
            
            conversation_title = conversation.title
            
            # Permanently delete the conversation (this will check ownership inside the method)
            result = conversation.permanent_delete_conversation()
            
            if result:
                return {'success': True, 'message': f'Đã xóa vĩnh viễn cuộc trò chuyện "{conversation_title}"'}
            else:
                return {'success': False, 'error': 'Không thể xóa vĩnh viễn cuộc trò chuyện'}
                
        except ValueError as e:
            _logger.warning(f"Permission denied in permanent_delete_conversation: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Lỗi khi xóa vĩnh viễn cuộc trò chuyện: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'}

    @http.route('/sbotchat/conversation/<int:conversation_id>/restore', type='json', auth='user', methods=['POST'])
    def restore_conversation(self, conversation_id):
        """Restore soft-deleted conversation"""
        try:
            conversation = request.env['sbotchat.conversation'].browse(conversation_id)
            if not conversation.exists():
                return {'success': False, 'error': 'Không tìm thấy cuộc trò chuyện'}
            
            # Restore the conversation (this will check ownership inside the method)
            result = conversation.restore_conversation()
            
            if result:
                return {'success': True, 'message': f'Đã khôi phục cuộc trò chuyện "{conversation.title}"'}
            else:
                return {'success': False, 'error': 'Không thể khôi phục cuộc trò chuyện'}
                
        except ValueError as e:
            _logger.warning(f"Permission denied in restore_conversation: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Lỗi khi khôi phục cuộc trò chuyện: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'}

    @http.route('/sbotchat/conversation/<int:conversation_id>/update_title', type='json', auth='user', methods=['POST'])
    def update_conversation_title(self, conversation_id, title):
        """Update conversation title"""
        try:
            conversation = request.env['sbotchat.conversation'].browse(conversation_id)
            if not conversation.exists():
                return {'success': False, 'error': 'Không tìm thấy cuộc trò chuyện'}
            
            # Update the title (this will check ownership inside the method)
            result = conversation.update_title(title)
            
            if result:
                return {'success': True, 'message': f'Đã cập nhật tiêu đề thành "{title}"', 'new_title': title}
            else:
                return {'success': False, 'error': 'Không thể cập nhật tiêu đề cuộc trò chuyện'}
                
        except ValueError as e:
            _logger.warning(f"Permission denied or validation error in update_conversation_title: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Lỗi khi cập nhật tiêu đề cuộc trò chuyện: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'}

    @http.route('/sbotchat/conversations/deleted', type='json', auth='user')
    def get_deleted_conversations(self):
        """Get user's deleted (inactive) conversations"""
        try:
            conversations = request.env['sbotchat.conversation'].search([
                ('user_id', '=', request.env.user.id),
                ('is_active', '=', False)
            ], order='create_date desc')
            
            result = []
            for conv in conversations:
                try:
                    result.append({
                        'id': conv.id,
                        'title': conv.title or 'Chat không có tiêu đề',
                        'message_count': conv.message_count,
                        'last_message_date': conv.last_message_date.isoformat() if conv.last_message_date else None,
                        'deleted_date': conv.write_date.isoformat() if conv.write_date else None,
                    })
                except Exception as e:
                    _logger.error(f"Lỗi khi xử lý cuộc trò chuyện đã xóa {conv.id}: {str(e)}")
                    continue
            
            return {'success': True, 'data': result}
        except Exception as e:
            _logger.error(f"Lỗi khi lấy cuộc trò chuyện đã xóa: {str(e)}")
            return {'success': False, 'error': str(e), 'data': []}

    @http.route('/sbotchat/conversations/all', type='json', auth='user')
    def get_all_conversations(self, include_inactive=False, limit=50):
        """Get all user's conversations with optional inactive ones"""
        try:
            include_inactive = bool(include_inactive)
            limit = int(limit) if limit else 50
            
            domain = [('user_id', '=', request.env.user.id)]
            if not include_inactive:
                domain.append(('is_active', '=', True))
            
            conversations = request.env['sbotchat.conversation'].search(
                domain, 
                order='last_message_date desc, create_date desc', 
                limit=limit
            )
            
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
            
            return {
                'success': True, 
                'data': result,
                'total': len(result),
                'include_inactive': include_inactive,
                'limit': limit
            }
        except Exception as e:
            _logger.error(f"Lỗi khi lấy tất cả cuộc trò chuyện: {str(e)}")
            return {'success': False, 'error': str(e), 'data': []}

    @http.route('/sbotchat/conversation/<int:conversation_id>/archive', type='json', auth='user', methods=['POST'])
    def archive_conversation(self, conversation_id):
        """Archive conversation (alias for soft delete)"""
        try:
            return self.delete_conversation(conversation_id)
        except Exception as e:
            _logger.error(f"Lỗi khi lưu trữ cuộc trò chuyện: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'}

    @http.route('/sbotchat/conversation/<int:conversation_id>/duplicate', type='json', auth='user', methods=['POST'])
    def duplicate_conversation(self, conversation_id, new_title=None):
        """Duplicate conversation with all messages"""
        try:
            original_conv = request.env['sbotchat.conversation'].browse(conversation_id)
            if not original_conv.exists():
                return {'success': False, 'error': 'Không tìm thấy cuộc trò chuyện gốc'}
            
            # Check ownership
            if original_conv.user_id.id != request.env.user.id:
                return {'success': False, 'error': 'Bạn không có quyền sao chép cuộc trò chuyện này'}
            
            # Create new title
            if not new_title:
                new_title = f"Copy of {original_conv.title}"
            
            # Create new conversation
            new_conv = request.env['sbotchat.conversation'].create({
                'title': new_title,
                'user_id': request.env.user.id,
                'is_active': True,
            })
            
            # Copy all messages
            for msg in original_conv.message_ids.sorted('create_date'):
                request.env['sbotchat.message'].create({
                    'conversation_id': new_conv.id,
                    'role': msg.role,
                    'content': msg.content,
                    'model_used': msg.model_used,
                    'tokens_used': msg.tokens_used,
                    'response_time': msg.response_time,
                    'thinking_content': msg.thinking_content,
                })
            
            _logger.info(f"Đã sao chép cuộc trò chuyện {conversation_id} thành {new_conv.id}")
            
            return {
                'success': True, 
                'message': f'Đã sao chép cuộc trò chuyện thành "{new_title}"',
                'new_conversation_id': new_conv.id,
                'new_title': new_title
            }
            
        except Exception as e:
            _logger.error(f"Lỗi khi sao chép cuộc trò chuyện: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'}

    @http.route('/sbotchat/conversation/<int:conversation_id>/export', type='json', auth='user')
    def export_conversation(self, conversation_id, format='json'):
        """Export conversation to various formats"""
        try:
            conversation = request.env['sbotchat.conversation'].browse(conversation_id)
            if not conversation.exists():
                return {'success': False, 'error': 'Không tìm thấy cuộc trò chuyện'}
            
            # Check ownership
            if conversation.user_id.id != request.env.user.id:
                return {'success': False, 'error': 'Bạn không có quyền xuất cuộc trò chuyện này'}
            
            # Collect conversation data
            messages = []
            for msg in conversation.message_ids.sorted('create_date'):
                messages.append({
                    'role': msg.role,
                    'content': msg.content,
                    'thinking': msg.thinking_content or '',
                    'model_used': msg.model_used or '',
                    'timestamp': msg.create_date.isoformat() if msg.create_date else None,
                    'tokens_used': msg.tokens_used,
                    'response_time': msg.response_time,
                })
            
            export_data = {
                'conversation': {
                    'id': conversation.id,
                    'title': conversation.title,
                    'created_date': conversation.create_date.isoformat() if conversation.create_date else None,
                    'last_message_date': conversation.last_message_date.isoformat() if conversation.last_message_date else None,
                    'message_count': len(messages),
                    'user': conversation.user_id.name,
                },
                'messages': messages,
                'export_date': fields.Datetime.now().isoformat(),
                'format': format
            }
            
            if format.lower() == 'text':
                # Convert to readable text format
                text_content = f"# {conversation.title}\n\n"
                text_content += f"Xuất ngày: {fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                text_content += f"Tổng tin nhắn: {len(messages)}\n\n"
                text_content += "=" * 50 + "\n\n"
                
                for msg in messages:
                    role_display = {
                        'user': '👤 Người dùng',
                        'assistant': '🤖 Trợ lý',
                        'system': '🔧 Hệ thống'
                    }.get(msg['role'], msg['role'])
                    
                    text_content += f"{role_display}:\n{msg['content']}\n\n"
                    if msg['thinking']:
                        text_content += f"💭 Suy nghĩ: {msg['thinking']}\n\n"
                    text_content += "-" * 30 + "\n\n"
                
                return {
                    'success': True,
                    'data': text_content,
                    'format': 'text',
                    'filename': f"{conversation.title}_export.txt"
                }
            else:
                # Return JSON format
                return {
                    'success': True,
                    'data': export_data,
                    'format': 'json',
                    'filename': f"{conversation.title}_export.json"
                }
            
        except Exception as e:
            _logger.error(f"Lỗi khi xuất cuộc trò chuyện: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'}

    @http.route('/sbotchat/conversations/bulk_delete', type='json', auth='user', methods=['POST'])
    def bulk_delete_conversations(self, conversation_ids, permanent=False):
        """Bulk delete multiple conversations"""
        try:
            if not conversation_ids or not isinstance(conversation_ids, list):
                return {'success': False, 'error': 'Danh sách ID cuộc trò chuyện không hợp lệ'}
            
            conversations = request.env['sbotchat.conversation'].browse(conversation_ids)
            if not conversations:
                return {'success': False, 'error': 'Không tìm thấy cuộc trò chuyện nào'}
            
            # Check ownership for all conversations
            for conv in conversations:
                if conv.user_id.id != request.env.user.id:
                    return {'success': False, 'error': f'Bạn không có quyền xóa cuộc trò chuyện "{conv.title}"'}
            
            success_count = 0
            error_count = 0
            
            for conv in conversations:
                try:
                    if permanent:
                        conv.permanent_delete_conversation()
                    else:
                        conv.delete_conversation()
                    success_count += 1
                except Exception as e:
                    _logger.error(f"Lỗi khi xóa cuộc trò chuyện {conv.id}: {str(e)}")
                    error_count += 1
            
            delete_type = "vĩnh viễn" if permanent else "tạm thời"
            message = f"Đã xóa {delete_type} {success_count} cuộc trò chuyện"
            if error_count > 0:
                message += f", {error_count} cuộc trò chuyện lỗi"
            
            return {
                'success': True,
                'message': message,
                'success_count': success_count,
                'error_count': error_count,
                'permanent': permanent
            }
            
        except Exception as e:
            _logger.error(f"Lỗi khi xóa hàng loạt cuộc trò chuyện: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'}

    @http.route('/sbotchat/conversations/bulk_restore', type='json', auth='user', methods=['POST'])
    def bulk_restore_conversations(self, conversation_ids):
        """Bulk restore multiple conversations"""
        try:
            if not conversation_ids or not isinstance(conversation_ids, list):
                return {'success': False, 'error': 'Danh sách ID cuộc trò chuyện không hợp lệ'}
            
            conversations = request.env['sbotchat.conversation'].browse(conversation_ids)
            if not conversations:
                return {'success': False, 'error': 'Không tìm thấy cuộc trò chuyện nào'}
            
            # Check ownership for all conversations
            for conv in conversations:
                if conv.user_id.id != request.env.user.id:
                    return {'success': False, 'error': f'Bạn không có quyền khôi phục cuộc trò chuyện "{conv.title}"'}
            
            success_count = 0
            error_count = 0
            
            for conv in conversations:
                try:
                    conv.restore_conversation()
                    success_count += 1
                except Exception as e:
                    _logger.error(f"Lỗi khi khôi phục cuộc trò chuyện {conv.id}: {str(e)}")
                    error_count += 1
            
            message = f"Đã khôi phục {success_count} cuộc trò chuyện"
            if error_count > 0:
                message += f", {error_count} cuộc trò chuyện lỗi"
            
            return {
                'success': True,
                'message': message,
                'success_count': success_count,
                'error_count': error_count
            }
            
        except Exception as e:
            _logger.error(f"Lỗi khi khôi phục hàng loạt cuộc trò chuyện: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'}

    @http.route('/sbotchat/conversations/search', type='json', auth='user')
    def search_conversations(self, query, limit=20, include_inactive=False):
        """Search conversations by title or content"""
        try:
            if not query or not query.strip():
                return {'success': False, 'error': 'Từ khóa tìm kiếm không được để trống'}
            
            query = query.strip()
            limit = int(limit) if limit else 20
            
            # Build domain
            domain = [('user_id', '=', request.env.user.id)]
            if not include_inactive:
                domain.append(('is_active', '=', True))
            
            # Search by title
            title_domain = domain + [('title', 'ilike', query)]
            conversations = request.env['sbotchat.conversation'].search(
                title_domain, 
                order='last_message_date desc', 
                limit=limit
            )
            
            # If not enough results, also search in message content
            if len(conversations) < limit:
                remaining_limit = limit - len(conversations)
                message_domain = domain + [('message_ids.content', 'ilike', query)]
                additional_convs = request.env['sbotchat.conversation'].search(
                    message_domain,
                    order='last_message_date desc',
                    limit=remaining_limit
                )
                # Merge and remove duplicates
                all_conv_ids = list(set(conversations.ids + additional_convs.ids))
                conversations = request.env['sbotchat.conversation'].browse(all_conv_ids)
            
            result = []
            for conv in conversations[:limit]:
                try:
                    # Find matching messages
                    matching_messages = conv.message_ids.filtered(
                        lambda m: query.lower() in m.content.lower()
                    )
                    
                    result.append({
                        'id': conv.id,
                        'title': conv.title or 'Chat không có tiêu đề',
                        'message_count': conv.message_count,
                        'last_message_date': conv.last_message_date.isoformat() if conv.last_message_date else None,
                        'is_active': conv.is_active,
                        'matching_messages_count': len(matching_messages),
                        'title_match': query.lower() in conv.title.lower() if conv.title else False,
                    })
                except Exception as e:
                    _logger.error(f"Lỗi khi xử lý kết quả tìm kiếm {conv.id}: {str(e)}")
                    continue
            
            return {
                'success': True,
                'data': result,
                'query': query,
                'total_found': len(result),
                'include_inactive': include_inactive
            }
            
        except Exception as e:
            _logger.error(f"Lỗi khi tìm kiếm cuộc trò chuyện: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'}

    @http.route('/sbotchat/conversations/stats', type='json', auth='user')
    def get_conversation_stats(self):
        """Get user's conversation statistics"""
        try:
            user_id = request.env.user.id
            
            # Basic counts
            total_conversations = request.env['sbotchat.conversation'].search_count([
                ('user_id', '=', user_id)
            ])
            
            active_conversations = request.env['sbotchat.conversation'].search_count([
                ('user_id', '=', user_id),
                ('is_active', '=', True)
            ])
            
            deleted_conversations = request.env['sbotchat.conversation'].search_count([
                ('user_id', '=', user_id),
                ('is_active', '=', False)
            ])
            
            # Message counts
            total_messages = request.env['sbotchat.message'].search_count([
                ('conversation_id.user_id', '=', user_id)
            ])
            
            user_messages = request.env['sbotchat.message'].search_count([
                ('conversation_id.user_id', '=', user_id),
                ('role', '=', 'user')
            ])
            
            assistant_messages = request.env['sbotchat.message'].search_count([
                ('conversation_id.user_id', '=', user_id),
                ('role', '=', 'assistant')
            ])
            
            # Recent activity
            recent_conversations = request.env['sbotchat.conversation'].search([
                ('user_id', '=', user_id),
                ('is_active', '=', True)
            ], order='last_message_date desc', limit=5)
            
            recent_activity = []
            for conv in recent_conversations:
                recent_activity.append({
                    'id': conv.id,
                    'title': conv.title,
                    'last_message_date': conv.last_message_date.isoformat() if conv.last_message_date else None,
                    'message_count': conv.message_count
                })
            
            # Calculate averages
            avg_messages_per_conversation = round(total_messages / total_conversations, 1) if total_conversations > 0 else 0
            
            return {
                'success': True,
                'stats': {
                    'conversations': {
                        'total': total_conversations,
                        'active': active_conversations,
                        'deleted': deleted_conversations,
                        'deletion_rate': round((deleted_conversations / total_conversations * 100), 1) if total_conversations > 0 else 0
                    },
                    'messages': {
                        'total': total_messages,
                        'user_messages': user_messages,
                        'assistant_messages': assistant_messages,
                        'avg_per_conversation': avg_messages_per_conversation
                    },
                    'recent_activity': recent_activity,
                    'generated_at': fields.Datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            _logger.error(f"Lỗi khi lấy thống kê cuộc trò chuyện: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'}

    @http.route('/sbotchat/cleanup/old_conversations', type='json', auth='user', methods=['POST'])
    def cleanup_old_conversations(self, days_threshold=30, permanent=False):
        """Cleanup old inactive conversations"""
        try:
            days_threshold = int(days_threshold) if days_threshold else 30
            threshold_date = fields.Datetime.now() - fields.timedelta(days=days_threshold)
            
            # Find old inactive conversations
            old_conversations = request.env['sbotchat.conversation'].search([
                ('user_id', '=', request.env.user.id),
                ('is_active', '=', False),
                ('write_date', '<', threshold_date)
            ])
            
            if not old_conversations:
                return {
                    'success': True,
                    'message': f'Không tìm thấy cuộc trò chuyện cũ hơn {days_threshold} ngày để dọn dẹp',
                    'cleaned_count': 0
                }
            
            cleaned_count = 0
            for conv in old_conversations:
                try:
                    if permanent:
                        conv.permanent_delete_conversation()
                    else:
                        # Just mark for final cleanup later
                        conv.write({'title': f"[TO_DELETE] {conv.title}"})
                    cleaned_count += 1
                except Exception as e:
                    _logger.error(f"Lỗi khi dọn dẹp cuộc trò chuyện {conv.id}: {str(e)}")
            
            action_type = "xóa vĩnh viễn" if permanent else "đánh dấu để xóa"
            
            return {
                'success': True,
                'message': f'Đã {action_type} {cleaned_count} cuộc trò chuyện cũ hơn {days_threshold} ngày',
                'cleaned_count': cleaned_count,
                'days_threshold': days_threshold,
                'permanent': permanent
            }
            
        except Exception as e:
            _logger.error(f"Lỗi khi dọn dẹp cuộc trò chuyện cũ: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'} 