from src.utils.logger import logger
import uuid
from src.channels.jelou import MessageType
from src.domain.models.message import Message
from src.domain.models.user import User, UserType
from src.domain.models.payload import PayloadAgent
from src.ai.main import invoke


class ProcessorService:
    def __init__(self):
        from src.domain.services.messages import MessageService

        self.message_service = MessageService()

    def process_message(
        self, message: Message, user: User, is_chit_chat: bool = False
    ) -> dict:
        """
        Procesa un mensaje recibido y ejecuta el flujo correspondiente según el tipo de mensaje y usuario.
        Separa la lógica de OCR y delega la invocación al agente principal.
        """

        invoke_id = uuid.uuid4()
        payload = PayloadAgent(
            invoke_id=invoke_id,
            user=user,
            message=message.message,
            message_object=message,
            is_chit_chat=is_chit_chat,
        )
        logger.info(
            f"Session ID: {user.current_session_id} - Invoke ID: {invoke_id} - Process Message: {message.message}"
        )
        response = invoke(payload)
        return response
