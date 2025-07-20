import json
from typing import List, Dict
from pydantic import BaseModel, Field
import redis
import os
from datetime import datetime
import logging
from src.domain.models.client import Client
from src.domain.models.collection import Collection

logger = logging.getLogger(__name__)

class MemorySchema(BaseModel):
    """
    Schema for storing conversation messages and associated debts.
    """

    messages: List[Dict] = Field(default_factory=list)
    collections: Dict[str, Collection] = Field(default_factory=dict)
    clients: Dict[str, Client] = Field(default_factory=dict)

    def get_collections_in_text(self):
        collections = self.collections
        template = """
        Id de colección: {id}
        Celular del cliente: {client_cellphone}
        Nombre completo del cliente: {client_full_name}
        Nombre completo del acreedor: {acreetor_full_name}
        Celular del acreedor: {acreetor_cellphone}
        Estado: {status}
        Descripción: {description}
        Moneda: {currency}
        Fecha de cobro: {collection_date}
        Fecha de pago: {payment_date}
        Monto: {amount}
        Frecuencia de cobro: {frequency_payment}
        Numero de cuota: {quota_number}
        Total de cuotas: {total_quotas}
        """
        data_list = [template.format(
            id=value.id,
            client_cellphone=value.client_cellphone,
            client_full_name=value.client_full_name,
            acreetor_full_name=value.acreetor_full_name,
            acreetor_cellphone=value.acreetor_cellphone,
            status=value.status,
            description=value.description,
            currency=value.currency,
            collection_date=value.collection_date,
            payment_date=value.payment_date,
            amount=value.amount,
            frequency_payment=value.frequency_payment,
            quota_number=value.quota_number,
            total_quotas=value.total_quotas
        ) for _, value in collections.items()]
        return "\n".join(data_list)

    def get_clients_in_text(self):
        clients = self.clients
        template = """
        ID del cliente: {id}
        RAW ID: {raw_id}
        Nombre completo: {name} {surname}
        Teléfono: {phone_number}
        Email: {email}
        """
        data_list = [template.format(
            id=value.id,
            raw_id=value.raw_id,
            name=value.name,
            surname=value.surname,
            phone_number=value.phone_number,
            email=value.email
        ) for key, value in clients.items()]
        return "\n".join(data_list)

    @staticmethod
    def from_json(json_data: str) -> "MemorySchema":
        """
        Convert a JSON string to a MemorySchema instance.

        :param json_data: JSON string representing the MemorySchema
        :return: MemorySchema instance
        """
        try:
            data = json.loads(json_data)  # Parse JSON string to a dictionary
            return MemorySchema(**data)  # Use Pydantic's validation to create an instance
        except Exception as e:
            logger.error(f"Error parsing JSON to MemorySchema: {e}")
            return MemorySchema()  # Return an empty schema in case of error
  
class RedisMemory:
    """
    A wrapper class for managing messages in Redis with schema validation.
    Supports connection via Redis URL.
    """

    def __init__(self, user_id: str):
        """
        Initialize Redis connection.

        """
        self.user_id = user_id
        self.redis_client = redis.from_url(os.getenv("REDIS_INDIBOT"), decode_responses=True)
        self.redis_key = f"conversation:{self.user_id}"
        self.stored_conversation = self.load_conversation()
        self.session_buffer_time = int(os.getenv("SESSION_BUFFER_WAIT_TIME"))

    def load_conversation(self):
        data = self.redis_client.get(self.redis_key)

        if not data:
            return MemorySchema(messages=[], collections={}, clients={})
        return MemorySchema.from_json(data)

    def messages(self):
        return self.stored_conversation.messages

    def add_user_message(self, content: str):
        """
        Add a human message to the conversation.

        :param conversation_id: Unique identifier for the conversation
        :param content: Message content
        :param metadata: Optional additional metadata for the message
        :param add_to_front: Whether to add message to the start of the list
        """
        message = {"role": "user", "content": content}

        timestamp = datetime.utcnow().isoformat() + "Z"
        message["timestamp"] = timestamp
        self.stored_conversation.messages.append(message)

    def list_clients(self):
        return self.stored_conversation.clients

    def add_client(self, client: Client):
        logging.info(f"Add client: {client.phone_number}")
        if client:
            logging.info(f"Memory: add client in {self.user_id}")
            clients = self.stored_conversation.clients

            for key, value in clients.items():
                if getattr(value, "id", None) == client.id:
                    logging.info(f"Client delete already exists: {client.phone_number}")               
                    del clients[key]
                    break
                
            clients[client.id] = client
            self.stored_conversation.clients = clients

    def list_collections(self):
        return self.stored_conversation.collections

    def add_collection(self, collection: Collection):
      logging.info(f"Add collection : {collection.id}")
      if collection:
          logging.info(f"Memory: add collection in {self.user_id}")
          collections = self.stored_conversation.collections
          collections[collection.id] = collection
          self.stored_conversation.collections = collections

    def delete_collection(self, collection_id: str):
      logging.info(f"Delete collection: {collection_id}")
      if collection_id:
          collections = self.stored_conversation.collections
          if collection_id in collections:
              del collections[collection_id]
          self.stored_conversation.collections = collections
    
    def add_ai_message(self, content: str):
        """
        Add an AI message to the conversation.

        :param conversation_id: Unique identifier for the conversation
        :param content: Message content
        :param metadata: Optional additional metadata for the message
        :param add_to_front: Whether to add message to the start of the list
        """
        message = {"role": "assistant", "content": content}

        timestamp = datetime.utcnow().isoformat() + "Z"
        message["timestamp"] = timestamp
        self.stored_conversation.messages.append(message)

    def save(self):
        """
        Save a conversation with messages and optional debts.

        :param messages: List of message dictionaries
        :param debts: List of debt dictionaries
        :param collections: List of collection dictionaries
        :param clients: List of client dictionaries
        :param metadata: Additional metadata for the conversation
        """
        # Create schema instance
        conversation = MemorySchema(
            messages=self.stored_conversation.messages or [],
            collections=self.stored_conversation.collections or {}, 
            clients=self.stored_conversation.clients or {}, 
        )

        # Convert to JSON for Redis storage
        conversation_json = conversation.model_dump_json()

        # Save to Redis
        
        logging.info(f"Save in redis: {self.redis_key}")
        logging.info(f"Conversation collections: {conversation.collections.keys()}")
        logging.info(f"Conversation clients: {conversation.clients.keys()}")
        redis_user_key = f"user:{self.user_id}"
        self.redis_client.set(self.redis_key, conversation_json, ex=self.session_buffer_time) 
        self.redis_client.expire(redis_user_key, self.session_buffer_time)        

def get_memory(user_id) -> RedisMemory:
    logging.info("Call redis")
    message_history = RedisMemory(user_id=user_id)
    return message_history
