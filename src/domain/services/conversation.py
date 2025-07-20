import os
import redis
from src.domain.models.user import User
from src.integrations.indi.provider import IndiProvider
from src.domain.models.conversation import Conversation


class ConversationService:
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv("REDIS_INDIBOT"), decode_responses=True)
        self.indi_provider = IndiProvider()
        self.redis_prefix = "conversation"
        self.session_buffer_time = int(os.getenv("SESSION_BUFFER_WAIT_TIME"))

    def get_or_create_conversation(self, user: User) -> Conversation:
        conversation = self.redis_client.get(f"{self.redis_prefix}:{user.user_id}")
        if conversation:
            return Conversation.model_validate_json(conversation)
        
        if(user.is_indi_user):
            clients_list = self.indi_provider.get_clients_by_user_id(user.user_id)
            collections_list = self.indi_provider.get_collection_by_user_id(user.user_id)
            clients_dict = {client.id: client for client in clients_list}
            collections_dict = {collection.id: collection for collection in collections_list}
            conversation = Conversation(
                messages=[],
                clients=clients_dict,
                collections=collections_dict,
            )
        else:
            conversation = Conversation(
                messages=[],
                clients={},
                collections={},
            )
        
        self.redis_client.set(f"{self.redis_prefix}:{user.user_id}", conversation.model_dump_json(), ex=self.session_buffer_time)
        return conversation
