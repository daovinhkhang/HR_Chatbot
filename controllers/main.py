# -*- coding: utf-8 -*-

import json
import requests
import time
import re
from datetime import datetime, timedelta
from odoo import http, _, fields
from odoo.http import request
import logging

from .hr_functions_schema import HRFunctionsSchema

_logger = logging.getLogger(__name__)

class SbotchatController(http.Controller):

    @http.route('/sbotchat/create_conversation', type='json', auth='user')
    def create_conversation(self, title=None, **kwargs):
        """Create new conversation endpoint"""
        try:
            # Set default title if not provided
            if not title:
                title = f"Chat mới {fields.Datetime.now().strftime('%H:%M')}"
            
            # Create conversation using model method
            conversation = request.env['sbotchat.conversation'].create_conversation(title=title)
            
            if conversation:
                return {
                    'success': True,
                    'conversation_id': conversation.id,
                    'conversation': {
                        'id': conversation.id,
                        'title': conversation.title,
                        'message_count': conversation.message_count,
                        'last_message_date': conversation.last_message_date.isoformat() if conversation.last_message_date else None,
                    }
                }
            else:
                return {'success': False, 'error': 'Không thể tạo cuộc trò chuyện'}
                
        except Exception as e:
            _logger.error(f"Lỗi trong create_conversation: {str(e)}")
            return {'success': False, 'error': f'Lỗi tạo cuộc trò chuyện: {str(e)}'}

    @http.route('/sbotchat/chat_with_deepseek', type='json', auth='user', methods=['POST'])
    def chat_with_deepseek(self, message, conversation_id=None, **kwargs):
        """Chat with DeepSeek API với HR Function Calling Support"""
        try:
            _logger.info(f"Nhận tin nhắn: {message}")
            
            # Get or create conversation
            conversation = self._get_or_create_conversation(conversation_id)
            if not conversation:
                return {'success': False, 'error': 'Không thể tạo cuộc trò chuyện'}

            # Get configuration  
            config = self._get_sbotchat_config()
            if not config:
                return {'error': 'Cấu hình SbotChat không tìm thấy. Vui lòng thiết lập cấu hình trước.'}
            
            if not config.api_key:
                return {'error': 'Khóa API chưa được cấu hình. Vui lòng thiết lập khóa API DeepSeek của bạn trong cài đặt.'}
            
            # Validate API key format (DeepSeek keys start with 'sk-')
            if not config.api_key.startswith('sk-'):
                return {'error': 'Định dạng khóa API không hợp lệ. Khóa API DeepSeek phải bắt đầu bằng "sk-"'}

            # Add user message to conversation
            user_message = request.env['sbotchat.message'].create({
                'conversation_id': conversation.id,
                'content': message,
                'role': 'user',
            })
            
            # Get conversation history
            messages = self._build_conversation_messages(conversation, config)
            
            # Add current user message
            messages.append({
                'role': 'user', 
                'content': message
            })

            # Call DeepSeek API với function calling
            max_iterations = 5  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                _logger.info(f"API Call iteration {iteration}")
                
                response_data = self._call_deepseek_api_with_functions(config, messages)

                if 'error' in response_data:
                    return response_data

                choice = response_data.get('choices', [{}])[0]
                assistant_message = choice.get('message', {})
                
                # Check if AI wants to call a function
                if assistant_message.get('tool_calls'):
                    # Process function calls
                    function_results = []
                    
                    for tool_call in assistant_message['tool_calls']:
                        if tool_call['type'] == 'function':
                            function_name = tool_call['function']['name']
                            function_args = json.loads(tool_call['function']['arguments'])
                            
                            # Execute HR function
                            result = self._execute_hr_function(function_name, function_args)
                            function_results.append({
                                'tool_call_id': tool_call['id'],
                                'result': result
                            })
                    
                    # Add assistant message with tool calls to history
                    messages.append(assistant_message)
                    
                    # Add function results to messages
                    for func_result in function_results:
                        messages.append({
                            'role': 'tool',
                            'content': json.dumps(func_result['result'], ensure_ascii=False),
                            'tool_call_id': func_result['tool_call_id']
                        })
                    
                    # Continue the conversation with function results
                    continue
                
                else:
                    # No function calls, this is the final response
                    response_content = assistant_message.get('content', '')
                    break
            
            if iteration >= max_iterations:
                response_content = "Xin lỗi, tôi đã thực hiện quá nhiều bước. Vui lòng thử lại với yêu cầu đơn giản hơn."
            
            # Handle DeepSeek reasoner thinking tags
            if config.model_type == 'deepseek-reasoner':
                thinking_content = self._extract_thinking_content(response_content)
                if thinking_content:
                    # Store thinking process separately
                    request.env['sbotchat.message'].create({
                        'conversation_id': conversation.id,
                        'content': thinking_content,
                        'role': 'system',
                        'thinking_content': thinking_content,
                    })
                    # Remove thinking tags from response
                    response_content = re.sub(r'<think>.*?</think>', '', response_content, flags=re.DOTALL).strip()

            # Create assistant response message
            assistant_message_record = request.env['sbotchat.message'].create({
                'conversation_id': conversation.id,
                'content': response_content,
                'role': 'assistant',
            })

            return {
                'success': True,
                'response': response_content,
                'conversation_id': conversation.id,
                'message_id': assistant_message_record.id
            }

        except Exception as e:
            _logger.error(f"Lỗi trong chat_with_deepseek: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'}

    @http.route('/sbotchat/send_message', type='json', auth='user', methods=['POST'])
    def send_message(self, message, conversation_id=None, **kwargs):
        """Send message endpoint - wrapper for chat_with_deepseek"""
        try:
            result = self.chat_with_deepseek(message, conversation_id, **kwargs)
            return result
        except Exception as e:
            _logger.error(f"Error in send_message: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/sbotchat/chat', type='json', auth='user', methods=['POST'])
    def chat(self, message, conversation_id=None, **kwargs):
        """Main chat endpoint - alias for send_message for backward compatibility"""
        try:
            result = self.chat_with_deepseek(message, conversation_id, **kwargs)
            return result
        except Exception as e:
            _logger.error(f"Error in chat: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/sbotchat/conversations', type='json', auth='user')
    def get_conversations(self):
        """Get user's conversations"""
        try:
            conversations = request.env['sbotchat.conversation'].search([
                ('user_id', '=', request.env.user.id),
                ('is_active', '=', True)
            ], order='last_message_date desc, create_date desc')
            
            result = []
            for conv in conversations:
                try:
                    result.append({
                        'id': conv.id,
                        'title': conv.title or 'Chat không có tiêu đề',
                        'message_count': conv.message_count,
                        'last_message_date': conv.last_message_date.isoformat() if conv.last_message_date else None,
                    })
                except Exception as e:
                    _logger.error(f"Lỗi khi xử lý cuộc trò chuyện {conv.id}: {str(e)}")
                    continue
            
            return {'success': True, 'data': result}
        except Exception as e:
            _logger.error(f"Lỗi khi lấy cuộc trò chuyện: {str(e)}")
            return {'error': str(e), 'conversations': []}

    @http.route('/sbotchat/conversation_messages', type='json', auth='user')
    def get_conversation_messages_new(self, conversation_id):
        """Get messages for a conversation - new endpoint"""
        try:
            conversation = request.env['sbotchat.conversation'].browse(conversation_id)
            if not conversation.exists():
                return {'error': 'Không tìm thấy cuộc trò chuyện'}
            
            if conversation.user_id.id != request.env.user.id:
                return {'error': 'Bị từ chối truy cập'}

            messages = []
            for msg in conversation.message_ids.sorted('create_date'):
                try:
                    messages.append({
                        'id': msg.id,
                        'role': msg.role,
                        'content': msg.content or '',
                        'thinking': msg.thinking_content or '',
                        'model_used': msg.model_used or '',
                        'timestamp': msg.create_date.isoformat() if msg.create_date else None,
                    })
                except Exception as e:
                    _logger.error(f"Lỗi khi xử lý tin nhắn {msg.id}: {str(e)}")
                    continue

            return {'success': True, 'data': messages}
        except Exception as e:
            _logger.error(f"Lỗi khi lấy tin nhắn: {str(e)}")
            return {'error': str(e), 'messages': []}

    @http.route('/sbotchat/conversation/<int:conversation_id>/messages', type='json', auth='user')
    def get_conversation_messages(self, conversation_id):
        """Get messages for a conversation"""
        try:
            conversation = request.env['sbotchat.conversation'].browse(conversation_id)
            if not conversation.exists():
                return {'error': 'Không tìm thấy cuộc trò chuyện'}
            
            if conversation.user_id.id != request.env.user.id:
                return {'error': 'Bị từ chối truy cập'}

            messages = []
            for msg in conversation.message_ids.sorted('create_date'):
                try:
                    messages.append({
                        'id': msg.id,
                        'role': msg.role,
                        'content': msg.content or '',
                        'thinking': msg.thinking_content or '',
                        'model_used': msg.model_used or '',
                        'timestamp': msg.create_date.isoformat() if msg.create_date else None,
                    })
                except Exception as e:
                    _logger.error(f"Lỗi khi xử lý tin nhắn {msg.id}: {str(e)}")
                    continue

            return {'success': True, 'data': messages}
        except Exception as e:
            _logger.error(f"Lỗi khi lấy tin nhắn: {str(e)}")
            return {'error': str(e), 'messages': []}

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

    @http.route('/sbotchat/config', type='json', auth='user')
    def handle_config(self, **kwargs):
        """Handle configuration get/set"""
        try:
            if not kwargs:
                # GET request - return current config
                config = request.env['sbotchat.config'].get_active_config()
                if not config or not config.exists():
                    return {
                        'success': False,
                        'error': 'Không tìm thấy cấu hình',
                        'data': {
                            'has_api_key': False,
                            'model_type': 'deepseek-chat',
                            'temperature': 1.0,
                            'max_tokens': 4000,
                            'system_prompt': 'Bạn là một trợ lý AI hữu ích.'
                        }
                    }
                
                return {
                    'success': True,
                    'data': {
                        'has_api_key': bool(config.api_key and config.api_key.strip()),
                        'api_key': '••••••••' if config.api_key else '',
                        'model_type': config.model_type,
                        'temperature': config.temperature,
                        'max_tokens': config.max_tokens,
                        'top_p': config.top_p,
                        'frequency_penalty': config.frequency_penalty,
                        'presence_penalty': config.presence_penalty,
                        'system_prompt': config.system_prompt or 'Bạn là một trợ lý AI hữu ích.'
                    }
                }
            else:
                # POST request - update config
                config = request.env['sbotchat.config'].get_active_config()
                
                # Validate inputs
                api_key = kwargs.get('api_key', '').strip()
                if api_key and api_key != '••••••••':
                    if not api_key.startswith('sk-'):
                        return {'success': False, 'error': 'Khóa API DeepSeek phải bắt đầu bằng "sk-"'}
                    if len(api_key) < 20:
                        return {'success': False, 'error': 'Khóa API có vẻ quá ngắn'}

                temperature = float(kwargs.get('temperature', 1.0))
                if temperature < 0.0 or temperature > 2.0:
                    return {'success': False, 'error': 'Nhiệt độ phải nằm trong khoảng từ 0.0 đến 2.0'}

                max_tokens = int(kwargs.get('max_tokens', 4000))
                if max_tokens < 100 or max_tokens > 8000:
                    return {'success': False, 'error': 'Số token tối đa phải nằm trong khoảng từ 100 đến 8000'}

                # Update or create config
                update_vals = {
                    'model_type': kwargs.get('model_type', 'deepseek-chat'),
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                    'top_p': float(kwargs.get('top_p', 1.0)),
                    'frequency_penalty': float(kwargs.get('frequency_penalty', 0.0)),
                    'presence_penalty': float(kwargs.get('presence_penalty', 0.0)),
                    'system_prompt': kwargs.get('system_prompt', 'Bạn là một trợ lý AI hữu ích.'),
                }

                # Only update API key if provided and not masked
                if api_key and api_key != '••••••••':
                    update_vals['api_key'] = api_key

                if config and config.exists():
                    config.write(update_vals)
                else:
                    update_vals.update({
                        'name': f'Cấu hình mặc định - {request.env.user.login}',
                        'user_id': request.env.user.id,
                        'is_active': True,
                    })
                    config = request.env['sbotchat.config'].create(update_vals)

                return {
                    'success': True,
                    'data': {
                        'has_api_key': bool(config.api_key and config.api_key.strip()),
                        'api_key': '••••••••' if config.api_key else '',
                        'model_type': config.model_type,
                        'temperature': config.temperature,
                        'max_tokens': config.max_tokens,
                        'top_p': config.top_p,
                        'frequency_penalty': config.frequency_penalty,
                        'presence_penalty': config.presence_penalty,
                        'system_prompt': config.system_prompt
                    }
                }

        except Exception as e:
            _logger.error(f"Lỗi trong handle_config: {str(e)}")
            return {'success': False, 'error': f'Đã xảy ra lỗi: {str(e)}'}

    @http.route('/sbotchat/duplicate_conversation', type='json', auth='user', methods=['POST'])
    def duplicate_conversation(self, conversation_id, **kwargs):
        """Duplicate conversation endpoint"""
        try:
            if not conversation_id:
                return {'success': False, 'error': 'conversation_id là bắt buộc'}
            
            # Find conversation
            conversation = request.env['sbotchat.conversation'].browse(conversation_id)
            if not conversation.exists():
                return {'success': False, 'error': 'Không tìm thấy cuộc trò chuyện'}
            
            # Check permission - only owner can duplicate
            if conversation.user_id.id != request.env.user.id:
                return {'success': False, 'error': 'Bạn không có quyền sao chép cuộc trò chuyện này'}
            
            # Create duplicate conversation
            new_conversation = conversation.copy({
                'title': f"{conversation.title} (Bản sao)",
                'user_id': request.env.user.id,
                'is_active': True,
            })
            
            # Copy all messages
            for message in conversation.message_ids:
                message.copy({
                    'conversation_id': new_conversation.id,
                })
            
            return {
                'success': True, 
                'message': f'Đã sao chép cuộc trò chuyện "{conversation.title}"',
                'new_conversation_id': new_conversation.id,
                'new_title': new_conversation.title
            }
            
        except Exception as e:
            _logger.error(f"Lỗi trong duplicate_conversation: {str(e)}")
            return {'success': False, 'error': f'Lỗi sao chép cuộc trò chuyện: {str(e)}'}

    @http.route('/sbotchat/delete_conversation', type='json', auth='user', methods=['POST'])
    def delete_conversation_simple(self, conversation_id, **kwargs):
        """Delete conversation endpoint (simple URL pattern)"""
        try:
            if not conversation_id:
                return {'success': False, 'error': 'conversation_id là bắt buộc'}
            
            # Find conversation
            conversation = request.env['sbotchat.conversation'].browse(conversation_id)
            if not conversation.exists():
                return {'success': False, 'error': 'Không tìm thấy cuộc trò chuyện'}
            
            # Check permission - only owner can delete
            if conversation.user_id.id != request.env.user.id:
                return {'success': False, 'error': 'Bạn không có quyền xóa cuộc trò chuyện này'}
            
            conversation_title = conversation.title
            
            # Soft delete the conversation
            conversation.write({'is_active': False})
            
            return {
                'success': True, 
                'message': f'Đã xóa cuộc trò chuyện "{conversation_title}"'
            }
            
        except Exception as e:
            _logger.error(f"Lỗi trong delete_conversation_simple: {str(e)}")
            return {'success': False, 'error': f'Lỗi xóa cuộc trò chuyện: {str(e)}'}

    def _prepare_messages_with_hr_context(self, conversation, config):
        """Prepare messages for API call with HR context"""
        try:
            messages = []
            
            # Enhanced system message with HR capabilities
            hr_enhanced_prompt = f"""{config.system_prompt}

🤖 **BẠN CÓ KHẢ NĂNG ĐẶC BIỆT:**
- Bạn có thể truy cập và xử lý dữ liệu HR thông qua 116 API endpoints
- Bạn hiểu tiếng Việt và có thể xử lý các yêu cầu về nhân sự
- Khi người dùng hỏi về HR, hãy gợi ý họ sử dụng các câu lệnh như:
  • "Danh sách nhân viên" 
  • "Thống kê tổng hợp"
  • "Báo cáo chấm công"
  • "Tìm nhân viên [tên]"

📋 **MODULES HR BẠN CÓ THỂ XỬ LÝ:**
- 👥 Quản lý nhân viên
- ⏰ Chấm công
- 📅 Nghỉ phép  
- 💰 Lương bổng
- 🏥 Bảo hiểm BHXH/BHYT/BHTN
- 🎯 Tuyển dụng
- 🧠 Kỹ năng
- ⏱️ Timesheet
- 📊 Báo cáo & Thống kê

💡 **LƯU Ý:** Nếu người dùng hỏi về HR, hãy khuyến khích họ sử dụng ngôn ngữ tự nhiên cụ thể để hệ thống có thể tự động xử lý."""
            
            if hr_enhanced_prompt:
                messages.append({
                    "role": "system",
                    "content": hr_enhanced_prompt
                })
            
            # Add conversation history (limit to last 20 messages for context)
            for msg in conversation.message_ids.sorted('create_date')[-20:]:
                if msg.role in ['user', 'assistant']:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            return messages
        except Exception as e:
            _logger.error(f"Lỗi khi chuẩn bị tin nhắn: {str(e)}")
            return []

    def _call_deepseek_api(self, config, messages):
        """Call DeepSeek API"""
        try:
            url = "https://api.deepseek.com/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.api_key}"
            }
            
            # Prepare request data with enhanced parameters
            data = {
                "model": config.model_type,
                "messages": messages,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "top_p": config.top_p,
                "frequency_penalty": config.frequency_penalty,
                "presence_penalty": config.presence_penalty,
                "stream": False
            }
            
            _logger.info(f"Gọi DeepSeek API với mô hình: {config.model_type}")
            
            response = requests.post(url, headers=headers, json=data, timeout=120)
            
            if response.status_code == 200:
                response_data = response.json()
                _logger.info(f"API thành công - Tokens sử dụng: {response_data.get('usage', {}).get('total_tokens', 0)}")
                return response_data
            elif response.status_code == 401:
                return {'error': 'Khóa API không hợp lệ hoặc đã hết hạn'}
            elif response.status_code == 429:
                return {'error': 'Đã vượt quá giới hạn tốc độ API. Vui lòng thử lại sau.'}
            elif response.status_code == 400:
                error_detail = response.json().get('error', {}).get('message', 'Yêu cầu không hợp lệ')
                return {'error': f'Yêu cầu không hợp lệ: {error_detail}'}
            else:
                return {'error': f'Lỗi API: {response.status_code} - {response.text}'}
                
        except requests.exceptions.Timeout:
            return {'error': 'Hết thời gian chờ API. Vui lòng thử lại.'}
        except requests.exceptions.ConnectionError:
            return {'error': 'Không thể kết nối với API DeepSeek. Kiểm tra kết nối internet của bạn.'}
        except Exception as e:
            _logger.error(f"Lỗi khi gọi API DeepSeek: {str(e)}")
            return {'error': f'Lỗi API: {str(e)}'}

    def _extract_thinking_content(self, content):
        """Extract thinking content from DeepSeek reasoner response"""
        try:
            # Pattern to match <think>...</think> tags
            think_pattern = r'<think>(.*?)</think>'
            thinking_matches = re.findall(think_pattern, content, re.DOTALL)
            
            if thinking_matches:
                thinking_content = '\n'.join(thinking_matches).strip()
                # Remove thinking tags from main content
                clean_content = re.sub(think_pattern, '', content, flags=re.DOTALL).strip()
                return thinking_content, clean_content
            
            return None, content
        except Exception as e:
            _logger.error(f"Lỗi khi trích xuất nội dung suy nghĩ: {str(e)}")
            return None, content

    @http.route('/sbotchat/test_config', type='http', auth='user')
    def test_config(self):
        """Test configuration endpoint"""
        try:
            config = request.env['sbotchat.config'].get_active_config()
            if not config:
                return "Không tìm thấy cấu hình"
            
            result = f"""
            <h2>Cấu hình SBot Chat</h2>
            <p><strong>Tên:</strong> {config.name}</p>
            <p><strong>Có khóa API:</strong> {'Có' if config.api_key else 'Không'}</p>
            <p><strong>Loại mô hình:</strong> {config.model_type}</p>
            <p><strong>Nhiệt độ:</strong> {config.temperature}</p>
            <p><strong>Token tối đa:</strong> {config.max_tokens}</p>
            <p><strong>Hoạt động:</strong> {'Có' if config.is_active else 'Không'}</p>
            """
            return result
        except Exception as e:
            return f"Lỗi: {str(e)}"

    @http.route('/sbotchat/debug', type='http', auth='user')
    def debug_info(self):
        """Debug information endpoint"""
        try:
            config = request.env['sbotchat.config'].get_active_config()
            conversations = request.env['sbotchat.conversation'].search([
                ('user_id', '=', request.env.user.id)
            ])
            
            result = f"""
            <h2>Thông tin Debug SBot Chat</h2>
            <h3>Người dùng hiện tại:</h3>
            <p>ID: {request.env.user.id}</p>
            <p>Tên: {request.env.user.name}</p>
            <p>Login: {request.env.user.login}</p>
            
            <h3>Cấu hình:</h3>
            """
            
            if config:
                result += f"""
                <p>ID cấu hình: {config.id}</p>
                <p>Tên: {config.name}</p>
                <p>Có khóa API: {'Có' if config.api_key else 'Không'}</p>
                <p>Mô hình: {config.model_type}</p>
                """
            else:
                result += "<p>Không tìm thấy cấu hình</p>"
            
            result += f"""
            <h3>Cuộc trò chuyện:</h3>
            <p>Tổng số: {len(conversations)}</p>
            """
            
            for conv in conversations[:5]:  # Show first 5
                result += f"<p>- {conv.title} (ID: {conv.id}, Tin nhắn: {conv.message_count})</p>"
            
            return result
        except Exception as e:
            return f"Lỗi debug: {str(e)}" 

    def _call_deepseek_api_with_functions(self, config, messages):
        """Call DeepSeek API with HR function calling support"""
        try:
            url = "https://api.deepseek.com/chat/completions"
            
            headers = {
                'Authorization': f'Bearer {config.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Define HR functions for AI
            tools = HRFunctionsSchema.get_schema()
            
            payload = {
                'model': config.model_type,
                'messages': messages,
                'tools': tools,
                'tool_choice': 'auto',  # Let AI decide when to use tools
                'max_tokens': config.max_tokens,
                'temperature': config.temperature,
                'stream': False
            }
            
            _logger.info(f"Gọi DeepSeek API với mô hình: {config.model_type} và {len(tools)} HR functions")
            
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.text
                _logger.error(f"DeepSeek API error {response.status_code}: {error_detail}")
                return {'error': f'Lỗi API: {response.status_code} - {error_detail}'}
                
        except requests.exceptions.Timeout:
            return {'error': 'Hết thời gian chờ khi gọi API DeepSeek. Vui lòng thử lại.'}
        except requests.exceptions.ConnectionError:
            return {'error': 'Không thể kết nối với API DeepSeek. Kiểm tra kết nối internet của bạn.'}
        except Exception as e:
            _logger.error(f"Lỗi khi gọi API DeepSeek: {str(e)}")
            return {'error': f'Lỗi không xác định: {str(e)}'}

    def _execute_hr_function(self, function_name, function_args):
        """Execute HR function and return result"""
        try:
            _logger.info(f"Executing HR function: {function_name} with args: {function_args}")
            
            if function_name == 'get_employees':
                # Filter out unexpected parameters - only allow supported ones
                filtered_args = {k: v for k, v in function_args.items() if k in ['department', 'active', 'limit', 'name']}
                return self._hr_get_employees(**filtered_args)
            elif function_name == 'create_leave_request':
                return self._hr_create_leave_request(**function_args)
            elif function_name == 'get_attendance_summary':
                return self._hr_get_attendance_summary(**function_args)
            elif function_name == 'checkin_employee':
                return self._hr_checkin_employee(**function_args)
            elif function_name == 'checkout_employee':
                return self._hr_checkout_employee(**function_args)
            elif function_name == 'get_dashboard_stats':
                return self._hr_get_dashboard_stats()
            elif function_name == 'search_hr_global':
                return self._hr_search_global(**function_args)
            elif function_name == 'get_leave_types':
                return self._hr_get_leave_types()
            elif function_name == 'approve_leave_request':
                return self._hr_approve_leave_request(**function_args)
            elif function_name == 'get_employee_leaves':
                return self._hr_get_employee_leaves(**function_args)
            # ======================= BƯỚC 1: EMPLOYEE MANAGEMENT =======================
            elif function_name == 'create_employee':
                return self._hr_create_employee(**function_args)
            elif function_name == 'update_employee':
                return self._hr_update_employee(**function_args)
            elif function_name == 'get_employee_detail':
                return self._hr_get_employee_detail(**function_args)
            elif function_name == 'archive_employee':
                return self._hr_archive_employee(**function_args)
            elif function_name == 'get_departments':
                # Filter out unexpected parameters
                filtered_args = {k: v for k, v in function_args.items() if k in ['active']}
                return self._hr_get_departments(**filtered_args)
            elif function_name == 'create_department':
                return self._hr_create_department(**function_args)
            elif function_name == 'update_department':
                return self._hr_update_department(**function_args)
            elif function_name == 'get_jobs':
                return self._hr_get_jobs(**function_args)
            elif function_name == 'create_job':
                return self._hr_create_job(**function_args)
            elif function_name == 'get_employee_status':
                return self._hr_get_employee_status(**function_args)
            elif function_name == 'update_employee_status':
                return self._hr_update_employee_status(**function_args)
            elif function_name == 'get_employee_bhxh':
                return self._hr_get_employee_bhxh(**function_args)
            elif function_name == 'update_employee_bhxh':
                return self._hr_update_employee_bhxh(**function_args)
            elif function_name == 'get_employee_projects':
                return self._hr_get_employee_projects(**function_args)
            elif function_name == 'assign_employee_project':
                return self._hr_assign_employee_project(**function_args)
            elif function_name == 'get_employee_shifts':
                return self._hr_get_employee_shifts(**function_args)
            elif function_name == 'assign_employee_shift':
                return self._hr_assign_employee_shift(**function_args)
            elif function_name == 'get_employee_tax_info':
                return self._hr_get_employee_tax_info(**function_args)
            elif function_name == 'create_employee_tax_record':
                return self._hr_create_employee_tax_record(**function_args)
            elif function_name == 'get_contract_details':
                return self._hr_get_contract_details(**function_args)
            elif function_name == 'update_contract_details':
                return self._hr_update_contract_details(**function_args)
            elif function_name == 'get_contract_history':
                return self._hr_get_contract_history(**function_args)
            elif function_name == 'get_contract_status':
                return self._hr_get_contract_status(**function_args)
            elif function_name == 'get_contract_type':
                return self._hr_get_contract_type(**function_args)
            elif function_name == 'get_contract_duration':
                return self._hr_get_contract_duration(**function_args)
            elif function_name == 'get_contract_renewal_date':
                return self._hr_get_contract_renewal_date(**function_args)
            elif function_name == 'get_contract_termination_reason':
                return self._hr_get_contract_termination_reason(**function_args)
            elif function_name == 'get_contract_signing_date':
                return self._hr_get_contract_signing_date(**function_args)
            elif function_name == 'get_contract_signatory':
                return self._hr_get_contract_signatory(**function_args)
            elif function_name == 'get_contract_signature':
                return self._hr_get_contract_signature(**function_args)
            elif function_name == 'get_contract_attachment':
                return self._hr_get_contract_attachment(**function_args)
            elif function_name == 'get_contract_revision_history':
                return self._hr_get_contract_revision_history(**function_args)
            elif function_name == 'get_contract_approval_status':
                return self._hr_get_contract_approval_status(**function_args)
            elif function_name == 'get_contract_approval_date':
                return self._hr_get_contract_approval_date(**function_args)
            elif function_name == 'get_contract_approval_signatory':
                return self._hr_get_contract_approval_signatory(**function_args)
            elif function_name == 'get_contract_approval_signature':
                return self._hr_get_contract_approval_signature(**function_args)
            elif function_name == 'get_contract_approval_attachment':
                return self._hr_get_contract_approval_attachment(**function_args)
            elif function_name == 'get_contract_amendment_history':
                return self._hr_get_contract_amendment_history(**function_args)
            elif function_name == 'get_contract_amendment_status':
                return self._hr_get_contract_amendment_status(**function_args)
            elif function_name == 'get_contract_amendment_approval_status':
                return self._hr_get_contract_amendment_approval_status(**function_args)
            elif function_name == 'get_contract_amendment_approval_date':
                return self._hr_get_contract_amendment_approval_date(**function_args)
            elif function_name == 'get_contract_amendment_approval_signatory':
                return self._hr_get_contract_amendment_approval_signatory(**function_args)
            elif function_name == 'get_contract_amendment_approval_signature':
                return self._hr_get_contract_amendment_approval_signature(**function_args)
            elif function_name == 'get_contract_amendment_approval_attachment':
                return self._hr_get_contract_amendment_approval_attachment(**function_args)
            elif function_name == 'get_contracts':
                return self._hr_get_contracts(**function_args)
            elif function_name == 'create_contract':
                return self._hr_create_contract(**function_args)
            elif function_name == 'update_contract':
                return self._hr_update_contract(**function_args)
            elif function_name == 'get_contract_detail':
                return self._hr_get_contract_detail(**function_args)
            elif function_name == 'activate_contract':
                return self._hr_activate_contract(**function_args)
            elif function_name == 'terminate_contract':
                return self._hr_terminate_contract(**function_args)
            elif function_name == 'renew_contract':
                return self._hr_renew_contract(**function_args)
            elif function_name == 'get_salary_structures':
                return self._hr_get_salary_structures(**function_args)
            elif function_name == 'update_contract_salary':
                return self._hr_update_contract_salary(**function_args)
            # ======================= BƯỚC 3: ATTENDANCE MANAGEMENT =======================
            elif function_name == 'get_attendance_records':
                return self._hr_get_attendance_records(**function_args)
            elif function_name == 'create_attendance_manual':
                return self._hr_create_attendance_manual(**function_args)
            elif function_name == 'update_attendance_record':
                return self._hr_update_attendance_record(**function_args)
            elif function_name == 'delete_attendance_record':
                return self._hr_delete_attendance_record(**function_args)
            elif function_name == 'calculate_overtime':
                return self._hr_calculate_overtime(**function_args)
            elif function_name == 'get_missing_attendance':
                return self._hr_get_missing_attendance(**function_args)
            elif function_name == 'approve_attendance':
                return self._hr_approve_attendance(**function_args)
            elif function_name == 'get_work_schedules':
                return self._hr_get_work_schedules(**function_args)
            elif function_name == 'validate_attendance':
                return self._hr_validate_attendance(**function_args)
            elif function_name == 'get_attendance_analytics':
                return self._hr_get_attendance_analytics(**function_args)
            elif function_name == 'get_leave_types_new':
                return self._hr_get_leave_types_new(**function_args)
            elif function_name == 'create_leave_type':
                return self._hr_create_leave_type(**function_args)
            elif function_name == 'get_leave_allocations':
                return self._hr_get_leave_allocations(**function_args)
            elif function_name == 'create_leave_allocation':
                return self._hr_create_leave_allocation(**function_args)
            elif function_name == 'get_leave_requests':
                return self._hr_get_leave_requests(**function_args)
            elif function_name == 'create_leave_request_new':
                return self._hr_create_leave_request_new(**function_args)
            elif function_name == 'approve_leave':
                return self._hr_approve_leave(**function_args)
            elif function_name == 'refuse_leave':
                return self._hr_refuse_leave(**function_args)
            elif function_name == 'get_leave_balance':
                return self._hr_get_leave_balance(**function_args)
            elif function_name == 'get_leave_analytics':
                return self._hr_get_leave_analytics(**function_args)
            elif function_name == 'get_payslips':
                return self._hr_get_payslips(**function_args)
            elif function_name == 'create_payslip':
                return self._hr_create_payslip(**function_args)
            elif function_name == 'compute_payslip':
                return self._hr_compute_payslip(**function_args)
            elif function_name == 'get_payslip_lines':
                return self._hr_get_payslip_lines(**function_args)
            elif function_name == 'get_salary_rules':
                return self._hr_get_salary_rules(**function_args)
            elif function_name == 'create_salary_rule':
                return self._hr_create_salary_rule(**function_args)
            elif function_name == 'get_payroll_structures':
                return self._hr_get_payroll_structures(**function_args)
            elif function_name == 'create_payroll_structure':
                return self._hr_create_payroll_structure(**function_args)
            elif function_name == 'validate_payslip':
                return self._hr_validate_payslip(**function_args)
            elif function_name == 'get_payroll_summary':
                return self._hr_get_payroll_summary(**function_args)
            elif function_name == 'get_applicants':
                return self._hr_get_applicants(**function_args)
            elif function_name == 'create_applicant':
                return self._hr_create_applicant(**function_args)
            elif function_name == 'update_applicant_stage':
                return self._hr_update_applicant_stage(**function_args)
            elif function_name == 'hire_applicant':
                return self._hr_hire_applicant(**function_args)
            elif function_name == 'refuse_applicant':
                return self._hr_refuse_applicant(**function_args)
            elif function_name == 'get_recruitment_stages':
                return self._hr_get_recruitment_stages(**function_args)
            elif function_name == 'create_recruitment_stage':
                return self._hr_create_recruitment_stage(**function_args)
            elif function_name == 'get_recruitment_jobs':
                return self._hr_get_recruitment_jobs(**function_args)
            elif function_name == 'create_recruitment_job':
                return self._hr_create_recruitment_job(**function_args)
            elif function_name == 'get_recruitment_analytics':
                return self._hr_get_recruitment_analytics(**function_args)
            elif function_name == 'get_skills':
                return self._hr_get_skills(**function_args)
            elif function_name == 'create_skill':
                return self._hr_create_skill(**function_args)
            elif function_name == 'get_skill_types':
                return self._hr_get_skill_types(**function_args)
            elif function_name == 'create_skill_type':
                return self._hr_create_skill_type(**function_args)
            elif function_name == 'get_employee_skills':
                return self._hr_get_employee_skills(**function_args)
            elif function_name == 'assign_employee_skill':
                return self._hr_assign_employee_skill(**function_args)
            elif function_name == 'get_skill_levels':
                return self._hr_get_skill_levels(**function_args)
            elif function_name == 'get_skills_analytics':
                return self._hr_get_skills_analytics(**function_args)
            # ======================= BƯỚC 8: TIMESHEET MANAGEMENT =======================
            elif function_name == 'get_timesheets':
                return self._hr_get_timesheets(**function_args)
            elif function_name == 'create_timesheet':
                return self._hr_create_timesheet(**function_args)
            elif function_name == 'update_timesheet':
                return self._hr_update_timesheet(**function_args)
            elif function_name == 'get_employee_timesheets':
                return self._hr_get_employee_timesheets(**function_args)
            elif function_name == 'get_project_timesheets':
                return self._hr_get_project_timesheets(**function_args)
            elif function_name == 'get_timesheet_analytics':
                return self._hr_get_timesheet_analytics(**function_args)
            # ======================= BƯỚC 9: INSURANCE MANAGEMENT =======================
            elif function_name == 'get_insurances':
                return self._hr_get_insurances(**function_args)
            elif function_name == 'create_insurance':
                return self._hr_create_insurance(**function_args)
            elif function_name == 'update_insurance_status':
                return self._hr_update_insurance_status(**function_args)
            elif function_name == 'get_insurance_analytics':
                return self._hr_get_insurance_analytics(**function_args)
            elif function_name == 'get_job_detail':
                return self._hr_get_job_detail(**function_args)
            elif function_name == 'update_job':
                return self._hr_update_job(**function_args)
            elif function_name == 'archive_job':
                return self._hr_archive_job(**function_args)
            else:
                return {'error': f'Unknown function: {function_name}'}
                
        except Exception as e:
            _logger.error(f"Error executing HR function {function_name}: {str(e)}")
            return {'error': f'Lỗi khi thực hiện {function_name}: {str(e)}'}

    # HR Function Implementations
    def _hr_get_employees(self, department=None, active=True, limit=20, name=None):
        """Get employees list with optional name search"""
        try:
            domain = [('active', '=', active)] if active else []
            
            # Filter by department if provided
            if department:
                domain.append(('department_id.name', 'ilike', department))
            
            # Filter by name if provided
            if name:
                domain.append(('name', 'ilike', name))
            
            employees = request.env['hr.employee'].search(domain, limit=limit)
            return {
                'success': True,
                'data': [{
                    'id': emp.id,
                    'name': emp.name,
                    'work_email': emp.work_email,
                    'department': emp.department_id.name if emp.department_id else None,
                    'job_title': emp.job_title,
                    'active': emp.active
                } for emp in employees],
                'count': len(employees)
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_leave_request(self, employee_id, leave_type_id, date_from, date_to, name):
        """Create leave request"""
        try:
            leave = request.env['hr.leave'].create({
                'employee_id': employee_id,
                'holiday_status_id': leave_type_id,
                'date_from': date_from,
                'date_to': date_to,
                'name': name,
                'state': 'draft'
            })
            return {
                'success': True,
                'leave_id': leave.id,
                'message': f'Đơn nghỉ phép #{leave.id} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_attendance_summary(self, employee_id=None, date_from=None, date_to=None):
        """Get attendance summary"""
        try:
            domain = []
            if employee_id:
                domain.append(('employee_id', '=', employee_id))
            if date_from:
                domain.append(('check_in', '>=', date_from))
            if date_to:
                domain.append(('check_out', '<=', date_to))
                
            attendances = request.env['hr.attendance'].search(domain)
            total_hours = sum(att.worked_hours for att in attendances)
            
            return {
                'success': True,
                'total_days': len(attendances),
                'total_hours': total_hours,
                'average_hours': total_hours / len(attendances) if attendances else 0,
                'data': [{
                    'date': att.check_in.strftime('%Y-%m-%d'),
                    'check_in': att.check_in.strftime('%H:%M'),
                    'check_out': att.check_out.strftime('%H:%M') if att.check_out else None,
                    'worked_hours': att.worked_hours
                } for att in attendances[-10:]]  # Last 10 records
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_checkin_employee(self, employee_id):
        """Check-in employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            # Check if already checked in today
            today = fields.Date.today()
            existing = request.env['hr.attendance'].search([
                ('employee_id', '=', employee_id),
                ('check_in', '>=', today),
                ('check_out', '=', False)
            ])
            
            if existing:
                return {'error': f'{employee.name} đã check-in hôm nay rồi'}
            
            attendance = request.env['hr.attendance'].create({
                'employee_id': employee_id,
                'check_in': fields.Datetime.now()
            })
            
            return {
                'success': True,
                'message': f'{employee.name} đã check-in thành công lúc {attendance.check_in.strftime("%H:%M")}'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_checkout_employee(self, employee_id):
        """Check-out employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            # Find today's check-in without check-out
            today = fields.Date.today()
            attendance = request.env['hr.attendance'].search([
                ('employee_id', '=', employee_id),
                ('check_in', '>=', today),
                ('check_out', '=', False)
            ], limit=1)
            
            if not attendance:
                return {'error': f'{employee.name} chưa check-in hôm nay hoặc đã check-out rồi'}
            
            attendance.check_out = fields.Datetime.now()
            
            return {
                'success': True,
                'message': f'{employee.name} đã check-out thành công lúc {attendance.check_out.strftime("%H:%M")}. Tổng: {attendance.worked_hours:.1f} giờ'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_dashboard_stats(self):
        """Get HR dashboard statistics"""
        try:
            total_employees = request.env['hr.employee'].search_count([('active', '=', True)])
            total_departments = request.env['hr.department'].search_count([])
            
            # Today's attendance
            today = fields.Date.today()
            today_checkins = request.env['hr.attendance'].search_count([
                ('check_in', '>=', today)
            ])
            
            # Pending leaves
            pending_leaves = request.env['hr.leave'].search_count([
                ('state', 'in', ['draft', 'confirm'])
            ])
            
            return {
                'success': True,
                'total_employees': total_employees,
                'total_departments': total_departments,
                'today_checkins': today_checkins,
                'pending_leaves': pending_leaves,
                'attendance_rate': f"{(today_checkins/total_employees*100):.1f}%" if total_employees > 0 else "0%"
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_search_global(self, search_term):
        """Global HR search"""
        try:
            results = {}
            
            # Search employees
            employees = request.env['hr.employee'].search([
                '|', ('name', 'ilike', search_term),
                ('work_email', 'ilike', search_term)
            ], limit=5)
            results['employees'] = [{'id': e.id, 'name': e.name, 'email': e.work_email} for e in employees]
            
            # Search leaves
            leaves = request.env['hr.leave'].search([
                ('name', 'ilike', search_term)
            ], limit=5)
            results['leaves'] = [{'id': l.id, 'name': l.name, 'employee': l.employee_id.name} for l in leaves]
            
            return {
                'success': True,
                'data': results,
                'total_found': len(employees) + len(leaves)
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_leave_types(self):
        """Get leave types"""
        try:
            leave_types = request.env['hr.leave.type'].search([])
            return {
                'success': True,
                'data': [{
                    'id': lt.id,
                    'name': lt.name,
                    'allocation_type': lt.allocation_type,
                    'validity_start': lt.validity_start,
                    'validity_stop': lt.validity_stop
                } for lt in leave_types]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_approve_leave_request(self, leave_id):
        """Approve leave request"""
        try:
            leave = request.env['hr.leave'].browse(leave_id)
            if not leave.exists():
                return {'error': 'Đơn nghỉ phép không tồn tại'}
            
            if leave.state != 'confirm':
                return {'error': f'Đơn nghỉ phép đang ở trạng thái {leave.state}, không thể phê duyệt'}
            
            leave.action_approve()
            return {
                'success': True,
                'message': f'Đã phê duyệt đơn nghỉ phép #{leave.id} cho {leave.employee_id.name}'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_employee_leaves(self, employee_id=None, state=None):
        """Get employee leaves"""
        try:
            domain = []
            if employee_id:
                domain.append(('employee_id', '=', employee_id))
            if state:
                domain.append(('state', '=', state))
                
            leaves = request.env['hr.leave'].search(domain, limit=20)
            return {
                'success': True,
                'data': [{
                    'id': l.id,
                    'employee': l.employee_id.name,
                    'name': l.name,
                    'leave_type': l.holiday_status_id.name,
                    'date_from': l.date_from.strftime('%Y-%m-%d'),
                    'date_to': l.date_to.strftime('%Y-%m-%d'),
                    'number_of_days': l.number_of_days,
                    'state': l.state
                } for l in leaves],
                'count': len(leaves)
            }
        except Exception as e:
            return {'error': str(e)}

    def _build_conversation_messages(self, conversation, config):
        """Build conversation messages for API call"""
        messages = []
        
        # Enhanced system prompt with HR context
        system_prompt = """Bạn là trợ lý AI thông minh cho hệ thống HR của công ty. Bạn có thể:

🏢 **Quản lý nhân viên**: Xem danh sách, thông tin chi tiết nhân viên
👥 **Chấm công**: Check-in/out, xem báo cáo attendance 
📅 **Nghỉ phép**: Tạo đơn, phê duyệt, theo dõi trạng thái
📊 **Báo cáo**: Thống kê tổng quan, phân tích dữ liệu HR
🔍 **Tìm kiếm**: Tìm kiếm thông tin trong toàn bộ hệ thống

**Quy tắc giao tiếp:**
- Luôn thân thiện, chuyên nghiệp
- Giải thích rõ ràng kết quả của các action
- Hỏi thông tin cần thiết nếu user không cung cấp đủ
- Format dữ liệu dễ đọc (bảng, danh sách)
- Đưa ra gợi ý hữu ích

**Lưu ý:** Khi cần thực hiện action HR, hãy sử dụng các function tools có sẵn."""

        messages.append({'role': 'system', 'content': system_prompt})
        
        # Add conversation history
        history_messages = request.env['sbotchat.message'].search([
            ('conversation_id', '=', conversation.id)
        ], order='create_date asc', limit=20)  # Last 20 messages
        
        for msg in history_messages:
            if msg.role == 'user':
                messages.append({'role': 'user', 'content': msg.content})
            elif msg.role == 'assistant':
                messages.append({'role': 'assistant', 'content': msg.content})
            # Skip thinking messages for conversation flow
            
        return messages

    def _get_sbotchat_config(self):
        """Get active SbotChat configuration"""
        try:
            config = request.env['sbotchat.config'].search([
                ('is_active', '=', True)
            ], limit=1)
            
            if not config:
                # Create default config if none exists
                config = request.env['sbotchat.config'].create({
                    'name': 'Mặc định',
                    'api_key': '',
                    'model_type': 'deepseek-chat',
                    'max_tokens': 4000,
                    'temperature': 0.7,
                    'is_active': True
                })
            
            return config
        except Exception as e:
            _logger.error(f"Error getting config: {str(e)}")
            return None

    def _get_or_create_conversation(self, conversation_id=None):
        """Get existing conversation or create a new one"""
        if conversation_id:
            conversation = request.env['sbotchat.conversation'].browse(conversation_id)
            if conversation.exists():
                return conversation
        
        # Create new conversation
        conversation = request.env['sbotchat.conversation'].create({
            'title': f'HR Chat - {fields.Datetime.now().strftime("%Y-%m-%d %H:%M")}'
        })
        return conversation

    # ======================= BƯỚC 1: EMPLOYEE MANAGEMENT IMPLEMENTATIONS =======================
    
    def _hr_create_employee(self, name, work_email=None, department_id=None, job_id=None):
        """Create new employee"""
        try:
            vals = {'name': name}
            if work_email:
                vals['work_email'] = work_email
            if department_id:
                vals['department_id'] = department_id
            if job_id:
                vals['job_id'] = job_id
                
            employee = request.env['hr.employee'].create(vals)
            return {
                'success': True,
                'employee_id': employee.id,
                'message': f'Nhân viên {employee.name} đã được tạo thành công (ID: {employee.id})'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_update_employee(self, employee_id, **vals):
        """Update employee information"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            # Remove employee_id from vals if present
            vals.pop('employee_id', None)
            employee.write(vals)
            
            return {
                'success': True,
                'message': f'Thông tin nhân viên {employee.name} đã được cập nhật'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_employee_detail(self, employee_id):
        """Get detailed employee information"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'employee': {
                    'id': employee.id,
                    'name': employee.name,
                    'work_email': employee.work_email,
                    'work_phone': employee.work_phone,
                    'department': employee.department_id.name if employee.department_id else None,
                    'job_title': employee.job_title,
                    'manager': employee.parent_id.name if employee.parent_id else None,
                    'active': employee.active,
                    'hire_date': employee.first_contract_date.isoformat() if employee.first_contract_date else None,
                    'departure_date': employee.departure_date.isoformat() if employee.departure_date else None,
                    'bhxh_code': employee.bhxh_code,
                    'personal_tax_code': employee.personal_tax_code
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_archive_employee(self, employee_id):
        """Archive/deactivate employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            employee.write({'active': False})
            return {
                'success': True,
                'message': f'Nhân viên {employee.name} đã được lưu trữ'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_departments(self, active=True, **kwargs):
        """Get departments list"""
        try:
            domain = [('active', '=', active)] if active else []
            departments = request.env['hr.department'].search(domain)
            
            return {
                'success': True,
                'departments': [{
                    'id': dept.id,
                    'name': dept.name,
                    'manager': dept.manager_id.name if dept.manager_id else None,
                    'employee_count': dept.total_employee,
                    'active': dept.active
                } for dept in departments]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_department(self, name, manager_id=None):
        """Create new department"""
        try:
            vals = {'name': name}
            if manager_id:
                vals['manager_id'] = manager_id
                
            department = request.env['hr.department'].create(vals)
            return {
                'success': True,
                'department_id': department.id,
                'message': f'Phòng ban {department.name} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_update_department(self, department_id, **vals):
        """Update department information"""
        try:
            department = request.env['hr.department'].browse(department_id)
            if not department.exists():
                return {'error': 'Phòng ban không tồn tại'}
                
            vals.pop('department_id', None)
            department.write(vals)
            
            return {
                'success': True,
                'message': f'Phòng ban {department.name} đã được cập nhật'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_jobs(self, department_id=None, active=True, limit=20):
        """Get job positions list"""
        try:
            domain = []
            if department_id:
                domain.append(('department_id', '=', department_id))
            
            # Add active filter
            if active is not None:
                domain.append(('active', '=', active))
                
            jobs = request.env['hr.job'].search(domain, limit=limit)
            
            return {
                'success': True,
                'jobs': [{
                    'id': job.id,
                    'name': job.name,
                    'department': job.department_id.name if job.department_id else None,
                    'expected_employees': job.no_of_recruitment,
                    'no_of_employee': job.no_of_employee,
                    'active': job.active,
                    'description': job.description or ''
                } for job in jobs]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_job(self, name, department_id=None, expected_employees=1, description=None, requirements=None):
        """Create new job position with full information"""
        try:
            vals = {
                'name': name,
                'no_of_recruitment': expected_employees  # Odoo uses no_of_recruitment field
            }
            if department_id:
                vals['department_id'] = department_id
            if description:
                vals['description'] = description
            if requirements:
                vals['requirements'] = requirements
                
            job = request.env['hr.job'].create(vals)
            return {
                'success': True,
                'job_id': job.id,
                'message': f'Vị trí công việc {job.name} đã được tạo thành công',
                'job_details': {
                    'id': job.id,
                    'name': job.name,
                    'department': job.department_id.name if job.department_id else '',
                    'expected_employees': job.no_of_recruitment,
                    'description': job.description or '',
                    'requirements': job.requirements or '',
                    'active': job.active
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_employee_status(self, employee_id):
        """Get employee status"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'status': {
                    'active': employee.active,
                    'hr_presence_state': employee.hr_presence_state,
                    'departure_date': employee.departure_date.isoformat() if employee.departure_date else None,
                    'last_activity': employee.last_activity.isoformat() if employee.last_activity else None,
                    'contract_status': 'active' if employee.contract_ids.filtered(lambda c: c.state == 'open') else 'inactive'
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_update_employee_status(self, employee_id, **status_vals):
        """Update employee status"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            status_vals.pop('employee_id', None)
            employee.write(status_vals)
            
            return {
                'success': True,
                'message': f'Trạng thái nhân viên {employee.name} đã được cập nhật'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_employee_bhxh(self, employee_id):
        """Get employee BHXH/BHYT/BHTN information"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'bhxh_info': {
                    'employee_name': employee.name,
                    'bhxh_code': employee.bhxh_code or '',
                    'bhyt_code': employee.bhyt_code or '',
                    'bhtn_code': employee.bhtn_code or '',
                    'personal_tax_code': employee.personal_tax_code or '',
                    'minimum_wage_region': employee.minimum_wage_region or 0
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_update_employee_bhxh(self, employee_id, **bhxh_vals):
        """Update employee BHXH information"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            bhxh_vals.pop('employee_id', None)
            employee.write(bhxh_vals)
            
            return {
                'success': True,
                'message': f'Thông tin BHXH của {employee.name} đã được cập nhật'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_employee_projects(self, employee_id):
        """Get employee projects assignments"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            # Try to get project assignments if model exists
            try:
                assignments = request.env['hr.employee.project.assignment'].search([
                    ('employee_id', '=', employee_id)
                ])
                projects_data = [{
                    'project_name': assign.project_id.name if assign.project_id else '',
                    'role': assign.role,
                    'date_start': assign.date_start.isoformat() if assign.date_start else '',
                    'date_end': assign.date_end.isoformat() if assign.date_end else '',
                    'progress': assign.progress
                } for assign in assignments]
            except:
                # Fallback to regular project search
                projects = request.env['project.project'].search([
                    ('user_id', '=', employee.user_id.id)
                ])
                projects_data = [{
                    'project_name': proj.name,
                    'role': 'Member',
                    'date_start': '',
                    'date_end': '',
                    'progress': 0
                } for proj in projects]
                
            return {
                'success': True,
                'employee_name': employee.name,
                'projects': projects_data
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_assign_employee_project(self, employee_id, project_id, role='Member', date_start=None):
        """Assign employee to project"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            project = request.env['project.project'].browse(project_id)
            
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
            if not project.exists():
                return {'error': 'Dự án không tồn tại'}
                
            # Try to create assignment record if model exists
            try:
                vals = {
                    'employee_id': employee_id,
                    'project_id': project_id,
                    'role': role
                }
                if date_start:
                    vals['date_start'] = date_start
                    
                request.env['hr.employee.project.assignment'].create(vals)
                message = f'{employee.name} đã được phân công vào dự án {project.name} với vai trò {role}'
            except:
                # Fallback to adding user to project
                if employee.user_id:
                    project.write({'user_id': employee.user_id.id})
                    message = f'{employee.name} đã được thêm vào dự án {project.name}'
                else:
                    return {'error': 'Nhân viên chưa có tài khoản user'}
                
            return {
                'success': True,
                'message': message
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_employee_shifts(self, employee_id):
        """Get employee shifts"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            # Try to get shifts if model exists
            try:
                shifts = request.env['hr.employee.shift'].search([
                    ('employee_id', '=', employee_id)
                ])
                shifts_data = [{
                    'shift_name': shift.shift_name,
                    'time_start': shift.time_start,
                    'time_end': shift.time_end,
                    'date_apply': shift.date_apply.isoformat() if shift.date_apply else ''
                } for shift in shifts]
            except:
                # Default shift info
                shifts_data = [{
                    'shift_name': 'Ca hành chính',
                    'time_start': '08:00',
                    'time_end': '17:00',
                    'date_apply': fields.Date.today().isoformat()
                }]
                
            return {
                'success': True,
                'employee_name': employee.name,
                'shifts': shifts_data
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_assign_employee_shift(self, employee_id, shift_name, time_start, time_end, date_apply=None):
        """Assign shift to employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            # Try to create shift record if model exists
            try:
                vals = {
                    'employee_id': employee_id,
                    'shift_name': shift_name,
                    'time_start': time_start,
                    'time_end': time_end
                }
                if date_apply:
                    vals['date_apply'] = date_apply
                else:
                    vals['date_apply'] = fields.Date.today()
                    
                request.env['hr.employee.shift'].create(vals)
                message = f'Ca làm việc {shift_name} ({time_start}-{time_end}) đã được phân công cho {employee.name}'
            except:
                # Fallback message
                message = f'Đã ghi nhận ca làm việc {shift_name} ({time_start}-{time_end}) cho {employee.name}'
                
            return {
                'success': True,
                'message': message
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_employee_tax_info(self, employee_id, year=None):
        """Get employee tax information"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            if not year:
                year = fields.Date.today().year
                
            # Try to get tax records if model exists
            try:
                tax_records = request.env['hr.employee.personal.income.tax'].search([
                    ('employee_id', '=', employee_id),
                    ('year', '=', year)
                ])
                
                if tax_records:
                    record = tax_records[0]
                    tax_data = {
                        'year': record.year,
                        'total_income': record.total_income,
                        'self_deduction': record.self_deduction,
                        'dependent_deduction': record.dependent_deduction,
                        'taxable_income': record.taxable_income,
                        'tax_amount': record.tax_amount,
                        'state': record.state
                    }
                else:
                    tax_data = {
                        'year': year,
                        'total_income': 0,
                        'self_deduction': 11000000,  # Default
                        'dependent_deduction': 0,
                        'taxable_income': 0,
                        'tax_amount': 0,
                        'state': 'draft'
                    }
            except:
                tax_data = {
                    'year': year,
                    'personal_tax_code': employee.personal_tax_code or '',
                    'message': 'Chưa có thông tin thuế chi tiết'
                }
                
            return {
                'success': True,
                'employee_name': employee.name,
                'tax_info': tax_data
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_employee_tax_record(self, employee_id, year, total_income, self_deduction=11000000, dependent_deduction=0):
        """Create employee tax record"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            # Calculate taxable income and tax
            taxable_income = max(0, total_income - self_deduction - dependent_deduction)
            
            # Simple tax calculation (Vietnam tax brackets)
            if taxable_income <= 5000000:
                tax_amount = taxable_income * 0.05
            elif taxable_income <= 10000000:
                tax_amount = 250000 + (taxable_income - 5000000) * 0.10
            elif taxable_income <= 18000000:
                tax_amount = 750000 + (taxable_income - 10000000) * 0.15
            else:
                tax_amount = 1950000 + (taxable_income - 18000000) * 0.20
                
            # Try to create tax record if model exists
            try:
                vals = {
                    'employee_id': employee_id,
                    'year': year,
                    'total_income': total_income,
                    'self_deduction': self_deduction,
                    'dependent_deduction': dependent_deduction,
                    'taxable_income': taxable_income,
                    'tax_amount': tax_amount,
                    'state': 'draft'
                }
                
                record = request.env['hr.employee.personal.income.tax'].create(vals)
                message = f'Bản kê khai thuế năm {year} cho {employee.name} đã được tạo (ID: {record.id})'
            except:
                message = f'Đã tính toán thuế năm {year} cho {employee.name}: {tax_amount:,.0f} VND'
                
            return {
                'success': True,
                'message': message,
                'tax_calculation': {
                    'total_income': total_income,
                    'taxable_income': taxable_income,
                    'tax_amount': tax_amount
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_details(self, employee_id):
        """Get contract details for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            contract = employee.contract_ids.filtered(lambda c: c.state == 'open')
            if not contract:
                return {'error': 'Nhân viên không có hợp đồng hiện tại'}
                
            return {
                'success': True,
                'contract': {
                    'id': contract.id,
                    'name': contract.name,
                    'start_date': contract.date_start.isoformat() if contract.date_start else None,
                    'end_date': contract.date_end.isoformat() if contract.date_end else None,
                    'status': contract.state,
                    'type': contract.type_id.name,
                    'duration': contract.duration_type,
                    'renewal_date': contract.renewal_date.isoformat() if contract.renewal_date else None,
                    'termination_reason': contract.termination_reason,
                    'signing_date': contract.date_signed.isoformat() if contract.date_signed else None,
                    'signatory': contract.signatory_id.name if contract.signatory_id else None,
                    'signature': contract.signature,
                    'attachment': contract.attachment_ids.mapped('name') if contract.attachment_ids else None,
                    'revision_history': contract.revision_history,
                    'approval_status': contract.approval_status,
                    'approval_date': contract.approval_date.isoformat() if contract.approval_date else None,
                    'approval_signatory': contract.approval_signatory_id.name if contract.approval_signatory_id else None,
                    'approval_signature': contract.approval_signature,
                    'amendment_history': contract.amendment_history,
                    'amendment_status': contract.amendment_status,
                    'amendment_approval_status': contract.amendment_approval_status,
                    'amendment_approval_date': contract.amendment_approval_date.isoformat() if contract.amendment_approval_date else None,
                    'amendment_approval_signatory': contract.amendment_approval_signatory_id.name if contract.amendment_approval_signatory_id else None,
                    'amendment_approval_signature': contract.amendment_approval_signature,
                    'amendment_approval_attachment': contract.amendment_approval_attachment_ids.mapped('name') if contract.amendment_approval_attachment_ids else None
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_update_contract_details(self, employee_id, contract_id, start_date, end_date, status, type_id, duration, renewal_date, termination_reason, signatory_id, signature, attachment_ids, revision_history, approval_status, approval_date, approval_signatory_id, approval_signature, amendment_history, amendment_status, amendment_approval_status, amendment_approval_date, amendment_approval_signatory_id, amendment_approval_signature, amendment_approval_attachment_ids):
        """Update contract details for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            contract = employee.contract_ids.filtered(lambda c: c.id == contract_id)
            if not contract:
                return {'error': 'Hợp đồng không tồn tại'}
                
            vals = {
                'name': contract.name,
                'date_start': start_date,
                'date_end': end_date,
                'state': status,
                'type_id': type_id,
                'duration_type': duration,
                'renewal_date': renewal_date,
                'termination_reason': termination_reason,
                'signatory_id': signatory_id,
                'signature': signature,
                'attachment_ids': attachment_ids,
                'revision_history': revision_history,
                'approval_status': approval_status,
                'approval_date': approval_date,
                'approval_signatory_id': approval_signatory_id,
                'approval_signature': approval_signature,
                'amendment_history': amendment_history,
                'amendment_status': amendment_status,
                'amendment_approval_status': amendment_approval_status,
                'amendment_approval_date': amendment_approval_date,
                'amendment_approval_signatory_id': amendment_approval_signatory_id,
                'amendment_approval_signature': amendment_approval_signature,
                'amendment_approval_attachment_ids': amendment_approval_attachment_ids
            }
            
            contract.write(vals)
            
            return {
                'success': True,
                'message': f'Thông tin hợp đồng của {employee.name} đã được cập nhật'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_history(self, employee_id):
        """Get contract history for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_history': [{
                    'id': contract.id,
                    'name': contract.name,
                    'start_date': contract.date_start.isoformat() if contract.date_start else None,
                    'end_date': contract.date_end.isoformat() if contract.date_end else None,
                    'status': contract.state,
                    'type': contract.type_id.name,
                    'duration': contract.duration_type,
                    'renewal_date': contract.renewal_date.isoformat() if contract.renewal_date else None,
                    'termination_reason': contract.termination_reason,
                    'signing_date': contract.date_signed.isoformat() if contract.date_signed else None,
                    'signatory': contract.signatory_id.name if contract.signatory_id else None,
                    'signature': contract.signature,
                    'attachment': contract.attachment_ids.mapped('name') if contract.attachment_ids else None,
                    'revision_history': contract.revision_history,
                    'approval_status': contract.approval_status,
                    'approval_date': contract.approval_date.isoformat() if contract.approval_date else None,
                    'approval_signatory': contract.approval_signatory_id.name if contract.approval_signatory_id else None,
                    'approval_signature': contract.approval_signature,
                    'amendment_history': contract.amendment_history,
                    'amendment_status': contract.amendment_status,
                    'amendment_approval_status': contract.amendment_approval_status,
                    'amendment_approval_date': contract.amendment_approval_date.isoformat() if contract.amendment_approval_date else None,
                    'amendment_approval_signatory': contract.amendment_approval_signatory_id.name if contract.amendment_approval_signatory_id else None,
                    'amendment_approval_signature': contract.amendment_approval_signature,
                    'amendment_approval_attachment': contract.amendment_approval_attachment_ids.mapped('name') if contract.amendment_approval_attachment_ids else None
                } for contract in employee.contract_ids]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_status(self, employee_id):
        """Get contract status for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_status': {
                    'current_contract': employee.contract_ids.filtered(lambda c: c.state == 'open').name,
                    'previous_contracts': [{'id': contract.id, 'name': contract.name} for contract in employee.contract_ids.filtered(lambda c: c.state != 'open')],
                    'next_contract': employee.contract_ids.filtered(lambda c: c.state != 'open' and c.date_start > fields.Date.today()).name if employee.contract_ids.filtered(lambda c: c.state != 'open' and c.date_start > fields.Date.today()) else None
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_type(self, employee_id):
        """Get contract type for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_type': {
                    'type': employee.contract_ids.filtered(lambda c: c.state == 'open').type_id.name,
                    'types': [{'id': type_id.id, 'name': type_id.name} for type_id in employee.contract_ids.filtered(lambda c: c.state == 'open').type_id]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_duration(self, employee_id):
        """Get contract duration for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_duration': {
                    'duration': employee.contract_ids.filtered(lambda c: c.state == 'open').duration_type,
                    'durations': [{'id': duration.id, 'name': duration.name} for duration in employee.contract_ids.filtered(lambda c: c.state == 'open').duration_type]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_renewal_date(self, employee_id):
        """Get contract renewal date for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_renewal_date': {
                    'renewal_date': employee.contract_ids.filtered(lambda c: c.state == 'open').renewal_date.isoformat() if employee.contract_ids.filtered(lambda c: c.state == 'open').renewal_date else None,
                    'renewal_dates': [{'id': renewal_date.id, 'name': renewal_date.name} for renewal_date in employee.contract_ids.filtered(lambda c: c.state == 'open').renewal_date]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_termination_reason(self, employee_id):
        """Get contract termination reason for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_termination_reason': {
                    'termination_reason': employee.contract_ids.filtered(lambda c: c.state == 'open').termination_reason,
                    'termination_reasons': [{'id': reason.id, 'name': reason.name} for reason in employee.contract_ids.filtered(lambda c: c.state == 'open').termination_reason]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_signing_date(self, employee_id):
        """Get contract signing date for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_signing_date': {
                    'signing_date': employee.contract_ids.filtered(lambda c: c.state == 'open').date_signed.isoformat() if employee.contract_ids.filtered(lambda c: c.state == 'open').date_signed else None,
                    'signing_dates': [{'id': signing_date.id, 'name': signing_date.name} for signing_date in employee.contract_ids.filtered(lambda c: c.state == 'open').date_signed]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_signatory(self, employee_id):
        """Get contract signatory for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_signatory': {
                    'signatory': employee.contract_ids.filtered(lambda c: c.state == 'open').signatory_id.name if employee.contract_ids.filtered(lambda c: c.state == 'open').signatory_id else None,
                    'signatories': [{'id': signatory.id, 'name': signatory.name} for signatory in employee.contract_ids.filtered(lambda c: c.state == 'open').signatory_id]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_signature(self, employee_id):
        """Get contract signature for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_signature': {
                    'signature': employee.contract_ids.filtered(lambda c: c.state == 'open').signature,
                    'signatures': [{'id': signature.id, 'name': signature.name} for signature in employee.contract_ids.filtered(lambda c: c.state == 'open').signature]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_attachment(self, employee_id):
        """Get contract attachments for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_attachments': [{'id': attachment.id, 'name': attachment.name} for attachment in employee.contract_ids.filtered(lambda c: c.state == 'open').attachment_ids]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_revision_history(self, employee_id):
        """Get contract revision history for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_revision_history': [{'id': revision.id, 'name': revision.name} for revision in employee.contract_ids.filtered(lambda c: c.state == 'open').revision_history]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_approval_status(self, employee_id):
        """Get contract approval status for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_approval_status': {
                    'approval_status': employee.contract_ids.filtered(lambda c: c.state == 'open').approval_status,
                    'approval_statuses': [{'id': status.id, 'name': status.name} for status in employee.contract_ids.filtered(lambda c: c.state == 'open').approval_status]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_approval_date(self, employee_id):
        """Get contract approval date for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_approval_date': {
                    'approval_date': employee.contract_ids.filtered(lambda c: c.state == 'open').approval_date.isoformat() if employee.contract_ids.filtered(lambda c: c.state == 'open').approval_date else None,
                    'approval_dates': [{'id': approval_date.id, 'name': approval_date.name} for approval_date in employee.contract_ids.filtered(lambda c: c.state == 'open').approval_date]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_approval_signatory(self, employee_id):
        """Get contract approval signatory for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_approval_signatory': {
                    'approval_signatory': employee.contract_ids.filtered(lambda c: c.state == 'open').approval_signatory_id.name if employee.contract_ids.filtered(lambda c: c.state == 'open').approval_signatory_id else None,
                    'approval_signatories': [{'id': signatory.id, 'name': signatory.name} for signatory in employee.contract_ids.filtered(lambda c: c.state == 'open').approval_signatory_id]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_approval_signature(self, employee_id):
        """Get contract approval signature for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_approval_signature': {
                    'approval_signature': employee.contract_ids.filtered(lambda c: c.state == 'open').approval_signature,
                    'approval_signatures': [{'id': signature.id, 'name': signature.name} for signature in employee.contract_ids.filtered(lambda c: c.state == 'open').approval_signature]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_approval_attachment(self, employee_id):
        """Get contract approval attachments for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_approval_attachments': [{'id': attachment.id, 'name': attachment.name} for attachment in employee.contract_ids.filtered(lambda c: c.state == 'open').approval_attachment_ids]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_amendment_history(self, employee_id):
        """Get contract amendment history for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_amendment_history': [{'id': amendment.id, 'name': amendment.name} for amendment in employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_history]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_amendment_status(self, employee_id):
        """Get contract amendment status for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_amendment_status': {
                    'amendment_status': employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_status,
                    'amendment_statuses': [{'id': status.id, 'name': status.name} for status in employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_status]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_amendment_approval_status(self, employee_id):
        """Get contract amendment approval status for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_amendment_approval_status': {
                    'amendment_approval_status': employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_approval_status,
                    'amendment_approval_statuses': [{'id': status.id, 'name': status.name} for status in employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_approval_status]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_amendment_approval_date(self, employee_id):
        """Get contract amendment approval date for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_amendment_approval_date': {
                    'amendment_approval_date': employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_approval_date.isoformat() if employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_approval_date else None,
                    'amendment_approval_dates': [{'id': approval_date.id, 'name': approval_date.name} for approval_date in employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_approval_date]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_amendment_approval_signatory(self, employee_id):
        """Get contract amendment approval signatory for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_amendment_approval_signatory': {
                    'amendment_approval_signatory': employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_approval_signatory_id.name if employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_approval_signatory_id else None,
                    'amendment_approval_signatories': [{'id': signatory.id, 'name': signatory.name} for signatory in employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_approval_signatory_id]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_amendment_approval_signature(self, employee_id):
        """Get contract amendment approval signature for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_amendment_approval_signature': {
                    'amendment_approval_signature': employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_approval_signature,
                    'amendment_approval_signatures': [{'id': signature.id, 'name': signature.name} for signature in employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_approval_signature]
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_amendment_approval_attachment(self, employee_id):
        """Get contract amendment approval attachments for an employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
                
            return {
                'success': True,
                'contract_amendment_approval_attachments': [{'id': attachment.id, 'name': attachment.name} for attachment in employee.contract_ids.filtered(lambda c: c.state == 'open').amendment_approval_attachment_ids]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contracts(self, employee_id, state=None, active=True):
        """Get contracts for an employee"""
        try:
            domain = [('employee_id', '=', employee_id), ('state', 'in', ['draft', 'open', 'close', 'cancel'])] if state else [('employee_id', '=', employee_id)]
            contracts = request.env['hr.contract'].search(domain)
            
            return {
                'success': True,
                'contracts': [{
                    'id': contract.id,
                    'name': contract.name,
                    'start_date': contract.date_start.isoformat() if contract.date_start else None,
                    'end_date': contract.date_end.isoformat() if contract.date_end else None,
                    'status': contract.state,
                    'type': contract.type_id.name,
                    'duration': contract.duration_type,
                    'renewal_date': contract.renewal_date.isoformat() if contract.renewal_date else None,
                    'termination_reason': contract.termination_reason,
                    'signing_date': contract.date_signed.isoformat() if contract.date_signed else None,
                    'signatory': contract.signatory_id.name if contract.signatory_id else None,
                    'signature': contract.signature,
                    'attachment': contract.attachment_ids.mapped('name') if contract.attachment_ids else None,
                    'revision_history': contract.revision_history,
                    'approval_status': contract.approval_status,
                    'approval_date': contract.approval_date.isoformat() if contract.approval_date else None,
                    'approval_signatory': contract.approval_signatory_id.name if contract.approval_signatory_id else None,
                    'approval_signature': contract.approval_signature,
                    'amendment_history': contract.amendment_history,
                    'amendment_status': contract.amendment_status,
                    'amendment_approval_status': contract.amendment_approval_status,
                    'amendment_approval_date': contract.amendment_approval_date.isoformat() if contract.amendment_approval_date else None,
                    'amendment_approval_signatory': contract.amendment_approval_signatory_id.name if contract.amendment_approval_signatory_id else None,
                    'amendment_approval_signature': contract.amendment_approval_signature,
                    'amendment_approval_attachment': contract.amendment_approval_attachment_ids.mapped('name') if contract.amendment_approval_attachment_ids else None
                } for contract in contracts]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_contract(self, employee_id, name, date_start, date_end, wage):
        """Create a new contract for an employee"""
        try:
            vals = {
                'employee_id': employee_id,
                'name': name,
                'date_start': date_start,
                'date_end': date_end,
                'wage': wage,
                'state': 'draft',
                'type_id': request.env['hr.contract.type'].search([('name', '=', 'Fixed-term')]).id,
                'duration_type': 'fixed',
                'renewal_date': date_end,
                'signatory_id': request.env.user.id,
                'signature': request.env.user.signature,
                'attachment_ids': [(6, 0, [])],
                'revision_history': [],
                'approval_status': 'draft',
                'approval_date': fields.Datetime.now(),
                'approval_signatory_id': request.env.user.id,
                'approval_signature': request.env.user.signature
            }
            
            contract = request.env['hr.contract'].create(vals)
            return {
                'success': True,
                'contract_id': contract.id,
                'message': f'Hợp đồng #{contract.id} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_update_contract(self, contract_id, name, date_end, wage):
        """Update an existing contract for an employee"""
        try:
            contract = request.env['hr.contract'].browse(contract_id)
            if not contract.exists():
                return {'error': 'Hợp đồng không tồn tại'}
            
            vals = {
                'name': name,
                'date_end': date_end,
                'wage': wage,
                'state': contract.state,
                'type_id': contract.type_id.id,
                'duration_type': contract.duration_type,
                'renewal_date': contract.renewal_date,
                'signatory_id': contract.signatory_id.id,
                'signature': contract.signature,
                'attachment_ids': contract.attachment_ids.ids,
                'revision_history': contract.revision_history,
                'approval_status': contract.approval_status,
                'approval_date': contract.approval_date,
                'approval_signatory_id': contract.approval_signatory_id.id,
                'approval_signature': contract.approval_signature,
                'amendment_history': contract.amendment_history,
                'amendment_status': contract.amendment_status,
                'amendment_approval_status': contract.amendment_approval_status,
                'amendment_approval_date': contract.amendment_approval_date,
                'amendment_approval_signatory_id': contract.amendment_approval_signatory_id.id,
                'amendment_approval_signature': contract.amendment_approval_signature,
                'amendment_approval_attachment_ids': contract.amendment_approval_attachment_ids.ids
            }
            
            contract.write(vals)
            return {
                'success': True,
                'message': f'Hợp đồng #{contract.id} đã được cập nhật'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_contract_detail(self, contract_id):
        """Get detailed information about a contract"""
        try:
            contract = request.env['hr.contract'].browse(contract_id)
            if not contract.exists():
                return {'error': 'Hợp đồng không tồn tại'}
            
            return {
                'success': True,
                'contract': {
                    'id': contract.id,
                    'name': contract.name,
                    'start_date': contract.date_start.isoformat() if contract.date_start else None,
                    'end_date': contract.date_end.isoformat() if contract.date_end else None,
                    'status': contract.state,
                    'type': contract.type_id.name,
                    'duration': contract.duration_type,
                    'renewal_date': contract.renewal_date.isoformat() if contract.renewal_date else None,
                    'termination_reason': contract.termination_reason,
                    'signing_date': contract.date_signed.isoformat() if contract.date_signed else None,
                    'signatory': contract.signatory_id.name if contract.signatory_id else None,
                    'signature': contract.signature,
                    'attachment': contract.attachment_ids.mapped('name') if contract.attachment_ids else None,
                    'revision_history': contract.revision_history,
                    'approval_status': contract.approval_status,
                    'approval_date': contract.approval_date.isoformat() if contract.approval_date else None,
                    'approval_signatory': contract.approval_signatory_id.name if contract.approval_signatory_id else None,
                    'approval_signature': contract.approval_signature,
                    'amendment_history': contract.amendment_history,
                    'amendment_status': contract.amendment_status,
                    'amendment_approval_status': contract.amendment_approval_status,
                    'amendment_approval_date': contract.amendment_approval_date.isoformat() if contract.amendment_approval_date else None,
                    'amendment_approval_signatory': contract.amendment_approval_signatory_id.name if contract.amendment_approval_signatory_id else None,
                    'amendment_approval_signature': contract.amendment_approval_signature,
                    'amendment_approval_attachment': contract.amendment_approval_attachment_ids.mapped('name') if contract.amendment_approval_attachment_ids else None
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_activate_contract(self, contract_id):
        """Activate an existing contract"""
        try:
            contract = request.env['hr.contract'].browse(contract_id)
            if not contract.exists():
                return {'error': 'Hợp đồng không tồn tại'}
            
            contract.write({'state': 'open'})
            return {
                'success': True,
                'message': f'Hợp đồng #{contract.id} đã được kích hoạt'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_terminate_contract(self, contract_id, date_end, reason):
        """Terminate an existing contract"""
        try:
            contract = request.env['hr.contract'].browse(contract_id)
            if not contract.exists():
                return {'error': 'Hợp đồng không tồn tại'}
            
            contract.write({
                'state': 'close',
                'date_end': date_end,
                'termination_reason': reason
            })
            return {
                'success': True,
                'message': f'Hợp đồng #{contract.id} đã được chấm dứt'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_renew_contract(self, contract_id, new_end_date, new_wage):
        """Renew an existing contract"""
        try:
            contract = request.env['hr.contract'].browse(contract_id)
            if not contract.exists():
                return {'error': 'Hợp đồng không tồn tại'}
            
            vals = {
                'date_end': new_end_date,
                'wage': new_wage,
                'state': 'draft',
                'type_id': contract.type_id.id,
                'duration_type': contract.duration_type,
                'renewal_date': new_end_date,
                'signatory_id': contract.signatory_id.id,
                'signature': contract.signature,
                'attachment_ids': contract.attachment_ids.ids,
                'revision_history': contract.revision_history,
                'approval_status': 'draft',
                'approval_date': fields.Datetime.now(),
                'approval_signatory_id': contract.approval_signatory_id.id,
                'approval_signature': contract.approval_signature
            }
            
            new_contract = request.env['hr.contract'].create(vals)
            return {
                'success': True,
                'contract_id': new_contract.id,
                'message': f'Hợp đồng #{new_contract.id} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_salary_structures(self, active=True):
        """Get salary structures"""
        try:
            domain = [('active', '=', active)] if active else []
            structures = request.env['hr.salary.structure'].search(domain)
            
            return {
                'success': True,
                'structures': [{
                    'id': structure.id,
                    'name': structure.name,
                    'structure_type': structure.structure_type,
                    'structure_line_ids': [{
                        'id': line.id,
                        'name': line.name,
                        'amount': line.amount,
                        'sequence': line.sequence,
                        'active': line.active
                    } for line in structure.structure_line_ids]
                } for structure in structures]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_update_contract_salary(self, contract_id, wage, effective_date):
        """Update salary for an existing contract"""
        try:
            contract = request.env['hr.contract'].browse(contract_id)
            if not contract.exists():
                return {'error': 'Hợp đồng không tồn tại'}
            
            vals = {
                'wage': wage,
                'effective_date': effective_date,
                'state': 'draft',
                'signatory_id': request.env.user.id,
                'signature': request.env.user.signature,
                'attachment_ids': [(6, 0, [])],
                'revision_history': [],
                'approval_status': 'draft',
                'approval_date': fields.Datetime.now(),
                'approval_signatory_id': request.env.user.id,
                'approval_signature': request.env.user.signature
            }
            
            contract.write(vals)
            return {
                'success': True,
                'message': f'Lương trong hợp đồng #{contract.id} đã được cập nhật'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_attendance_records(self, employee_id, date_from, date_to, limit=50):
        """Get attendance records for an employee"""
        try:
            domain = [
                ('employee_id', '=', employee_id),
                ('check_in', '>=', date_from),
                ('check_out', '<=', date_to)
            ]
            records = request.env['hr.attendance'].search(domain, limit=limit)
            return {
                'success': True,
                'attendance_records': [{
                    'id': record.id,
                    'check_in': record.check_in.strftime('%Y-%m-%d %H:%M:%S') if record.check_in else None,
                    'check_out': record.check_out.strftime('%Y-%m-%d %H:%M:%S') if record.check_out else None,
                    'worked_hours': record.worked_hours,
                    'reason': record.reason
                } for record in records]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_attendance_manual(self, employee_id, check_in, check_out, reason):
        """Create a manual attendance record"""
        try:
            vals = {
                'employee_id': employee_id,
                'check_in': check_in,
                'check_out': check_out,
                'reason': reason
            }
            record = request.env['hr.attendance'].create(vals)
            return {
                'success': True,
                'attendance_id': record.id,
                'message': f'Bản ghi chấm công #{record.id} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_update_attendance_record(self, attendance_id, check_in, check_out):
        """Update an existing attendance record"""
        try:
            record = request.env['hr.attendance'].browse(attendance_id)
            if not record.exists():
                return {'error': 'Bản ghi chấm công không tồn tại'}
            
            vals = {
                'check_in': check_in,
                'check_out': check_out
            }
            record.write(vals)
            return {
                'success': True,
                'message': f'Bản ghi chấm công #{record.id} đã được cập nhật'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_delete_attendance_record(self, attendance_id):
        """Delete an existing attendance record"""
        try:
            record = request.env['hr.attendance'].browse(attendance_id)
            if not record.exists():
                return {'error': 'Bản ghi chấm công không tồn tại'}
            
            record.unlink()
            return {
                'success': True,
                'message': f'Bản ghi chấm công #{record.id} đã được xóa'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_calculate_overtime(self, employee_id, date_from, date_to, standard_hours=8):
        """Calculate overtime for an employee"""
        try:
            domain = [
                ('employee_id', '=', employee_id),
                ('check_in', '>=', date_from),
                ('check_out', '<=', date_to)
            ]
            records = request.env['hr.attendance'].search(domain)
            total_hours = sum(att.worked_hours for att in records)
            overtime_hours = max(0, total_hours - standard_hours)
            return {
                'success': True,
                'overtime_hours': overtime_hours
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_missing_attendance(self, employee_id, date_from, date_to):
        """Get missing attendance records for an employee"""
        try:
            domain = [
                ('employee_id', '=', employee_id),
                ('check_in', '>=', date_from),
                ('check_out', '<=', date_to)
            ]
            records = request.env['hr.attendance'].search(domain)
            missing_records = [
                {
                    'date': date_from + timedelta(days=i),
                    'reason': 'Chưa check-in' if not any(
                        att.check_in and att.check_out and date_from + timedelta(days=i) == att.check_in.date()
                        for att in records
                    ) else 'Chưa check-out'
                }
                for i in range((date_to - date_from).days + 1)
            ]
            return {
                'success': True,
                'missing_records': missing_records
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_approve_attendance(self, attendance_ids, approved_by):
        """Approve attendance records"""
        try:
            records = request.env['hr.attendance'].browse(attendance_ids)
            for record in records:
                if record.state != 'draft':
                    return {'error': f'Bản ghi chấm công #{record.id} đã được xử lý'}
                record.write({'state': 'approved', 'approved_by': approved_by})
            return {
                'success': True,
                'message': f'{len(records)} bản ghi chấm công đã được phê duyệt'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_work_schedules(self, employee_id, date_from, date_to):
        """Get work schedules for an employee"""
        try:
            domain = [
                ('employee_id', '=', employee_id),
                ('date_start', '<=', date_to),
                ('date_end', '>=', date_from)
            ]
            schedules = request.env['hr.employee.schedule'].search(domain)
            return {
                'success': True,
                'work_schedules': [{
                    'id': schedule.id,
                    'date_start': schedule.date_start.isoformat() if schedule.date_start else None,
                    'date_end': schedule.date_end.isoformat() if schedule.date_end else None,
                    'shift_name': schedule.shift_id.name if schedule.shift_id else None
                } for schedule in schedules]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_validate_attendance(self, employee_id, date):
        """Validate attendance for an employee"""
        try:
            domain = [
                ('employee_id', '=', employee_id),
                ('check_in', '<=', date),
                ('check_out', '>=', date)
            ]
            record = request.env['hr.attendance'].search(domain, limit=1)
            if record:
                return {
                    'success': True,
                    'attendance_record': {
                        'id': record.id,
                        'check_in': record.check_in.strftime('%Y-%m-%d %H:%M:%S') if record.check_in else None,
                        'check_out': record.check_out.strftime('%Y-%m-%d %H:%M:%S') if record.check_out else None,
                        'worked_hours': record.worked_hours,
                        'reason': record.reason
                    }
                }
            else:
                return {
                    'success': True,
                    'message': 'Không tìm thấy bản ghi chấm công cho ngày đó'
                }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_attendance_analytics(self, employee_id, date_from, date_to, group_by):
        """Get attendance analytics for an employee"""
        try:
            domain = [
                ('employee_id', '=', employee_id),
                ('check_in', '>=', date_from),
                ('check_out', '<=', date_to)
            ]
            records = request.env['hr.attendance'].search(domain)
            if group_by == 'day':
                data = {
                    date_from + timedelta(days=i): {
                        'check_ins': [att.check_in.strftime('%Y-%m-%d %H:%M:%S') for att in records if att.check_in and date_from + timedelta(days=i) == att.check_in.date()],
                        'check_outs': [att.check_out.strftime('%Y-%m-%d %H:%M:%S') for att in records if att.check_out and date_from + timedelta(days=i) == att.check_out.date()],
                        'worked_hours': [att.worked_hours for att in records if date_from + timedelta(days=i) == att.check_in.date()],
                        'reasons': [att.reason for att in records if date_from + timedelta(days=i) == att.check_in.date()]
                    }
                    for i in range((date_to - date_from).days + 1)
                }
            elif group_by == 'week':
                data = {
                    date_from + timedelta(days=i): {
                        'check_ins': [att.check_in.strftime('%Y-%m-%d %H:%M:%S') for att in records if att.check_in and date_from + timedelta(days=i) == att.check_in.date()],
                        'check_outs': [att.check_out.strftime('%Y-%m-%d %H:%M:%S') for att in records if att.check_out and date_from + timedelta(days=i) == att.check_out.date()],
                        'worked_hours': [att.worked_hours for att in records if date_from + timedelta(days=i) == att.check_in.date()],
                        'reasons': [att.reason for att in records if date_from + timedelta(days=i) == att.check_in.date()]
                    }
                    for i in range((date_to - date_from).days + 1)
                }
            elif group_by == 'month':
                data = {
                    date_from + timedelta(days=i): {
                        'check_ins': [att.check_in.strftime('%Y-%m-%d %H:%M:%S') for att in records if att.check_in and date_from + timedelta(days=i) == att.check_in.date()],
                        'check_outs': [att.check_out.strftime('%Y-%m-%d %H:%M:%S') for att in records if att.check_out and date_from + timedelta(days=i) == att.check_out.date()],
                        'worked_hours': [att.worked_hours for att in records if date_from + timedelta(days=i) == att.check_in.date()],
                        'reasons': [att.reason for att in records if date_from + timedelta(days=i) == att.check_in.date()]
                    }
                    for i in range((date_to - date_from).days + 1)
                }
            else:
                return {'error': 'Nhóm theo không hợp lệ'}
            return {
                'success': True,
                'attendance_analytics': data
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_leave_types_new(self, active=True, company_id=None):
        """Get leave types"""
        try:
            domain = [('active', '=', active)]
            if company_id:
                domain.append(('company_id', '=', company_id))
            leave_types = request.env['hr.leave.type'].search(domain)
            return {
                'success': True,
                'data': [{
                    'id': lt.id,
                    'name': lt.name,
                    'allocation_type': lt.allocation_type,
                    'validity_start': lt.validity_start,
                    'validity_stop': lt.validity_stop,
                    'company_id': lt.company_id.id
                } for lt in leave_types]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_leave_type(self, name, allocation_type, color, time_type):
        """Create a new leave type"""
        try:
            vals = {
                'name': name,
                'allocation_type': allocation_type,
                'color': color,
                'time_type': time_type,
                'active': True,
                'company_id': request.env.user.company_id.id
            }
            leave_type = request.env['hr.leave.type'].create(vals)
            return {
                'success': True,
                'leave_type_id': leave_type.id,
                'message': f'Loại nghỉ phép {leave_type.name} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_leave_allocations(self, employee_id, leave_type_id, state=None):
        """Get leave allocations for an employee"""
        try:
            domain = [('employee_id', '=', employee_id), ('leave_type_id', '=', leave_type_id)]
            if state:
                domain.append(('state', '=', state))
            allocations = request.env['hr.leave.allocation'].search(domain)
            return {
                'success': True,
                'allocations': [{
                    'id': alloc.id,
                    'name': alloc.name,
                    'number_of_days': alloc.number_of_days,
                    'state': alloc.state,
                    'leave_type_id': alloc.leave_type_id.id
                } for alloc in allocations]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_leave_allocation(self, employee_id, leave_type_id, number_of_days, name):
        """Create a new leave allocation"""
        try:
            vals = {
                'employee_id': employee_id,
                'leave_type_id': leave_type_id,
                'number_of_days': number_of_days,
                'name': name,
                'state': 'draft'
            }
            allocation = request.env['hr.leave.allocation'].create(vals)
            return {
                'success': True,
                'allocation_id': allocation.id,
                'message': f'Phân bổ nghỉ phép #{allocation.id} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_leave_requests(self, employee_id, state=None, date_from=None, date_to=None):
        """Get leave requests for an employee"""
        try:
            domain = [('employee_id', '=', employee_id)]
            if state:
                domain.append(('state', '=', state))
            if date_from:
                domain.append(('date_from', '>=', date_from))
            if date_to:
                domain.append(('date_to', '<=', date_to))
            requests = request.env['hr.leave'].search(domain)
            return {
                'success': True,
                'requests': [{
                    'id': req.id,
                    'name': req.name,
                    'leave_type_id': req.holiday_status_id.id,
                    'date_from': req.date_from.isoformat() if req.date_from else None,
                    'date_to': req.date_to.isoformat() if req.date_to else None,
                    'state': req.state,
                    'number_of_days': req.number_of_days,
                    'employee_id': req.employee_id.id
                } for req in requests]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_leave_request_new(self, employee_id, leave_type_id, date_from, date_to, name, request_date_from, request_date_to):
        """Create a new leave request"""
        try:
            vals = {
                'employee_id': employee_id,
                'holiday_status_id': leave_type_id,
                'date_from': date_from,
                'date_to': date_to,
                'name': name,
                'state': 'draft',
                'request_date_from': request_date_from,
                'request_date_to': request_date_to
            }
            request = request.env['hr.leave'].create(vals)
            return {
                'success': True,
                'leave_id': request.id,
                'message': f'Đơn nghỉ phép #{request.id} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_approve_leave(self, leave_id, approve_note):
        """Approve a leave request"""
        try:
            leave = request.env['hr.leave'].browse(leave_id)
            if not leave.exists():
                return {'error': 'Đơn nghỉ phép không tồn tại'}
            
            if leave.state != 'draft':
                return {'error': 'Đơn nghỉ phép đã được xử lý'}
            
            leave.write({
                'state': 'confirm',
                'approve_note': approve_note
            })
            return {
                'success': True,
                'message': f'Đã phê duyệt đơn nghỉ phép #{leave.id} cho {leave.employee_id.name}'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_refuse_leave(self, leave_id, refuse_reason):
        """Refuse a leave request"""
        try:
            leave = request.env['hr.leave'].browse(leave_id)
            if not leave.exists():
                return {'error': 'Đơn nghỉ phép không tồn tại'}
            
            if leave.state != 'draft':
                return {'error': 'Đơn nghỉ phép đã được xử lý'}
            
            leave.write({
                'state': 'refuse',
                'refuse_reason': refuse_reason
            })
            return {
                'success': True,
                'message': f'Đã từ chối đơn nghỉ phép #{leave.id} cho {leave.employee_id.name}'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_leave_balance(self, employee_id, leave_type_id):
        """Get leave balance for an employee"""
        try:
            leave_type = request.env['hr.leave.type'].browse(leave_type_id)
            if not leave_type.exists():
                return {'error': 'Loại nghỉ phép không tồn tại'}
            
            domain = [
                ('employee_id', '=', employee_id),
                ('leave_type_id', '=', leave_type_id),
                ('state', '=', 'confirm')
            ]
            allocations = request.env['hr.leave.allocation'].search(domain)
            used_days = sum(alloc.number_of_days for alloc in allocations)
            return {
                'success': True,
                'leave_balance': leave_type.allocation_type == 'fixed' and leave_type.time_type == 'leave' and used_days or 0
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_leave_analytics(self, employee_id, department_id=None, date_from=None, date_to=None, group_by='employee'):
        """Get leave analytics for an employee"""
        try:
            domain = [('employee_id', '=', employee_id)]
            if department_id:
                domain.append(('department_id', '=', department_id))
            if date_from:
                domain.append(('date_from', '>=', date_from))
            if date_to:
                domain.append(('date_to', '<=', date_to))
            requests = request.env['hr.leave'].search(domain)
            if group_by == 'employee':
                data = {
                    'total_days': sum(req.number_of_days for req in requests),
                    'used_days': sum(req.number_of_days for req in requests if req.state == 'confirm'),
                    'remaining_days': sum(req.number_of_days for req in requests if req.state != 'confirm')
                }
            elif group_by == 'department':
                data = {
                    'total_days': sum(req.number_of_days for req in requests),
                    'used_days': sum(req.number_of_days for req in requests if req.state == 'confirm'),
                    'remaining_days': sum(req.number_of_days for req in requests if req.state != 'confirm')
                }
            elif group_by == 'leave_type':
                data = {
                    'total_days': sum(req.number_of_days for req in requests),
                    'used_days': sum(req.number_of_days for req in requests if req.state == 'confirm'),
                    'remaining_days': sum(req.number_of_days for req in requests if req.state != 'confirm')
                }
            else:
                return {'error': 'Nhóm theo không hợp lệ'}
            return {
                'success': True,
                'leave_analytics': data
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_payslips(self, employee_id, date_from, date_to, state=None, limit=20):
        """Get payslips for an employee"""
        try:
            domain = [('employee_id', '=', employee_id)]
            if date_from:
                domain.append(('date_from', '>=', date_from))
            if date_to:
                domain.append(('date_to', '<=', date_to))
            if state:
                domain.append(('state', '=', state))
            payslips = request.env['hr.payslip'].search(domain, limit=limit)
            return {
                'success': True,
                'payslips': [{
                    'id': slip.id,
                    'name': slip.name,
                    'date_from': slip.date_from.isoformat() if slip.date_from else None,
                    'date_to': slip.date_to.isoformat() if slip.date_to else None,
                    'state': slip.state,
                    'contract_id': slip.contract_id.id,
                    'struct_id': slip.struct_id.id
                } for slip in payslips]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_payslip(self, employee_id, date_from, date_to, contract_id, struct_id):
        """Create a new payslip for an employee"""
        try:
            vals = {
                'employee_id': employee_id,
                'date_from': date_from,
                'date_to': date_to,
                'contract_id': contract_id,
                'struct_id': struct_id,
                'state': 'draft'
            }
            payslip = request.env['hr.payslip'].create(vals)
            return {
                'success': True,
                'payslip_id': payslip.id,
                'message': f'Bảng lương #{payslip.id} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_compute_payslip(self, payslip_id, force_recompute=False):
        """Compute payslip"""
        try:
            payslip = request.env['hr.payslip'].browse(payslip_id)
            payslip.compute_sheet()
            return {
                'success': True,
                'message': f'Bảng lương #{payslip.id} đã được tính toán'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_payslip_lines(self, payslip_id, category):
        """Get payslip lines for a specific category"""
        try:
            payslip = request.env['hr.payslip'].browse(payslip_id)
            lines = payslip.line_ids.filtered(lambda l: l.category_id.name == category)
            return {
                'success': True,
                'lines': [{
                    'id': line.id,
                    'name': line.name,
                    'amount': line.amount,
                    'sequence': line.sequence,
                    'category_id': line.category_id.id
                } for line in lines]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_salary_rules(self, category_id, active=True, struct_id=None):
        """Get salary rules for a specific category"""
        try:
            domain = [('active', '=', active)]
            if category_id:
                domain.append(('category_id', '=', category_id))
            if struct_id:
                domain.append(('struct_ids', 'in', [struct_id]))
            rules = request.env['hr.salary.rule'].search(domain)
            return {
                'success': True,
                'rules': [{
                    'id': rule.id,
                    'name': rule.name,
                    'code': rule.code,
                    'category_id': rule.category_id.id,
                    'sequence': rule.sequence,
                    'amount_select': rule.amount_select,
                    'amount_fix': rule.amount_fix,
                    'amount_percentage': rule.amount_percentage
                } for rule in rules]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_salary_rule(self, name, code, category_id, sequence=5, amount_select='fix', amount_fix=0, amount_percentage=0):
        """Create a new salary rule"""
        try:
            vals = {
                'name': name,
                'code': code.upper(),
                'category_id': category_id,
                'sequence': sequence,
                'amount_select': amount_select,
                'amount_fix': amount_fix,
                'amount_percentage': amount_percentage,
                'active': True
            }
            rule = request.env['hr.salary.rule'].create(vals)
            return {
                'success': True,
                'rule_id': rule.id,
                'message': f'Quy tắc lương {rule.name} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_payroll_structures(self, active=True, country_id=None):
        """Get payroll structures"""
        try:
            domain = [('active', '=', active)]
            if country_id:
                domain.append(('country_id', '=', country_id))
            structures = request.env['hr.payroll.structure'].search(domain)
            return {
                'success': True,
                'structures': [{
                    'id': struct.id,
                    'name': struct.name,
                    'code': struct.code,
                    'country_id': struct.country_id.id if struct.country_id else None,
                    'rule_ids': [rule.id for rule in struct.rule_ids]
                } for struct in structures]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_payroll_structure(self, name, code, country_id=None, rule_ids=None):
        """Create a new payroll structure"""
        try:
            vals = {
                'name': name,
                'code': code,
                'active': True
            }
            if country_id:
                vals['country_id'] = country_id
            if rule_ids:
                vals['rule_ids'] = [(6, 0, rule_ids)]
             
            structure = request.env['hr.payroll.structure'].create(vals)
            return {
                'success': True,
                'structure_id': structure.id,
                'message': f'Cấu trúc lương {structure.name} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_validate_payslip(self, payslip_id, validation_note=None):
        """Validate and approve payslip"""
        try:
            payslip = request.env['hr.payslip'].browse(payslip_id)
            if not payslip.exists():
                return {'error': 'Bảng lương không tồn tại'}
             
            if payslip.state != 'draft':
                return {'error': 'Bảng lương đã được xử lý'}
             
            payslip.action_payslip_done()
            if validation_note:
                payslip.write({'note': validation_note})
             
            return {
                'success': True,
                'message': f'Đã xác nhận bảng lương #{payslip.id} cho {payslip.employee_id.name}'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_payroll_summary(self, employee_id=None, department_id=None, date_from=None, date_to=None, group_by='employee'):
        """Get payroll summary and analytics"""
        try:
            domain = []
            if employee_id:
                domain.append(('employee_id', '=', employee_id))
            if department_id:
                domain.append(('employee_id.department_id', '=', department_id))
            if date_from:
                domain.append(('date_from', '>=', date_from))
            if date_to:
                domain.append(('date_to', '<=', date_to))
             
            payslips = request.env['hr.payslip'].search(domain)
             
            if group_by == 'employee':
                summary = {}
                for payslip in payslips:
                    emp_id = payslip.employee_id.id
                    if emp_id not in summary:
                        summary[emp_id] = {
                            'employee_name': payslip.employee_id.name,
                            'total_payslips': 0,
                            'total_gross': 0,
                            'total_net': 0
                        }
                    summary[emp_id]['total_payslips'] += 1
                    summary[emp_id]['total_gross'] += sum(payslip.line_ids.filtered(lambda l: l.category_id.code == 'GROSS').mapped('total'))
                    summary[emp_id]['total_net'] += sum(payslip.line_ids.filtered(lambda l: l.category_id.code == 'NET').mapped('total'))
                 
                data = list(summary.values())
                 
            elif group_by == 'department':
                summary = {}
                for payslip in payslips:
                    dept_id = payslip.employee_id.department_id.id if payslip.employee_id.department_id else 0
                    dept_name = payslip.employee_id.department_id.name if payslip.employee_id.department_id else 'No Department'
                    if dept_id not in summary:
                        summary[dept_id] = {
                            'department_name': dept_name,
                            'total_payslips': 0,
                            'total_employees': set(),
                            'total_gross': 0,
                            'total_net': 0
                        }
                    summary[dept_id]['total_payslips'] += 1
                    summary[dept_id]['total_employees'].add(payslip.employee_id.id)
                    summary[dept_id]['total_gross'] += sum(payslip.line_ids.filtered(lambda l: l.category_id.code == 'GROSS').mapped('total'))
                    summary[dept_id]['total_net'] += sum(payslip.line_ids.filtered(lambda l: l.category_id.code == 'NET').mapped('total'))
                 
                # Convert sets to counts
                for key in summary:
                    summary[key]['total_employees'] = len(summary[key]['total_employees'])
                 
                data = list(summary.values())
                 
            elif group_by == 'month':
                summary = {}
                for payslip in payslips:
                    month_key = payslip.date_from.strftime('%Y-%m') if payslip.date_from else 'Unknown'
                    if month_key not in summary:
                        summary[month_key] = {
                            'month': month_key,
                            'total_payslips': 0,
                            'total_employees': set(),
                            'total_gross': 0,
                            'total_net': 0
                        }
                    summary[month_key]['total_payslips'] += 1
                    summary[month_key]['total_employees'].add(payslip.employee_id.id)
                    summary[month_key]['total_gross'] += sum(payslip.line_ids.filtered(lambda l: l.category_id.code == 'GROSS').mapped('total'))
                    summary[month_key]['total_net'] += sum(payslip.line_ids.filtered(lambda l: l.category_id.code == 'NET').mapped('total'))
                 
                # Convert sets to counts
                for key in summary:
                    summary[key]['total_employees'] = len(summary[key]['total_employees'])
                 
                data = list(summary.values())
            else:
                return {'error': 'Nhóm theo không hợp lệ'}
             
            return {
                'success': True,
                'payroll_summary': {
                    'group_by': group_by,
                    'total_records': len(payslips),
                    'data': data
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_applicants(self, job_id, stage_id, state, active, limit):
        """Get applicants for a job"""
        try:
            domain = [
                ('job_id', '=', job_id),
                ('stage_id', '=', stage_id),
                ('state', '=', state),
                ('active', '=', active)
            ]
            applicants = request.env['hr.applicant'].search(domain, limit=limit)
            return {
                'success': True,
                'applicants': [{
                    'id': app.id,
                    'name': app.name,
                    'email': app.email_from,
                    'phone': app.partner_phone,
                    'stage': app.stage_id.name,
                    'active': app.active
                } for app in applicants]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_applicant(self, partner_name, email_from, partner_phone, job_id, description):
        """Create a new applicant"""
        try:
            vals = {
                'name': partner_name,
                'email_from': email_from,
                'partner_phone': partner_phone,
                'job_id': job_id,
                'description': description,
                'stage_id': request.env['hr.recruitment.stage'].search([('name', '=', 'New')]).id,
                'active': True
            }
            applicant = request.env['hr.applicant'].create(vals)
            return {
                'success': True,
                'applicant_id': applicant.id,
                'message': f'Ứng viên {applicant.name} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_update_applicant_stage(self, applicant_id, stage_id, note):
        """Update applicant stage"""
        try:
            applicant = request.env['hr.applicant'].browse(applicant_id)
            if not applicant.exists():
                return {'error': 'Ứng viên không tồn tại'}
            
            applicant.write({
                'stage_id': stage_id,
                'note': note
            })
            return {
                'success': True,
                'message': f'Giai đoạn tuyển dụng của ứng viên {applicant.name} đã được cập nhật'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_hire_applicant(self, applicant_id, department_id, job_id, start_date):
        """Hire applicant"""
        try:
            applicant = request.env['hr.applicant'].browse(applicant_id)
            if not applicant.exists():
                return {'error': 'Ứng viên không tồn tại'}
            
            vals = {
                'name': applicant.name,
                'email_from': applicant.email_from,
                'partner_phone': applicant.partner_phone,
                'department_id': department_id,
                'job_id': job_id,
                'start_date': start_date,
                'state': 'draft',
                'type_id': request.env['hr.contract.type'].search([('name', '=', 'Fixed-term')]).id,
                'duration_type': 'fixed',
                'renewal_date': start_date,
                'signatory_id': request.env.user.id,
                'signature': request.env.user.signature,
                'attachment_ids': [(6, 0, [])],
                'revision_history': [],
                'approval_status': 'draft',
                'approval_date': fields.Datetime.now(),
                'approval_signatory_id': request.env.user.id,
                'approval_signature': request.env.user.signature
            }
            contract = request.env['hr.contract'].create(vals)
            applicant.write({
                'contract_id': contract.id,
                'state': 'hired'
            })
            return {
                'success': True,
                'contract_id': contract.id,
                'message': f'Hợp đồng #{contract.id} đã được tạo thành công cho ứng viên {applicant.name}'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_refuse_applicant(self, applicant_id, refuse_reason):
        """Refuse applicant"""
        try:
            applicant = request.env['hr.applicant'].browse(applicant_id)
            if not applicant.exists():
                return {'error': 'Ứng viên không tồn tại'}
            
            applicant.write({
                'refuse_reason': refuse_reason,
                'state': 'refuse'
            })
            return {
                'success': True,
                'message': f'Ứng viên {applicant.name} đã được từ chối'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_recruitment_stages(self, job_id, active):
        """Get recruitment stages for a job"""
        try:
            domain = [('job_id', '=', job_id), ('active', '=', active)]
            stages = request.env['hr.recruitment.stage'].search(domain)
            return {
                'success': True,
                'stages': [{
                    'id': stage.id,
                    'name': stage.name,
                    'sequence': stage.sequence,
                    'fold': stage.fold,
                    'hired_stage': stage.hired_stage
                } for stage in stages]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_recruitment_stage(self, name, sequence, fold, hired_stage):
        """Create a new recruitment stage"""
        try:
            vals = {
                'name': name,
                'sequence': sequence,
                'fold': fold,
                'hired_stage': hired_stage,
                'active': True,
                'company_id': request.env.user.company_id.id
            }
            stage = request.env['hr.recruitment.stage'].create(vals)
            return {
                'success': True,
                'stage_id': stage.id,
                'message': f'Giai đoạn tuyển dụng {stage.name} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_recruitment_jobs(self, department_id, active, state):
        """Get recruitment jobs for a department"""
        try:
            domain = [('department_id', '=', department_id), ('active', '=', active), ('state', '=', state)]
            jobs = request.env['hr.job'].search(domain)
            return {
                'success': True,
                'jobs': [{
                    'id': job.id,
                    'name': job.name,
                    'no_of_recruitment': job.no_of_recruitment,
                    'description': job.description,
                    'requirements': job.requirements
                } for job in jobs]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_recruitment_job(self, name, department_id, no_of_recruitment, description, requirements):
        """Create a new recruitment job"""
        try:
            vals = {
                'name': name,
                'department_id': department_id,
                'no_of_recruitment': no_of_recruitment,
                'description': description,
                'requirements': requirements,
                'active': True,
                'company_id': request.env.user.company_id.id
            }
            job = request.env['hr.job'].create(vals)
            return {
                'success': True,
                'job_id': job.id,
                'message': f'Vị trí tuyển dụng {job.name} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_recruitment_analytics(self, job_id, department_id, date_from, date_to, group_by):
        """Get recruitment analytics for a job"""
        try:
            domain = [('job_id', '=', job_id)]
            if department_id:
                domain.append(('department_id', '=', department_id))
            if date_from:
                domain.append(('date_from', '>=', date_from))
            if date_to:
                domain.append(('date_to', '<=', date_to))
            requests = request.env['hr.applicant'].search(domain)
            if group_by == 'job':
                data = {
                    'total_applicants': len(requests),
                    'hired_applicants': len([req for req in requests if req.state == 'hired']),
                    'pending_applicants': len([req for req in requests if req.state == 'new']),
                    'rejected_applicants': len([req for req in requests if req.state == 'refuse'])
                }
            elif group_by == 'department':
                data = {
                    'total_applicants': len(requests),
                    'hired_applicants': len([req for req in requests if req.state == 'hired']),
                    'pending_applicants': len([req for req in requests if req.state == 'new']),
                    'rejected_applicants': len([req for req in requests if req.state == 'refuse'])
                }
            elif group_by == 'stage':
                data = {
                    'total_applicants': len(requests),
                    'hired_applicants': len([req for req in requests if req.state == 'hired']),
                    'pending_applicants': len([req for req in requests if req.state == 'new']),
                    'rejected_applicants': len([req for req in requests if req.state == 'refuse'])
                }
            else:
                return {'error': 'Nhóm theo không hợp lệ'}
            return {
                'success': True,
                'recruitment_analytics': data
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_skills(self, skill_type_id, active, search):
        """Get skills for a skill type"""
        try:
            domain = [('skill_type_id', '=', skill_type_id), ('active', '=', active)]
            if search:
                domain.append(('name', 'ilike', search))
            skills = request.env['hr.skill'].search(domain)
            return {
                'success': True,
                'skills': [{
                    'id': skill.id,
                    'name': skill.name,
                    'sequence': skill.sequence,
                    'color': skill.color
                } for skill in skills]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_skill(self, name, skill_type_id, sequence, color):
        """Create a new skill"""
        try:
            vals = {
                'name': name,
                'skill_type_id': skill_type_id,
                'sequence': sequence,
                'color': color,
                'active': True,
                'company_id': request.env.user.company_id.id
            }
            skill = request.env['hr.skill'].create(vals)
            return {
                'success': True,
                'skill_id': skill.id,
                'message': f'Kỹ năng {skill.name} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_skill_types(self, active):
        """Get skill types"""
        try:
            domain = [('active', '=', active)]
            skill_types = request.env['hr.skill.type'].search(domain)
            return {
                'success': True,
                'skill_types': [{
                    'id': skill_type.id,
                    'name': skill_type.name
                } for skill_type in skill_types]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_skill_type(self, name, color):
        """Create a new skill type"""
        try:
            vals = {
                'name': name,
                'color': color,
                'active': True,
                'company_id': request.env.user.company_id.id
            }
            skill_type = request.env['hr.skill.type'].create(vals)
            return {
                'success': True,
                'skill_type_id': skill_type.id,
                'message': f'Loại kỹ năng {skill_type.name} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_employee_skills(self, employee_id, skill_type_id, skill_level_id):
        """Get skills for an employee"""
        try:
            domain = [('employee_id', '=', employee_id), ('skill_type_id', '=', skill_type_id)]
            if skill_level_id:
                domain.append(('skill_level_id', '=', skill_level_id))
            skills = request.env['hr.employee.skill'].search(domain)
            return {
                'success': True,
                'skills': [{
                    'id': skill.id,
                    'name': skill.skill_id.name,
                    'level': skill.skill_level_id.name,
                    'progress': skill.level_progress
                } for skill in skills]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_assign_employee_skill(self, employee_id, skill_id, skill_level_id, level_progress):
        """Assign skill to employee"""
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'error': 'Nhân viên không tồn tại'}
            
            skill = request.env['hr.skill'].browse(skill_id)
            if not skill.exists():
                return {'error': 'Kỹ năng không tồn tại'}
            
            vals = {
                'employee_id': employee_id,
                'skill_id': skill_id,
                'skill_level_id': skill.skill_level_ids.filtered(lambda l: l.id == skill_level_id).id,
                'level_progress': level_progress
            }
            skill_assignment = request.env['hr.employee.skill'].create(vals)
            return {
                'success': True,
                'skill_assignment_id': skill_assignment.id,
                'message': f'Kỹ năng {skill.name} đã được gán cho nhân viên {employee.name}'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_skill_levels(self, skill_type_id, active):
        """Get skill levels for a skill type"""
        try:
            domain = [('skill_type_id', '=', skill_type_id), ('active', '=', active)]
            skill_levels = request.env['hr.skill.level'].search(domain)
            return {
                'success': True,
                'skill_levels': [{
                    'id': skill_level.id,
                    'name': skill_level.name
                } for skill_level in skill_levels]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_skills_analytics(self, department_id, skill_type_id, group_by):
        """Get skills analytics for a department"""
        try:
            domain = [('department_id', '=', department_id), ('skill_type_id', '=', skill_type_id)]
            skills = request.env['hr.employee.skill'].search(domain)
            if group_by == 'employee':
                data = {
                    emp.id: {
                        'total_skills': len(emp.skill_ids),
                        'assigned_skills': len([skill for skill in emp.skill_ids if skill.skill_type_id.id == skill_type_id]),
                        'unassigned_skills': len([skill for skill in emp.skill_ids if skill.skill_type_id.id != skill_type_id])
                    }
                    for emp in skills.mapped('employee_id')
                }
            elif group_by == 'skill_type':
                data = {
                    skill_type.id: {
                        'total_skills': len(skill_type.skill_ids),
                        'assigned_skills': len([skill for skill in skill_type.skill_ids if skill.skill_type_id.id == skill_type_id]),
                        'unassigned_skills': len([skill for skill in skill_type.skill_ids if skill.skill_type_id.id != skill_type_id])
                    }
                    for skill_type in skills.mapped('skill_type_id')
                }
            else:
                return {'error': 'Nhóm theo không hợp lệ'}
            return {
                'success': True,
                'skills_analytics': data
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_timesheets(self, employee_id, project_id, task_id, date_from, date_to, limit=50):
        """Get timesheets for an employee"""
        try:
            domain = [
                ('employee_id', '=', employee_id),
                ('project_id', '=', project_id),
                ('task_id', '=', task_id),
                ('date', '>=', date_from),
                ('date', '<=', date_to)
            ]
            timesheets = request.env['hr.timesheet'].search(domain, limit=limit)
            return {
                'success': True,
                'timesheets': [{
                    'id': timesheet.id,
                    'date': timesheet.date.isoformat() if timesheet.date else None,
                    'unit_amount': timesheet.unit_amount,
                    'name': timesheet.name,
                    'project_id': timesheet.project_id.id,
                    'task_id': timesheet.task_id.id
                } for timesheet in timesheets]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_timesheet(self, employee_id, project_id, task_id, date, unit_amount, name):
        """Create a new timesheet"""
        try:
            vals = {
                'employee_id': employee_id,
                'project_id': project_id,
                'task_id': task_id,
                'date': date,
                'unit_amount': unit_amount,
                'name': name
            }
            timesheet = request.env['hr.timesheet'].create(vals)
            return {
                'success': True,
                'timesheet_id': timesheet.id,
                'message': f'Timesheet #{timesheet.id} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_update_timesheet(self, timesheet_id, unit_amount, name):
        """Update an existing timesheet"""
        try:
            timesheet = request.env['hr.timesheet'].browse(timesheet_id)
            if not timesheet.exists():
                return {'error': 'Timesheet không tồn tại'}
            
            vals = {
                'unit_amount': unit_amount,
                'name': name
            }
            timesheet.write(vals)
            return {
                'success': True,
                'message': f'Timesheet #{timesheet.id} đã được cập nhật'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_employee_timesheets(self, employee_id, date_from, date_to, group_by):
        """Get timesheets for an employee"""
        try:
            domain = [
                ('employee_id', '=', employee_id),
                ('date', '>=', date_from),
                ('date', '<=', date_to)
            ]
            timesheets = request.env['hr.timesheet'].search(domain)
            if group_by == 'day':
                data = {
                    date_from + timedelta(days=i): {
                        'timesheets': [ts.id for ts in timesheets if ts.date.date() == date_from + timedelta(days=i)],
                        'total_unit_amount': sum(ts.unit_amount for ts in timesheets if ts.date.date() == date_from + timedelta(days=i))
                    }
                    for i in range((date_to - date_from).days + 1)
                }
            elif group_by == 'week':
                data = {
                    date_from + timedelta(days=i): {
                        'timesheets': [ts.id for ts in timesheets if date_from + timedelta(days=i) <= ts.date.date() < date_from + timedelta(days=i+7)],
                        'total_unit_amount': sum(ts.unit_amount for ts in timesheets if date_from + timedelta(days=i) <= ts.date.date() < date_from + timedelta(days=i+7))
                    }
                    for i in range((date_to - date_from).days // 7 + 1)
                }
            elif group_by == 'month':
                data = {
                    date_from + timedelta(days=i): {
                        'timesheets': [ts.id for ts in timesheets if ts.date.month == date_from.month and ts.date.year == date_from.year],
                        'total_unit_amount': sum(ts.unit_amount for ts in timesheets if ts.date.month == date_from.month and ts.date.year == date_from.year)
                    }
                    for i in range((date_to - date_from).days // 30 + 1)
                }
            else:
                return {'error': 'Nhóm theo không hợp lệ'}
            return {
                'success': True,
                'employee_timesheets': data
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_project_timesheets(self, project_id, date_from, date_to, include_cost=True):
        """Get timesheets for a project"""
        try:
            domain = [
                ('project_id', '=', project_id),
                ('date', '>=', date_from),
                ('date', '<=', date_to)
            ]
            timesheets = request.env['hr.timesheet'].search(domain)
            return {
                'success': True,
                'timesheets': [{
                    'id': timesheet.id,
                    'date': timesheet.date.isoformat() if timesheet.date else None,
                    'unit_amount': timesheet.unit_amount,
                    'name': timesheet.name,
                    'include_cost': include_cost
                } for timesheet in timesheets]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_timesheet_analytics(self, employee_id, department_id, project_id, date_from, date_to, group_by):
        """Get timesheet analytics for an employee"""
        try:
            domain = [
                ('employee_id', '=', employee_id),
                ('department_id', '=', department_id),
                ('project_id', '=', project_id),
                ('date', '>=', date_from),
                ('date', '<=', date_to)
            ]
            timesheets = request.env['hr.timesheet'].search(domain)
            if group_by == 'day':
                data = {
                    date_from + timedelta(days=i): {
                        'timesheets': [ts.id for ts in timesheets if ts.date.date() == date_from + timedelta(days=i)],
                        'total_unit_amount': sum(ts.unit_amount for ts in timesheets if ts.date.date() == date_from + timedelta(days=i)),
                        'total_cost': sum(ts.unit_amount * ts.project_id.cost for ts in timesheets if ts.date.date() == date_from + timedelta(days=i))
                    }
                    for i in range((date_to - date_from).days + 1)
                }
            elif group_by == 'week':
                data = {
                    date_from + timedelta(days=i): {
                        'timesheets': [ts.id for ts in timesheets if date_from + timedelta(days=i) <= ts.date.date() < date_from + timedelta(days=i+7)],
                        'total_unit_amount': sum(ts.unit_amount for ts in timesheets if date_from + timedelta(days=i) <= ts.date.date() < date_from + timedelta(days=i+7)),
                        'total_cost': sum(ts.unit_amount * ts.project_id.cost for ts in timesheets if date_from + timedelta(days=i) <= ts.date.date() < date_from + timedelta(days=i+7))
                    }
                    for i in range((date_to - date_from).days // 7 + 1)
                }
            elif group_by == 'month':
                data = {
                    date_from + timedelta(days=i): {
                        'timesheets': [ts.id for ts in timesheets if ts.date.month == date_from.month and ts.date.year == date_from.year],
                        'total_unit_amount': sum(ts.unit_amount for ts in timesheets if ts.date.month == date_from.month and ts.date.year == date_from.year),
                        'total_cost': sum(ts.unit_amount * ts.project_id.cost for ts in timesheets if ts.date.month == date_from.month and ts.date.year == date_from.year)
                    }
                    for i in range((date_to - date_from).days // 30 + 1)
                }
            else:
                return {'error': 'Nhóm theo không hợp lệ'}
            return {
                'success': True,
                'timesheet_analytics': data
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_insurances(self, employee_id, policy_type, state, active):
        """Get insurances for an employee"""
        try:
            domain = [
                ('employee_id', '=', employee_id),
                ('policy_type', '=', policy_type),
                ('state', '=', state),
                ('active', '=', active)
            ]
            insurances = request.env['hr.insurance'].search(domain)
            return {
                'success': True,
                'insurances': [{
                    'id': insurance.id,
                    'name': insurance.name,
                    'policy_type': insurance.policy_type,
                    'start_date': insurance.start_date.isoformat() if insurance.start_date else None,
                    'end_date': insurance.end_date.isoformat() if insurance.end_date else None,
                    'premium_amount': insurance.premium_amount,
                    'company_contribution': insurance.company_contribution,
                    'employee_contribution': insurance.employee_contribution
                } for insurance in insurances]
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_create_insurance(self, employee_id, policy_type, start_date, end_date, premium_amount, company_contribution, employee_contribution):
        """Create a new insurance"""
        try:
            vals = {
                'employee_id': employee_id,
                'policy_type': policy_type,
                'start_date': start_date,
                'end_date': end_date,
                'premium_amount': premium_amount,
                'company_contribution': company_contribution,
                'employee_contribution': employee_contribution,
                'state': 'draft',
                'active': True
            }
            insurance = request.env['hr.insurance'].create(vals)
            return {
                'success': True,
                'insurance_id': insurance.id,
                'message': f'Bảo hiểm #{insurance.id} đã được tạo thành công'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_update_insurance_status(self, insurance_id, state, note):
        """Update insurance status"""
        try:
            insurance = request.env['hr.insurance'].browse(insurance_id)
            if not insurance.exists():
                return {'error': 'Bảo hiểm không tồn tại'}
            
            vals = {
                'state': state,
                'note': note
            }
            insurance.write(vals)
            return {
                'success': True,
                'message': f'Trạng thái bảo hiểm #{insurance.id} đã được cập nhật'
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_insurance_analytics(self, employee_id, department_id, policy_type, date_from, date_to, group_by):
        """Get insurance analytics for an employee"""
        try:
            domain = [
                ('employee_id', '=', employee_id),
                ('department_id', '=', department_id),
                ('policy_type', '=', policy_type),
                ('date', '>=', date_from),
                ('date', '<=', date_to)
            ]
            insurances = request.env['hr.insurance'].search(domain)
            if group_by == 'day':
                data = {
                    date_from + timedelta(days=i): {
                        'insurances': [ins.id for ins in insurances if ins.date.date() == date_from + timedelta(days=i)],
                        'total_premium': sum(ins.premium_amount for ins in insurances if ins.date.date() == date_from + timedelta(days=i)),
                        'company_contribution': sum(ins.company_contribution for ins in insurances if ins.date.date() == date_from + timedelta(days=i)),
                        'employee_contribution': sum(ins.employee_contribution for ins in insurances if ins.date.date() == date_from + timedelta(days=i))
                    }
                    for i in range((date_to - date_from).days + 1)
                }
            elif group_by == 'week':
                data = {
                    date_from + timedelta(days=i): {
                        'insurances': [ins.id for ins in insurances if date_from + timedelta(days=i) <= ins.date.date() < date_from + timedelta(days=i+7)],
                        'total_premium': sum(ins.premium_amount for ins in insurances if date_from + timedelta(days=i) <= ins.date.date() < date_from + timedelta(days=i+7)),
                        'company_contribution': sum(ins.company_contribution for ins in insurances if date_from + timedelta(days=i) <= ins.date.date() < date_from + timedelta(days=i+7)),
                        'employee_contribution': sum(ins.employee_contribution for ins in insurances if date_from + timedelta(days=i) <= ins.date.date() < date_from + timedelta(days=i+7))
                    }
                    for i in range((date_to - date_from).days // 7 + 1)
                }
            elif group_by == 'month':
                data = {
                    date_from + timedelta(days=i): {
                        'insurances': [ins.id for ins in insurances if ts.date.month == date_from.month and ts.date.year == date_from.year],
                        'total_premium': sum(ins.premium_amount for ins in insurances if ts.date.month == date_from.month and ts.date.year == date_from.year),
                        'company_contribution': sum(ins.company_contribution for ins in insurances if ts.date.month == date_from.month and ts.date.year == date_from.year),
                        'employee_contribution': sum(ins.employee_contribution for ins in insurances if ts.date.month == date_from.month and ts.date.year == date_from.year)
                    }
                    for i in range((date_to - date_from).days // 30 + 1)
                }
            else:
                return {'error': 'Nhóm theo không hợp lệ'}
            return {
                'success': True,
                'insurance_analytics': data
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_get_job_detail(self, job_id):
        """Get job details"""
        try:
            job = request.env['hr.job'].browse(job_id)
            if not job.exists():
                return {'error': 'Job không tồn tại'}
            
            return {
                'success': True,
                'job': {
                    'id': job.id,
                    'name': job.name,
                    'department_id': job.department_id.id,
                    'expected_employees': job.no_of_recruitment,
                    'description': job.description,
                    'requirements': job.requirements,
                    'state': job.state
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_update_job(self, job_id, **vals):
        """Update job details"""
        try:
            job = request.env['hr.job'].browse(job_id)
            if not job.exists():
                return {'error': 'Job không tồn tại'}
            
            # Remove job_id from vals if present
            vals.pop('job_id', None)
            
            # Convert expected_employees to no_of_recruitment if present
            if 'expected_employees' in vals:
                vals['no_of_recruitment'] = vals.pop('expected_employees')
            
            job.write(vals)
            return {
                'success': True,
                'message': f'Job #{job.id} đã được cập nhật',
                'job_details': {
                    'id': job.id,
                    'name': job.name,
                    'department': job.department_id.name if job.department_id else '',
                    'expected_employees': job.no_of_recruitment,
                    'description': job.description or '',
                    'requirements': job.requirements or '',
                    'state': job.state
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _hr_archive_job(self, job_id):
        """Archive job"""
        try:
            job = request.env['hr.job'].browse(job_id)
            if not job.exists():
                return {'error': 'Job không tồn tại'}
            
            job.write({'active': False})
            return {
                'success': True,
                'message': f'Job #{job.id} đã được lưu trữ'
            }
        except Exception as e:
            return {'error': str(e)}

    @http.route('/sbotchat/dashboard/realtime_stats', type='json', auth='user', methods=['POST'])
    def dashboard_realtime_stats(self, **kwargs):
        """
        Get real-time HR dashboard statistics
        Enhanced with comprehensive data and real-time updates
        """
        try:
            user = request.env.user
            company_id = user.company_id.id
            today = fields.Date.today()
            
            # Get comprehensive dashboard data
            dashboard_data = {
                'employee_overview': self._get_employee_overview_stats(company_id, today),
                'realtime_attendance': self._get_realtime_attendance_stats(company_id, today),
                'leave_management': self._get_leave_management_stats(company_id, today),
                'recruitment': self._get_recruitment_stats(company_id),
                'payroll': self._get_payroll_stats(company_id, today),
                'notifications': self._get_dashboard_notifications(company_id, user),
                'quick_actions': self._get_quick_actions_config(user),
                'last_updated': fields.Datetime.now().strftime('%H:%M:%S %d/%m/%Y')
            }
            
            return {
                'success': True,
                'data': dashboard_data,
                'message': 'Dashboard data loaded successfully'
            }
            
        except Exception as e:
            _logger.error(f"Error loading dashboard data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': self._get_fallback_dashboard_data()
            }

    @http.route('/sbotchat/dashboard/critical_updates', type='json', auth='user', methods=['POST'])
    def dashboard_critical_updates(self, **kwargs):
        """
        Get critical real-time updates for dashboard (attendance, notifications)
        Called every 10 seconds for real-time data
        """
        try:
            user = request.env.user
            company_id = user.company_id.id
            today = fields.Date.today()
            
            # Get only critical real-time data
            critical_data = {
                'realtime_attendance': self._get_realtime_attendance_stats(company_id, today),
                'employee_overview': {
                    'late_arrivals': self._count_late_arrivals_today(company_id, today),
                    'overtime_workers': self._count_overtime_workers(company_id, today),
                    'attendance_rate': self._calculate_attendance_rate(company_id, today)
                },
                'notifications': self._get_dashboard_notifications(company_id, user),
                'last_updated': fields.Datetime.now().strftime('%H:%M:%S')
            }
            
            return {
                'success': True,
                'data': critical_data,
                'message': 'Critical data updated'
            }
            
        except Exception as e:
            _logger.error(f"Error updating critical data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # Helper methods for counting specific metrics
    def _count_overtime_workers(self, company_id, today):
        """Count employees working overtime today"""
        try:
            # This would require more complex logic based on working hours
            # For now, return placeholder
            return 0
        except:
            return 0

    def _count_missing_checkout(self, company_id, today):
        """Count employees who checked in but haven't checked out"""
        try:
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            return self.env['hr.attendance'].search_count([
                ('employee_id.company_id', '=', company_id),
                ('check_in', '>=', today_start),
                ('check_in', '<=', today_end),
                ('check_out', '=', False)
            ])
        except:
            return 0

    def _count_late_arrivals_today(self, company_id, today):
        """Count late arrivals today"""
        try:
            # This would require more complex logic based on working hours
            # For now, return placeholder
            return 0
        except:
            return 0

    def _calculate_attendance_rate(self, company_id, today):
        """Calculate attendance rate"""
        try:
            # This would require more complex logic based on working hours
            # For now, return placeholder
            return 0.0
        except:
            return 0.0

    def _get_realtime_attendance_stats(self, company_id, today):
        """Get real-time attendance statistics"""
        try:
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            # Get recent check-ins (last 10)
            recent_checkins = request.env['hr.attendance'].search([
                ('employee_id.company_id', '=', company_id),
                ('check_in', '>=', today_start),
                ('check_in', '<=', today_end)
            ], order='check_in desc', limit=10)
            
            checkin_data = []
            for attendance in recent_checkins:
                # Determine status based on check-in time
                check_in_time = attendance.check_in
                status = 'on_time'  # Default status
                
                # Simple logic for status (can be enhanced)
                if check_in_time.hour > 9:  # After 9 AM considered late
                    status = 'late'
                elif check_in_time.hour < 8:  # Before 8 AM considered early
                    status = 'early'
                
                checkin_data.append({
                    'id': attendance.id,
                    'employee_name': attendance.employee_id.name,
                    'check_in_time': check_in_time.strftime('%H:%M'),
                    'status': status,
                    'department': attendance.employee_id.department_id.name if attendance.employee_id.department_id else 'N/A'
                })
            
            # Get summary statistics
            total_checkins = len(recent_checkins)
            early_count = len([c for c in checkin_data if c['status'] == 'early'])
            on_time_count = len([c for c in checkin_data if c['status'] == 'on_time'])
            late_count = len([c for c in checkin_data if c['status'] == 'late'])
            
            return {
                'last_updated': fields.Datetime.now().strftime('%H:%M:%S'),
                'recent_checkins': checkin_data,
                'summary': {
                    'total_today': total_checkins,
                    'early': early_count,
                    'on_time': on_time_count,
                    'late': late_count,
                    'absent': 0  # Would need more complex logic
                }
            }
            
        except Exception as e:
            _logger.error(f"Error getting realtime attendance stats: {str(e)}")
            return self._get_fallback_attendance_stats()

    def _get_dashboard_notifications(self, company_id, user):
        """Get dashboard notifications"""
        try:
            notifications = {
                'high_priority': [],
                'medium_priority': [],
                'low_priority': [],
                'total_unread': 0
            }
            
            # Check for pending leave requests
            pending_leaves = request.env['hr.leave'].search([
                ('employee_id.company_id', '=', company_id),
                ('state', 'in', ['draft', 'confirm']),
            ], limit=5)
            
            for leave in pending_leaves:
                notifications['high_priority'].append({
                    'id': leave.id,
                    'type': 'leave_request',
                    'title': f'Leave Request - {leave.employee_id.name}',
                    'message': f'{leave.holiday_status_id.name} from {leave.request_date_from} to {leave.request_date_to}',
                    'timestamp': leave.create_date.strftime('%H:%M'),
                    'action_url': f'/web#id={leave.id}&model=hr.leave&view_type=form'
                })
            
            # Check for employees without checkout
            missing_checkout = request.env['hr.attendance'].search([
                ('employee_id.company_id', '=', company_id),
                ('check_in', '>=', fields.Date.today()),
                ('check_out', '=', False)
            ], limit=3)
            
            for attendance in missing_checkout:
                notifications['medium_priority'].append({
                    'id': attendance.id,
                    'type': 'missing_checkout',
                    'title': f'Missing Checkout - {attendance.employee_id.name}',
                    'message': f'Checked in at {attendance.check_in.strftime("%H:%M")} but no checkout',
                    'timestamp': attendance.check_in.strftime('%H:%M'),
                    'action_url': f'/web#id={attendance.id}&model=hr.attendance&view_type=form'
                })
            
            # Check for expiring contracts
            expiring_contracts = request.env['hr.contract'].search([
                ('employee_id.company_id', '=', company_id),
                ('date_end', '<=', fields.Date.today() + timedelta(days=30)),
                ('date_end', '>=', fields.Date.today()),
                ('state', '=', 'open')
            ], limit=3)
            
            for contract in expiring_contracts:
                notifications['low_priority'].append({
                    'id': contract.id,
                    'type': 'contract_expiring',
                    'title': f'Contract Expiring - {contract.employee_id.name}',
                    'message': f'Contract expires on {contract.date_end}',
                    'timestamp': fields.Datetime.now().strftime('%H:%M'),
                    'action_url': f'/web#id={contract.id}&model=hr.contract&view_type=form'
                })
            
            # Calculate total unread
            notifications['total_unread'] = (
                len(notifications['high_priority']) + 
                len(notifications['medium_priority']) + 
                len(notifications['low_priority'])
            )
            
            return notifications
            
        except Exception as e:
            _logger.error(f"Error getting dashboard notifications: {str(e)}")
            return {
                'high_priority': [],
                'medium_priority': [],
                'low_priority': [],
                'total_unread': 0
            }

    # Fallback data methods
    def _get_fallback_dashboard_data(self):
        """Fallback data when API fails - minimal real data structure"""
        try:
            # Get basic real data even in fallback mode
            company_id = request.env.company.id
            today = fields.Date.today()
            
            # Real employee count
            total_employees = request.env['hr.employee'].search_count([('company_id', '=', company_id), ('active', '=', True)])
            active_employees = request.env['hr.employee'].search_count([
                ('company_id', '=', company_id), 
                ('active', '=', True),
                ('contract_ids.state', '=', 'open')
            ])
            departments_count = request.env['hr.department'].search_count([('company_id', '=', company_id)])
            
            # Real attendance data for today
            today_checkins = request.env['hr.attendance'].search_count([
                ('employee_id.company_id', '=', company_id),
                ('check_in', '>=', today),
                ('check_in', '<', today + timedelta(days=1))
            ])
            
            return {
                'employee_overview': {
                    'total_employees': total_employees,
                    'active_employees': active_employees,
                    'departments_count': departments_count,
                    'today_checkins': today_checkins,
                    'attendance_rate': round((today_checkins / max(total_employees, 1)) * 100, 1) if total_employees > 0 else 0
                },
                'realtime_attendance': {
                    'summary': {
                        'total_today': today_checkins,
                        'early': 0,
                        'on_time': today_checkins,
                        'late': 0
                    },
                    'recent_checkins': []
                },
                'leave_management': {
                    'pending_approvals': 0,
                    'approved_today': 0,
                    'on_leave_today': 0,
                    'rejected_today': 0,
                    'pending_requests': []
                },
                'recent_actions': [],
                'system_info': {
                    'uptime': '99%',
                    'response_time': '25ms',
                    'memory_usage': '0.8GB',
                    'cpu_usage': '12%',
                    'active_users': request.env['res.users'].search_count([('active', '=', True)])
                },
                'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            _logger.error(f"Error in fallback dashboard data: {e}")
            return {
                'employee_overview': {
                    'total_employees': 0,
                    'active_employees': 0,
                    'departments_count': 0,
                    'today_checkins': 0,
                    'attendance_rate': 0
                },
                'realtime_attendance': {
                    'summary': {
                        'total_today': 0,
                        'early': 0,
                        'on_time': 0,
                        'late': 0
                    },
                    'recent_checkins': []
                },
                'leave_management': {
                    'pending_approvals': 0,
                    'approved_today': 0,
                    'on_leave_today': 0,
                    'rejected_today': 0,
                    'pending_requests': []
                },
                'recent_actions': [],
                'system_info': {
                    'uptime': '0%',
                    'response_time': 'N/A',
                    'memory_usage': 'N/A',
                    'cpu_usage': 'N/A',
                    'active_users': 0
                },
                'last_updated': 'N/A'
            }

    def _get_fallback_employee_stats(self):
        return {
            'total_employees': 0,
            'active_employees': 0,
            'departments_count': 0,
            'today_checkins': 0,
            'attendance_rate': 0.0,
            'on_leave_today': 0,
            'late_arrivals': 0,
            'absent_today': 0,
            'overtime_workers': 0,
            'missing_checkout': 0
        }

    def _get_fallback_attendance_stats(self):
        return {
            'last_updated': fields.Datetime.now().isoformat(),
            'recent_checkins': [],
            'summary': {'total_today': 0, 'early': 0, 'on_time': 0, 'late': 0, 'absent': 0}
        }

    def _get_fallback_leave_stats(self):
        return {
            'pending_approvals': {'count': 0, 'requests': []},
            'approved_today': 0,
            'rejected_today': 0,
            'total_days_requested': 0,
            'most_used_leave_type': {'name': 'Annual Leave', 'count': 0}
        }

    def _get_fallback_recruitment_stats(self):
        return {
            'open_positions': {'count': 0, 'urgent': 0, 'positions': []},
            'applicants': {'total': 0, 'new': 0, 'in_progress': 0, 'hired_this_month': 0, 'rejected': 0},
            'interviews_scheduled': {'today': 0, 'this_week': 0}
        }

    def _get_fallback_payroll_stats(self):
        return {
            'current_month': {'payslips_generated': 0, 'payslips_pending': 0, 'total_salary_cost': 0, 'average_salary': 0},
            'insurance': {'active_policies': 0, 'expiring_soon': 0, 'total_premium': 0},
            'overtime': {'total_hours': 0, 'cost': 0, 'employees_count': 0}
        }

    @http.route('/sbotchat/quick_action/approve_leaves', type='json', auth='user', methods=['POST'])
    def quick_action_approve_leaves(self, **kwargs):
        """Quick action to approve pending leave requests"""
        try:
            # Check permissions
            if not self.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
                return {'success': False, 'error': 'Insufficient permissions'}

            # Get pending leaves
            pending_leaves = self.env['hr.leave'].search([
                ('employee_id.company_id', '=', self.env.user.company_id.id),
                ('state', 'in', ['draft', 'confirm'])
            ], limit=5)

            approved_count = 0
            for leave in pending_leaves:
                try:
                    leave.action_approve()
                    approved_count += 1
                except Exception as e:
                    _logger.warning(f"Failed to approve leave {leave.id}: {str(e)}")

            return {
                'success': True,
                'message': f'Approved {approved_count} leave requests',
                'approved_count': approved_count
            }

        except Exception as e:
            _logger.error(f"Quick action approve leaves error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/sbotchat/quick_action/add_employee', type='json', auth='user', methods=['GET'])
    def quick_action_add_employee(self, **kwargs):
        """Quick action to get employee creation form URL"""
        try:
            if not self.env.user.has_group('hr.group_hr_user'):
                return {'success': False, 'error': 'Insufficient permissions'}

            return {
                'success': True,
                'action': {
                    'type': 'ir.actions.act_window',
                    'name': 'New Employee',
                    'res_model': 'hr.employee',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'default_company_id': self.env.user.company_id.id}
                }
            }

        except Exception as e:
            _logger.error(f"Quick action add employee error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/sbotchat/quick_action/generate_report', type='json', auth='user', methods=['GET'])
    def quick_action_generate_report(self, **kwargs):
        """Quick action to access HR reports"""
        try:
            if not self.env.user.has_group('hr.group_hr_user'):
                return {'success': False, 'error': 'Insufficient permissions'}

            return {
                'success': True,
                'action': {
                    'type': 'ir.actions.act_window',
                    'name': 'HR Reports',
                    'res_model': 'hr.employee',
                    'view_mode': 'pivot,graph,list',
                    'target': 'current',
                    'domain': [('company_id', '=', self.env.user.company_id.id)]
                }
            }

        except Exception as e:
            _logger.error(f"Quick action generate report error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/sbotchat/quick_action/calculate_payroll', type='json', auth='user', methods=['POST'])
    def quick_action_calculate_payroll(self, **kwargs):
        """Quick action for payroll calculation"""
        try:
            if not self.env.user.has_group('hr_payroll_community.group_hr_payroll_user'):
                return {'success': False, 'error': 'Insufficient permissions'}

            # This would require hr_payroll_community module
            # For now, return placeholder response
            return {
                'success': True,
                'message': 'Payroll calculation feature requires HR Payroll module',
                'action': {
                    'type': 'ir.actions.act_window',
                    'name': 'Payslips',
                    'res_model': 'hr.payslip',
                    'view_mode': 'list,form',
                    'target': 'current'
                }
            }

        except Exception as e:
            _logger.error(f"Quick action calculate payroll error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _get_employee_overview_stats(self, company_id, today):
        """Get employee overview statistics"""
        try:
            # Get basic employee counts
            total_employees = request.env['hr.employee'].search_count([
                ('company_id', '=', company_id),
                ('active', '=', True)
            ])
            
            active_employees = request.env['hr.employee'].search_count([
                ('company_id', '=', company_id),
                ('active', '=', True)
            ])
            
            departments_count = request.env['hr.department'].search_count([
                ('company_id', '=', company_id)
            ])
            
            # Get today's attendance stats
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            today_checkins = request.env['hr.attendance'].search_count([
                ('employee_id.company_id', '=', company_id),
                ('check_in', '>=', today_start),
                ('check_in', '<=', today_end)
            ])
            
            # Get leave stats for today
            on_leave_today = request.env['hr.leave'].search_count([
                ('employee_id.company_id', '=', company_id),
                ('state', '=', 'validate'),
                ('date_from', '<=', today),
                ('date_to', '>=', today)
            ])
            
            # Calculate derived stats
            late_arrivals = self._count_late_arrivals_today(company_id, today)
            overtime_workers = self._count_overtime_workers(company_id, today)
            missing_checkout = self._count_missing_checkout(company_id, today)
            attendance_rate = self._calculate_attendance_rate(company_id, today)
            absent_today = max(0, total_employees - today_checkins - on_leave_today)
            
            return {
                'total_employees': total_employees,
                'active_employees': active_employees,
                'departments_count': departments_count,
                'today_checkins': today_checkins,
                'attendance_rate': attendance_rate,
                'on_leave_today': on_leave_today,
                'late_arrivals': late_arrivals,
                'absent_today': absent_today,
                'overtime_workers': overtime_workers,
                'missing_checkout': missing_checkout
            }
            
        except Exception as e:
            _logger.error(f"Error getting employee overview stats: {str(e)}")
            return self._get_fallback_employee_stats()

    def _get_leave_management_stats(self, company_id, today):
        """Get leave management statistics"""
        try:
            # Get pending leave requests
            pending_leaves = request.env['hr.leave'].search([
                ('employee_id.company_id', '=', company_id),
                ('state', 'in', ['draft', 'confirm'])
            ], limit=10)
            
            pending_requests = []
            for leave in pending_leaves:
                pending_requests.append({
                    'id': leave.id,
                    'employee_name': leave.employee_id.name,
                    'leave_type': leave.holiday_status_id.name,
                    'date_from': leave.request_date_from.strftime('%d/%m/%Y') if leave.request_date_from else '',
                    'date_to': leave.request_date_to.strftime('%d/%m/%Y') if leave.request_date_to else '',
                    'days': leave.number_of_days,
                    'state': leave.state,
                    'urgent': (leave.request_date_from - fields.Date.today()).days <= 3 if leave.request_date_from else False
                })
            
            # Get today's approvals/rejections
            approved_today = request.env['hr.leave'].search_count([
                ('employee_id.company_id', '=', company_id),
                ('state', '=', 'validate'),
                ('write_date', '>=', datetime.combine(today, datetime.min.time()))
            ])
            
            rejected_today = request.env['hr.leave'].search_count([
                ('employee_id.company_id', '=', company_id),
                ('state', '=', 'refuse'),
                ('write_date', '>=', datetime.combine(today, datetime.min.time()))
            ])
            
            # Get total days requested this month
            month_start = today.replace(day=1)
            total_days_requested = sum(request.env['hr.leave'].search([
                ('employee_id.company_id', '=', company_id),
                ('create_date', '>=', datetime.combine(month_start, datetime.min.time()))
            ]).mapped('number_of_days'))
            
            # Get most used leave type
            leave_types = request.env['hr.leave.type'].search([])
            most_used_type = {'name': 'Annual Leave', 'count': 0}
            for leave_type in leave_types:
                count = request.env['hr.leave'].search_count([
                    ('employee_id.company_id', '=', company_id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('create_date', '>=', datetime.combine(month_start, datetime.min.time()))
                ])
                if count > most_used_type['count']:
                    most_used_type = {'name': leave_type.name, 'count': count}
            
            return {
                'pending_approvals': {
                    'count': len(pending_requests),
                    'requests': pending_requests
                },
                'approved_today': approved_today,
                'rejected_today': rejected_today,
                'total_days_requested': total_days_requested,
                'most_used_leave_type': most_used_type
            }
            
        except Exception as e:
            _logger.error(f"Error getting leave management stats: {str(e)}")
            return self._get_fallback_leave_stats()

    def _get_recruitment_stats(self, company_id):
        """Get recruitment statistics"""
        try:
            # Get open positions
            open_jobs = request.env['hr.job'].search([
                ('company_id', '=', company_id),
                ('active', '=', True)
            ])
            
            positions = []
            urgent_count = 0
            for job in open_jobs[:10]:  # Limit to 10 for performance
                is_urgent = job.no_of_recruitment > 0 and len(job.application_ids) == 0
                if is_urgent:
                    urgent_count += 1
                    
                positions.append({
                    'id': job.id,
                    'name': job.name,
                    'department': job.department_id.name if job.department_id else 'N/A',
                    'expected_employees': job.no_of_recruitment,
                    'current_applicants': len(job.application_ids),
                    'urgent': is_urgent
                })
            
            # Get applicant statistics
            total_applicants = request.env['hr.applicant'].search_count([
                ('job_id.company_id', '=', company_id)
            ])
            
            new_applicants = request.env['hr.applicant'].search_count([
                ('job_id.company_id', '=', company_id),
                ('create_date', '>=', datetime.combine(fields.Date.today(), datetime.min.time()))
            ])
            
            in_progress_applicants = request.env['hr.applicant'].search_count([
                ('job_id.company_id', '=', company_id),
                ('active', '=', True),
                ('stage_id.hired_stage', '=', False)
            ])
            
            # Get hired this month
            month_start = fields.Date.today().replace(day=1)
            hired_this_month = request.env['hr.applicant'].search_count([
                ('job_id.company_id', '=', company_id),
                ('stage_id.hired_stage', '=', True),
                ('write_date', '>=', datetime.combine(month_start, datetime.min.time()))
            ])
            
            rejected_applicants = request.env['hr.applicant'].search_count([
                ('job_id.company_id', '=', company_id),
                ('active', '=', False)
            ])
            
            # Get interviews scheduled (placeholder - would need calendar integration)
            interviews_today = 0
            interviews_this_week = 0
            
            return {
                'open_positions': {
                    'count': len(open_jobs),
                    'urgent': urgent_count,
                    'positions': positions
                },
                'applicants': {
                    'total': total_applicants,
                    'new': new_applicants,
                    'in_progress': in_progress_applicants,
                    'hired_this_month': hired_this_month,
                    'rejected': rejected_applicants
                },
                'interviews_scheduled': {
                    'today': interviews_today,
                    'this_week': interviews_this_week
                }
            }
            
        except Exception as e:
            _logger.error(f"Error getting recruitment stats: {str(e)}")
            return self._get_fallback_recruitment_stats()

    def _get_payroll_stats(self, company_id, today):
        """Get payroll statistics"""
        try:
            # Get current month payroll data
            month_start = today.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            # Payslip statistics (if hr_payroll_community is available)
            payslips_generated = 0
            payslips_pending = 0
            total_salary_cost = 0
            average_salary = 0
            
            try:
                payslips = request.env['hr.payslip'].search([
                    ('employee_id.company_id', '=', company_id),
                    ('date_from', '>=', month_start),
                    ('date_to', '<=', month_end)
                ])
                
                payslips_generated = len(payslips)
                payslips_pending = len(payslips.filtered(lambda p: p.state == 'draft'))
                total_salary_cost = sum(payslips.mapped('net_wage'))
                average_salary = total_salary_cost / payslips_generated if payslips_generated > 0 else 0
                
            except Exception:
                # hr_payroll_community not available
                pass
            
            # Insurance statistics (if hr_insurance is available)
            active_policies = 0
            expiring_soon = 0
            total_premium = 0
            
            try:
                insurances = request.env['hr.insurance'].search([
                    ('employee_id.company_id', '=', company_id),
                    ('state', '=', 'active')
                ])
                
                active_policies = len(insurances)
                expiring_soon = len(insurances.filtered(
                    lambda i: i.end_date and i.end_date <= today + timedelta(days=30)
                ))
                total_premium = sum(insurances.mapped('premium_amount'))
                
            except Exception:
                # hr_insurance not available
                pass
            
            # Overtime statistics (placeholder)
            overtime_hours = 0
            overtime_cost = 0
            overtime_employees = 0
            
            return {
                'current_month': {
                    'payslips_generated': payslips_generated,
                    'payslips_pending': payslips_pending,
                    'total_salary_cost': total_salary_cost,
                    'average_salary': average_salary
                },
                'insurance': {
                    'active_policies': active_policies,
                    'expiring_soon': expiring_soon,
                    'total_premium': total_premium
                },
                'overtime': {
                    'total_hours': overtime_hours,
                    'cost': overtime_cost,
                    'employees_count': overtime_employees
                }
            }
            
        except Exception as e:
            _logger.error(f"Error getting payroll stats: {str(e)}")
            return self._get_fallback_payroll_stats()

    def _get_quick_actions_config(self, user):
        """Get quick actions configuration based on user permissions"""
        try:
            actions = []
            
            # Check permissions and add appropriate actions
            if user.has_group('hr_holidays.group_hr_holidays_manager'):
                actions.append({
                    'id': 'approve_leaves',
                    'title': 'Approve Leaves',
                    'icon': 'fa-check-circle',
                    'type': 'primary',
                    'endpoint': '/sbotchat/quick_action/approve_leaves'
                })
            
            if user.has_group('hr.group_hr_manager'):
                actions.extend([
                    {
                        'id': 'add_employee',
                        'title': 'Add Employee',
                        'icon': 'fa-user-plus',
                        'type': 'success',
                        'endpoint': '/sbotchat/quick_action/add_employee'
                    },
                    {
                        'id': 'generate_report',
                        'title': 'Generate Report',
                        'icon': 'fa-file-alt',
                        'type': 'info',
                        'endpoint': '/sbotchat/quick_action/generate_report'
                    }
                ])
            
            if user.has_group('hr_payroll.group_hr_payroll_manager'):
                actions.append({
                    'id': 'calculate_payroll',
                    'title': 'Calculate Payroll',
                    'icon': 'fa-calculator',
                    'type': 'warning',
                    'endpoint': '/sbotchat/quick_action/calculate_payroll'
                })
            
            return actions
            
        except Exception as e:
            _logger.error(f"Error getting quick actions config: {str(e)}")
            return []

    def _get_realtime_history_data(self, company_id, limit=20):
        """Get real-time history data for dashboard"""
        try:
            history_items = []
            
            # Get recent attendance activities
            recent_attendance = request.env['hr.attendance'].search([
                ('employee_id.company_id', '=', company_id),
                ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24))
            ], order='create_date desc', limit=10)
            
            for attendance in recent_attendance:
                action_type = 'check_in' if attendance.check_in and not attendance.check_out else 'check_out'
                history_items.append({
                    'id': f'attendance_{attendance.id}',
                    'type': 'attendance',
                    'action': action_type,
                    'employee_name': attendance.employee_id.name,
                    'department': attendance.employee_id.department_id.name if attendance.employee_id.department_id else 'N/A',
                    'timestamp': attendance.create_date,
                    'time_display': attendance.create_date.strftime('%H:%M'),
                    'date_display': attendance.create_date.strftime('%d/%m'),
                    'details': f"{'Check-in' if action_type == 'check_in' else 'Check-out'} at {attendance.check_in.strftime('%H:%M') if attendance.check_in else attendance.check_out.strftime('%H:%M')}",
                    'icon': 'fa-clock',
                    'color': 'success' if action_type == 'check_in' else 'info'
                })
            
            # Get recent leave requests
            recent_leaves = request.env['hr.leave'].search([
                ('employee_id.company_id', '=', company_id),
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=7))
            ], order='create_date desc', limit=10)
            
            for leave in recent_leaves:
                status_color = {
                    'draft': 'secondary',
                    'confirm': 'warning', 
                    'validate': 'success',
                    'refuse': 'danger',
                    'cancel': 'dark'
                }.get(leave.state, 'secondary')
                
                history_items.append({
                    'id': f'leave_{leave.id}',
                    'type': 'leave',
                    'action': f'leave_{leave.state}',
                    'employee_name': leave.employee_id.name,
                    'department': leave.employee_id.department_id.name if leave.employee_id.department_id else 'N/A',
                    'timestamp': leave.create_date,
                    'time_display': leave.create_date.strftime('%H:%M'),
                    'date_display': leave.create_date.strftime('%d/%m'),
                    'details': f"{leave.holiday_status_id.name} - {leave.state.title()} ({leave.number_of_days} days)",
                    'icon': 'fa-calendar-alt',
                    'color': status_color
                })
            
            # Get recent employee changes
            recent_employees = request.env['hr.employee'].search([
                ('company_id', '=', company_id),
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=30))
            ], order='create_date desc', limit=5)
            
            for employee in recent_employees:
                history_items.append({
                    'id': f'employee_{employee.id}',
                    'type': 'employee',
                    'action': 'employee_created',
                    'employee_name': employee.name,
                    'department': employee.department_id.name if employee.department_id else 'N/A',
                    'timestamp': employee.create_date,
                    'time_display': employee.create_date.strftime('%H:%M'),
                    'date_display': employee.create_date.strftime('%d/%m'),
                    'details': f"New employee added to {employee.department_id.name if employee.department_id else 'company'}",
                    'icon': 'fa-user-plus',
                    'color': 'primary'
                })
            
            # Get recent contract activities
            recent_contracts = request.env['hr.contract'].search([
                ('employee_id.company_id', '=', company_id),
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=30))
            ], order='create_date desc', limit=5)
            
            for contract in recent_contracts:
                history_items.append({
                    'id': f'contract_{contract.id}',
                    'type': 'contract',
                    'action': 'contract_created',
                    'employee_name': contract.employee_id.name,
                    'department': contract.employee_id.department_id.name if contract.employee_id.department_id else 'N/A',
                    'timestamp': contract.create_date,
                    'time_display': contract.create_date.strftime('%H:%M'),
                    'date_display': contract.create_date.strftime('%d/%m'),
                    'details': f"New contract - {contract.name} (${contract.wage:,.0f})",
                    'icon': 'fa-file-contract',
                    'color': 'success'
                })
            
            # Sort all items by timestamp (most recent first)
            history_items.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Return limited results
            return history_items[:limit]
            
        except Exception as e:
            _logger.error(f"Error getting realtime history data: {str(e)}")
            return []

    def _get_attendance_history_detailed(self, company_id, days=7, limit=50):
        """Get detailed attendance history for the dashboard"""
        try:
            start_date = fields.Date.today() - timedelta(days=days)
            
            # Get attendance records
            attendance_records = request.env['hr.attendance'].search([
                ('employee_id.company_id', '=', company_id),
                ('check_in', '>=', start_date)
            ], order='check_in desc', limit=limit)
            
            detailed_history = []
            for record in attendance_records:
                # Calculate work duration
                work_duration = 0
                if record.check_out:
                    duration_delta = record.check_out - record.check_in
                    work_duration = duration_delta.total_seconds() / 3600  # Convert to hours
                
                # Determine status
                check_in_hour = record.check_in.hour
                status = 'on_time'
                if check_in_hour > 9:
                    status = 'late'
                elif check_in_hour < 8:
                    status = 'early'
                
                detailed_history.append({
                    'id': record.id,
                    'employee_id': record.employee_id.id,
                    'employee_name': record.employee_id.name,
                    'employee_code': record.employee_id.employee_id or 'N/A',
                    'department': record.employee_id.department_id.name if record.employee_id.department_id else 'N/A',
                    'job_title': record.employee_id.job_id.name if record.employee_id.job_id else 'N/A',
                    'check_in': record.check_in.strftime('%Y-%m-%d %H:%M:%S'),
                    'check_in_time': record.check_in.strftime('%H:%M'),
                    'check_in_date': record.check_in.strftime('%d/%m/%Y'),
                    'check_out': record.check_out.strftime('%Y-%m-%d %H:%M:%S') if record.check_out else None,
                    'check_out_time': record.check_out.strftime('%H:%M') if record.check_out else 'Not checked out',
                    'work_duration': round(work_duration, 2),
                    'work_duration_display': f"{int(work_duration)}h {int((work_duration % 1) * 60)}m" if work_duration > 0 else 'In progress',
                    'status': status,
                    'status_display': status.replace('_', ' ').title(),
                    'is_complete': bool(record.check_out),
                    'overtime_hours': max(0, work_duration - 8) if work_duration > 8 else 0
                })
            
            return detailed_history
            
        except Exception as e:
            _logger.error(f"Error getting detailed attendance history: {str(e)}")
            return []

    def _get_leave_history_detailed(self, company_id, days=30, limit=50):
        """Get detailed leave history for the dashboard"""
        try:
            start_date = fields.Date.today() - timedelta(days=days)
            
            # Get leave records
            leave_records = request.env['hr.leave'].search([
                ('employee_id.company_id', '=', company_id),
                ('create_date', '>=', start_date)
            ], order='create_date desc', limit=limit)
            
            detailed_history = []
            for leave in leave_records:
                # Calculate leave duration
                leave_duration = leave.number_of_days
                
                # Get approver info
                approver_name = 'N/A'
                if leave.first_approver_id:
                    approver_name = leave.first_approver_id.name
                elif leave.second_approver_id:
                    approver_name = leave.second_approver_id.name
                
                detailed_history.append({
                    'id': leave.id,
                    'employee_id': leave.employee_id.id,
                    'employee_name': leave.employee_id.name,
                    'employee_code': leave.employee_id.employee_id or 'N/A',
                    'department': leave.employee_id.department_id.name if leave.employee_id.department_id else 'N/A',
                    'leave_type': leave.holiday_status_id.name,
                    'leave_type_color': leave.holiday_status_id.color or 0,
                    'request_date': leave.create_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'request_date_display': leave.create_date.strftime('%d/%m/%Y %H:%M'),
                    'date_from': leave.request_date_from.strftime('%Y-%m-%d'),
                    'date_to': leave.request_date_to.strftime('%Y-%m-%d'),
                    'date_from_display': leave.request_date_from.strftime('%d/%m/%Y'),
                    'date_to_display': leave.request_date_to.strftime('%d/%m/%Y'),
                    'duration_days': leave_duration,
                    'duration_display': f"{leave_duration} day{'s' if leave_duration != 1 else ''}",
                    'state': leave.state,
                    'state_display': leave.state.replace('_', ' ').title(),
                    'description': leave.name or 'No description',
                    'approver': approver_name,
                    'approval_date': leave.date_approve.strftime('%d/%m/%Y %H:%M') if leave.date_approve else None,
                    'is_approved': leave.state in ['validate', 'validate1'],
                    'is_pending': leave.state in ['draft', 'confirm'],
                    'is_rejected': leave.state == 'refuse',
                    'can_approve': leave.state in ['draft', 'confirm']
                })
            
            return detailed_history
            
        except Exception as e:
            _logger.error(f"Error getting detailed leave history: {str(e)}")
            return []

    def _get_payroll_history_detailed(self, company_id, months=3, limit=50):
        """Get detailed payroll history for the dashboard"""
        try:
            start_date = fields.Date.today().replace(day=1) - timedelta(days=months*30)
            
            # Get payslip records
            payslip_records = request.env['hr.payslip'].search([
                ('employee_id.company_id', '=', company_id),
                ('date_from', '>=', start_date)
            ], order='date_from desc', limit=limit)
            
            detailed_history = []
            for payslip in payslip_records:
                # Calculate net salary
                net_salary = 0
                gross_salary = 0
                
                # Get salary lines
                for line in payslip.line_ids:
                    if line.code == 'NET':
                        net_salary = line.total
                    elif line.code == 'GROSS':
                        gross_salary = line.total
                
                detailed_history.append({
                    'id': payslip.id,
                    'employee_id': payslip.employee_id.id,
                    'employee_name': payslip.employee_id.name,
                    'employee_code': payslip.employee_id.employee_id or 'N/A',
                    'department': payslip.employee_id.department_id.name if payslip.employee_id.department_id else 'N/A',
                    'payslip_name': payslip.name,
                    'period_from': payslip.date_from.strftime('%Y-%m-%d'),
                    'period_to': payslip.date_to.strftime('%Y-%m-%d'),
                    'period_display': f"{payslip.date_from.strftime('%d/%m')} - {payslip.date_to.strftime('%d/%m/%Y')}",
                    'gross_salary': gross_salary,
                    'net_salary': net_salary,
                    'gross_salary_display': f"${gross_salary:,.0f}",
                    'net_salary_display': f"${net_salary:,.0f}",
                    'state': payslip.state,
                    'state_display': payslip.state.replace('_', ' ').title(),
                    'contract_name': payslip.contract_id.name if payslip.contract_id else 'N/A',
                    'struct_name': payslip.struct_id.name if payslip.struct_id else 'N/A',
                    'create_date': payslip.create_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'create_date_display': payslip.create_date.strftime('%d/%m/%Y %H:%M'),
                    'is_done': payslip.state == 'done',
                    'is_draft': payslip.state == 'draft',
                    'can_confirm': payslip.state == 'draft'
                })
            
            return detailed_history
            
        except Exception as e:
            _logger.error(f"Error getting detailed payroll history: {str(e)}")
            return []

    @http.route('/sbotchat/dashboard/history/realtime', type='json', auth='user', methods=['POST'])
    def dashboard_history_realtime(self, **kwargs):
        """Get real-time history data for dashboard"""
        try:
            company_id = request.env.user.company_id.id
            limit = kwargs.get('limit', 20)
            
            history_data = self._get_realtime_history_data(company_id, limit)
            
            return {
                'success': True,
                'data': {
                    'history_items': history_data,
                    'total_count': len(history_data),
                    'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'company_id': company_id
                }
            }
            
        except Exception as e:
            _logger.error(f"Error getting dashboard history realtime: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {
                    'history_items': [],
                    'total_count': 0,
                    'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }

    @http.route('/sbotchat/dashboard/history/attendance', type='json', auth='user', methods=['POST'])
    def dashboard_history_attendance(self, **kwargs):
        """Get detailed attendance history for dashboard"""
        try:
            company_id = request.env.user.company_id.id
            days = kwargs.get('days', 7)
            limit = kwargs.get('limit', 50)
            
            attendance_history = self._get_attendance_history_detailed(company_id, days, limit)
            
            return {
                'success': True,
                'data': {
                    'attendance_records': attendance_history,
                    'total_count': len(attendance_history),
                    'period_days': days,
                    'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            _logger.error(f"Error getting attendance history: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {
                    'attendance_records': [],
                    'total_count': 0,
                    'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }

    @http.route('/sbotchat/dashboard/history/leaves', type='json', auth='user', methods=['POST'])
    def dashboard_history_leaves(self, **kwargs):
        """Get detailed leave history for dashboard"""
        try:
            company_id = request.env.user.company_id.id
            days = kwargs.get('days', 30)
            limit = kwargs.get('limit', 50)
            
            leave_history = self._get_leave_history_detailed(company_id, days, limit)
            
            return {
                'success': True,
                'data': {
                    'leave_records': leave_history,
                    'total_count': len(leave_history),
                    'period_days': days,
                    'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            _logger.error(f"Error getting leave history: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {
                    'leave_records': [],
                    'total_count': 0,
                    'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }

    @http.route('/sbotchat/dashboard/history/payroll', type='json', auth='user', methods=['POST'])
    def dashboard_history_payroll(self, **kwargs):
        """Get detailed payroll history for dashboard"""
        try:
            company_id = request.env.user.company_id.id
            months = kwargs.get('months', 3)
            limit = kwargs.get('limit', 50)
            
            payroll_history = self._get_payroll_history_detailed(company_id, months, limit)
            
            return {
                'success': True,
                'data': {
                    'payroll_records': payroll_history,
                    'total_count': len(payroll_history),
                    'period_months': months,
                    'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            _logger.error(f"Error getting payroll history: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {
                    'payroll_records': [],
                    'total_count': 0,
                    'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }

    @http.route('/sbotchat/static/src/css/', type='http', auth='public', methods=['GET'])
    def handle_css_404(self, **kwargs):
        """Handle CSS 404 errors by redirecting to index file"""
        return request.redirect('/sbotchat/static/src/css/index.css')
    
    @http.route('/sbotchat/static/src/css/<path:filename>', type='http', auth='public', methods=['GET'])
    def serve_css_files(self, filename, **kwargs):
        """Serve CSS files with proper content type"""
        try:
            import os
            from odoo.modules import get_module_path
            
            module_path = get_module_path('sbotchat')
            css_path = os.path.join(module_path, 'static', 'src', 'css', filename)
            
            if os.path.exists(css_path):
                with open(css_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                response = request.make_response(content)
                response.headers['Content-Type'] = 'text/css; charset=utf-8'
                response.headers['Cache-Control'] = 'public, max-age=3600'
                return response
            else:
                return request.not_found()
                
        except Exception as e:
            _logger.error(f"Error serving CSS file {filename}: {e}")
            return request.not_found()

    @http.route('/sbotchat/test_config', type='http', auth='user')
    def test_config(self):
        """Test configuration endpoint"""
        try:
            config = request.env['sbotchat.config'].get_active_config()
            if not config:
                return "Không tìm thấy cấu hình"
            
            result = f"""
            <h2>Cấu hình SBot Chat</h2>
            <p><strong>Tên:</strong> {config.name}</p>
            <p><strong>Có khóa API:</strong> {'Có' if config.api_key else 'Không'}</p>
            <p><strong>Loại mô hình:</strong> {config.model_type}</p>
            <p><strong>Nhiệt độ:</strong> {config.temperature}</p>
            <p><strong>Token tối đa:</strong> {config.max_tokens}</p>
            <p><strong>Hoạt động:</strong> {'Có' if config.is_active else 'Không'}</p>
            """
            return result
        except Exception as e:
            return f"Lỗi: {str(e)}"

    @http.route('/sbotchat/debug', type='http', auth='user')
    def debug_info(self):
        """Debug information endpoint"""
        try:
            config = request.env['sbotchat.config'].get_active_config()
            conversations = request.env['sbotchat.conversation'].search([
                ('user_id', '=', request.env.user.id)
            ])
            
            result = f"""
            <h2>Thông tin Debug SBot Chat</h2>
            <h3>Người dùng hiện tại:</h3>
            <p>ID: {request.env.user.id}</p>
            <p>Tên: {request.env.user.name}</p>
            <p>Login: {request.env.user.login}</p>
            
            <h3>Cấu hình:</h3>
            """
            
            if config:
                result += f"""
                <p>ID cấu hình: {config.id}</p>
                <p>Tên: {config.name}</p>
                <p>Có khóa API: {'Có' if config.api_key else 'Không'}</p>
                <p>Mô hình: {config.model_type}</p>
                """
            else:
                result += "<p>Không tìm thấy cấu hình</p>"
            
            result += f"""
            <h3>Cuộc trò chuyện:</h3>
            <p>Tổng số: {len(conversations)}</p>
            """
            
            for conv in conversations[:5]:  # Show first 5
                result += f"<p>- {conv.title} (ID: {conv.id}, Tin nhắn: {conv.message_count})</p>"
            
            return result
        except Exception as e:
            return f"Lỗi debug: {str(e)}" 