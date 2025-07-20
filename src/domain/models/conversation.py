from pydantic import BaseModel
from typing import Dict, List
import logging

from src.domain.models.chat_message import ChatMessage
from src.domain.models.collection import Collection
from src.domain.models.client import Client

logger = logging.getLogger(__name__)

class Conversation(BaseModel):
    messages: List[ChatMessage] = []
    collections: Dict[str, Collection] = {}
    clients: Dict[str, Client] = {}