import uuid
import logging
import requests
from enum import Enum
from src.channels.channel import Channel
from src.domain.models.message import Message
from src.domain.models.user import User, UserType
from typing import Dict, Any, Optional, Tuple, List
from src.domain.services.messages import MessageService
from src.domain.services.aggregator import AggregatorService
from src.utils.ocr.ocr import (
    process_image_ocr,
    process_enterprise_file_ocr,
    process_enterprise_image_ocr,
)


class MessageType(Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    CONTACTS = "CONTACTS"
    AUDIO = "AUDIO"
    FILE = "FILE"

class JelouChannel(Channel):
    def __init__(self, api_key: str, bot_id: str):
        self.api_key = api_key
        self.bot_id = bot_id
        self.base_url = "https://api.jelou.ai/v2"
        self.headers = {"Authorization": f"Basic {api_key}", "Content-Type": "application/json"}
        self.provider = "jelou"
        self.is_enterprise_file = False

    def send_message(self, to: str, message: str) -> Tuple[bool, Dict[str, Any]]:
        """Send a text message via Jelou API."""
        endpoint = f"{self.base_url}/whatsapp/messages"

        payload = {"userId": to, "botId": self.bot_id, "type": "text", "text": message}

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            return True, response.json()
        except Exception as e:
            logging.error(f"Failed to send message: {str(e)}")
            return False, {"error": str(e)}

    def send_template_message(self, to: str, template_name: str, template_parameters: List[str], additional_payload: Dict[str, Any] = {}) -> Tuple[bool, Dict[str, Any]]:
        """Send a template message via Jelou API."""
        endpoint = f"{self.base_url}/whatsapp/{self.bot_id}/hsm"
        logging.info("\n\n Send template")
        if len(template_parameters) > 0:
            payload = {"elementName": template_name, "destinations": to, "type": "text", "parameters": template_parameters, **additional_payload}
            logging.info(f"Payload send: {payload}")
            try:
                response = requests.post(endpoint, headers=self.headers, json=payload)
                response.raise_for_status()
                return True, response.json()
            except Exception as e:
                logging.error(f"Failed to send template message: {str(e)}")
                return False, {"error": str(e)}
        return False, {"error": "No parameters found"}

    def _parse_text_message(self, data: Dict[str, Any]) -> str:
        return data.get("data", {}).get("text")

    def _parse_audio_message(self, data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        incoming_message = data.get("data", {}).get("text")
        mediaUrl = data.get("data", {}).get("mediaUrl", None)
        return incoming_message, mediaUrl

    def _parse_image_message(self, data: Dict[str, Any], user: User) -> Optional[str]:
        data = data.get("data", {})
        if data['type'] == MessageType.IMAGE.value and data['mediaUrl']:
            if user.type_user not in [UserType.ACREETOR, UserType.ENTERPRISE]:
                logging.info(f"Session ID: {user.current_session_id} - Usuario no autorizado para OCR. Se usará el caption como mensaje.")
                response = {
                    "text": "No puedo ayudarte con el procesamiento de este tipo de contenido",
                    "tools": []
                }
                return response['text'], data['mediaUrl']
            elif user.type_user == UserType.ACREETOR:
                logging.info(f"Session ID: {user.current_session_id} - Procesando imagen para OCR: {data['mediaUrl']}")
                ocr_result = process_image_ocr(data['mediaUrl'], data.get("caption", ''), user.current_session_id, str(uuid.uuid4()))
                incoming_mediaUrl = data['mediaUrl']
            elif user.type_user == UserType.ENTERPRISE:
                logging.info(f"Session ID: {user.current_session_id} - Procesando imagen para OCR empresarial: {data['mediaUrl']}")
                ocr_result = process_enterprise_image_ocr(data['mediaUrl'], user.user_id, user.current_session_id, str(uuid.uuid4()))
                incoming_mediaUrl = data['mediaUrl']
                self.is_enterprise_file = True
        return ocr_result, incoming_mediaUrl

    def _parse_contacts_message(self, data: Dict[str, Any]) -> str:
        incoming_messages = []
        for contact in data.get("data", {}).get("contacts", []):
            phone = contact.get("phones", [{}])[0].get("phone", "").replace(" ", "")
            if phone.startswith("+51"):
                phone = f"+51 {phone.replace('+51', '')}"
            incoming_messages.append(f"Aqui esta el contacto con nombre: {contact.get('name')} y numero de celular: {phone}")
        return str(" y ".join(incoming_messages))
    
    def _parse_file_message(self, data: Dict[str, Any], user: User) -> Optional[str]:
        data = data.get("data", {})
        if data["type"] == MessageType.FILE.value and data["mediaUrl"]:
            if user.type_user != UserType.ENTERPRISE:
                logging.info(f"Session ID: {user.current_session_id} - Usuario no autorizado para OCR. Se usará el caption como mensaje.")
                response = {
                    "text": "No puedo ayudarte con el procesamiento de este tipo de contenido",
                    "tools": []
                }
                return response['text'], data['mediaUrl']
            else:
                logging.info(f"Session ID: {user.current_session_id} - Procesando archivo para OCR: {data['mediaUrl']}")
                ocr_result = process_enterprise_file_ocr(data["mediaUrl"], data.get("mimeType", ""), user.user_id)
                ocr_message = ocr_result["message"]
                incoming_mediaUrl = data["mediaUrl"]
                self.is_enterprise_file = True
        return ocr_message, incoming_mediaUrl

    def _message_parser_dispatcher(self, message_type: MessageType, data: Dict[str, Any], user: User) -> Tuple[str, Optional[str]]:
        """Despacha la función de parseo según el tipo de mensaje."""
        dispatch = {
            MessageType.TEXT: lambda d: (self._parse_text_message(d), None),
            MessageType.AUDIO: self._parse_audio_message,
            MessageType.IMAGE: lambda d: self._parse_image_message(d, user),
            MessageType.CONTACTS: lambda d: (self._parse_contacts_message(d), None),
            MessageType.FILE: lambda d: self._parse_file_message(d, user),
        }
        parser = dispatch.get(message_type, lambda d: ("", None))
        return parser(data)

    async def parse_message(self, data: Dict[str, Any], user: User) -> Tuple[Optional[Message], bool, bool]:
        """Parse incoming Jelou message."""
        try:
            sender = data["sender"]
            logging.info(user)
            is_enterprise = user.type_user == UserType.ENTERPRISE
            
            force_anonymous = data.get("forceAnonymous", False)

            if sender == "":
                return None

            message_type = MessageType(data.get("data", {}).get("type", MessageType.TEXT.value))
            incoming_message, message_mediaUrl = self._message_parser_dispatcher(message_type, data, user)
            image = {}

            aggregator = AggregatorService()
            await aggregator.buffer_message(sender, incoming_message, message_type.value, message_mediaUrl)
            aggregated_message = await aggregator.aggregate_if_ready(sender)
            status = aggregated_message["status"]
            logging.info(f"Session ID: {user.current_session_id} - Status message: {status}")
            final_message = aggregated_message["message"]

            if status == "complete":
                logging.info(f"Session ID: {user.current_session_id} - Incoming message: {aggregated_message}")
                aggregated_message["message"] = Message(sender=sender, message=final_message, source=message_type.value, provider=self.provider
                , image=image, force_anonymous=force_anonymous, mediaUrl=message_mediaUrl
                , caption=data.get("data", {}).get("caption", None), listed_messages=aggregated_message["listed_messages"])

            elif status == "interal_failure":
                message_service = MessageService()
                failure_input = aggregated_message["failure_input"]
                rejected_input_message = Message(sender=sender, message=failure_input, source=message_type.value, provider=self.provider
                , image=image, force_anonymous=force_anonymous, mediaUrl=message_mediaUrl
                , caption=data.get("data", {}).get("caption", None), listed_messages=aggregated_message["listed_messages"])
                invoke_id=uuid.uuid4()

                await message_service.save_message(
                    message=rejected_input_message,
                    user_id=user.user_id,
                    invoke_id=invoke_id,
                    user=user,
                    model_data=None,
                    is_outcome=False
                )
                await message_service.save_message(
                    message=final_message,
                    user_id=user.user_id,
                    invoke_id=invoke_id,
                    user=user,
                    model_data=None,
                    is_outcome=True
                )

            return aggregated_message, is_enterprise, self.is_enterprise_file
            
        except Exception as e:
            logging.error(f"Session ID: {user.current_session_id} - Error parsing Jelou message: {str(e)}")
            return None

    def verify_webhook(self, request: Any) -> Tuple[Any, int]:
        """Verify Jelou webhook."""
        return {"status": "success"}, 200
