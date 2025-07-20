from pydantic import BaseModel
from typing import Optional
from enum import Enum


class MessageType(Enum):
    """
    Enum para los tipos de mensajes soportados en el sistema de chat.
    """
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    CONTACTS = "CONTACTS"
    AUDIO = "AUDIO"


class Message(BaseModel):
    """
    Representa un mensaje en el sistema de chat.

    Atributos:
        sender (str): Identificador del remitente del mensaje
        message (str): Contenido del mensaje
        source (str): Fuente del mensaje, por defecto 'text'
        image (Optional[dict]): Datos de imagen asociados al mensaje
        name (str): Nombre a mostrar del remitente
        provider (str): Proveedor/servicio que envió el mensaje
        user_id (str): Identificador del usuario
        force_anonymous (bool): Indica si el mensaje debe ser anónimo
        mediaUrl (Optional[str]): URL opcional de un medio asociado
        caption (Optional[str]): Texto/caption asociado al medio
    """
    sender: str
    message: str
    source: str = MessageType.TEXT.value
    image: Optional[dict] = None
    name: str = ""
    provider: str
    user_id: str = ""
    force_anonymous: bool = False
    mediaUrl: Optional[str] = None
    caption: Optional[str] = None
    listed_messages: Optional[dict] = None
