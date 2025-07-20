from pydantic import BaseModel, field_validator
from typing import Union
from uuid import UUID
from src.domain.models.message import Message
from src.domain.models.user import User

class PayloadAgent(BaseModel):
    invoke_id: Union[str, UUID] = None
    user: User = None
    message: str = ""
    message_object: Message = None
    is_chit_chat: bool = False

    @field_validator('invoke_id', mode='before')
    @classmethod
    def validate_invoke_id(cls, v):
        """
        Valida y convierte invoke_id a string si es UUID.
        """
        if isinstance(v, UUID):
            return str(v)
        return v
