from datetime import datetime
from src.utils.logger import logger
from src.domain.models.user import User
from src.domain.models.message import Message
from src.domain.repositories.messages import MessageRepository
from src.utils.date.date_utils import get_date

class MessageService:
    def __init__(self):
        pass

    def serialize_message(self, obj):
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
        if isinstance(obj, (HumanMessage, AIMessage, ToolMessage)):
            return obj.__dict__
        if isinstance(obj, list):
            return [self.serialize_message(item) for item in obj]
        if isinstance(obj, dict):
            return {k: self.serialize_message(v) for k, v in obj.items()}
        return obj

    def ensure_json_serializable(self, data):
        import json
        try:
            json.dumps(data)
            return data
        except TypeError:
            return str(data)

    def build_model_data(self, tools, message):
        return {
            "tools": tools,
            "message": message
        }

    async def save_message(self, message: Message, user_id: str, invoke_id: str, user: User, model_data=None, content_filtered=False, is_outcome=False):
        current_date = get_date().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        msg_type = getattr(message, 'source', None) or 'TEXT'
        msg_message = getattr(message, 'message', None) or (str(message) if is_outcome else "")
        sender = 'ia' if is_outcome else (getattr(message, 'sender', None) or getattr(message, 'user_id', None) or user_id)
        media_url = getattr(message, 'mediaUrl', None) or ''
        caption = getattr(message, 'caption', None) or ''
        listed_messages = getattr(message, 'listed_messages', None) or {}
        type_user = 'ia'
        if hasattr(user, 'is_indi_user') and user.is_indi_user:
            type_user = user.get_type() if hasattr(user, 'get_type') else getattr(user, 'type_user', 'ia')
        elif isinstance(user, dict) and 'type_user' in user:
            type_user = user['type_user']
        if user:
            if hasattr(user, 'get_type'):
                type_user = user.get_type()
            elif isinstance(user, dict) and 'type_user' in user:
                type_user = user['type_user']

        if ((listed_messages is not None) or (listed_messages != {})) and (sender != 'ia'):
            for key,listed_message in listed_messages.items():
                if (listed_message['ocr_success_status'] == False) and (listed_message['type'] == 'IMAGE'):
                    sender = 'ocr' 
                payload = {
                    "type": listed_message['type'],
                    "message": listed_message['message'],
                    "sender": sender,
                    "mediaUrl": listed_message['mediaUrl'],
                    "caption": caption,
                    "type_user": type_user,
                    "user_id": user.user_id,
                    "invokeId": invoke_id,
                    "date": datetime.fromisoformat(key).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                    "modelData": self.ensure_json_serializable(model_data) if model_data else None,
                    "contentFiltered": content_filtered,
                    "ocr_context": listed_message['ocr_context'],
                    "session_id": user.current_session_id
                }
                try:
                    logger.info(f"Session ID: {user.current_session_id} - Invoke ID: {invoke_id} - Saving message: {sender} : {listed_message}")
                    message_repository = MessageRepository()
                    message_repository.create(payload)
                except Exception as e:
                    logger.error(f"Session ID: {user.current_session_id} - Invoke ID: {invoke_id} - Error saving message: {e}")

        else:
            payload = {
                "type": msg_type,
                "message": msg_message,
                "sender": sender,
                "mediaUrl": media_url,
                "caption": caption,
                "type_user": type_user,
                "user_id": user.user_id,
                "invokeId": invoke_id,
                "date": current_date,
                "modelData": self.ensure_json_serializable(model_data) if model_data else None,
                "contentFiltered": content_filtered,
                "session_id": user.current_session_id
            }
            try:
                logger.info(f"Session ID: {user.current_session_id} - Invoke ID: {invoke_id} - Saving message: {sender} : {msg_message}")
                message_repository = MessageRepository()
                message_repository.create(payload)
            except Exception as e:
                logger.error(f"Session ID: {user.current_session_id} - Invoke ID: {invoke_id} - Error saving message: {e}")
