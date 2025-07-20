import logging
from typing import Any, Dict, List

from src.ai.memory import MemorySchema, RedisMemory
from src.domain.models.client import Client
from src.integrations.indi.provider import IndiProvider

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = [
    "userPhoneNumber", "prefixPhone", "phoneNumber", "name", "surname",
    "codePhone", "email", "id", "userId"
]


class ClientValidationError(Exception):
    """Custom exception for client validation errors."""


class ClientService:

    def __init__(self):
        self.indi_provider = IndiProvider()

    @staticmethod
    def _validate_data(client: Dict[str, Any]) -> List[str]:
        missing = [field for field in REQUIRED_FIELDS if field not in client]
        return missing

    def add_clients(self, data: list[dict[str, Any]]) -> any:
        clients = {}
        errors = []
        user_phone_number = ""
        for idx, client in enumerate(data):
            missing_fields = self._validate_data(client)
            if missing_fields:
                errors.append({
                    "index": idx,
                    "missing_fields": missing_fields
                })
                continue

            user_phone_number = client["userPhoneNumber"]
            client_id = f'{client["prefixPhone"]}{client["phoneNumber"]}'
            clients[client_id] = {
                "id": client_id,
                "name": client["name"],
                "surname": client["surname"],
                "code_phone": client["codePhone"],
                "prefix_phone": client["prefixPhone"],
                "phone_number": client["phoneNumber"],
                "email": client["email"],
                "creditor_id": client["userId"],
                "raw_id": client["id"],
            }

        if errors:
            logging.warning(f"Validation errors: {errors}")
            raise ClientValidationError(errors)

        logging.info(f"Saving clients for session: {user_phone_number}")
        memory = RedisMemory(user_id=user_phone_number)
        if memory.stored_conversation.clients != {}:
            for client_data in clients.values():
                client_obj = Client(**client_data)
                logging.debug(f"Adding client: {client_obj.to_dict()}")

                clients_redis = memory.list_clients()
                for key, value in clients_redis.items():
                    if getattr(value, "raw_id", None) == client_obj.raw_id:
                        self.update_client_in_collection(client_obj, memory)
                        break

                memory.add_client(client_obj)

            memory.save()

            logging.info("Clients saved successfully")
            return list(clients.keys())

    def update_client_in_collection(self, client_obj, memory):
        collections_redis = memory.list_collections()
        for collection in collections_redis.values():
            if getattr(collection, "client_id", None) == client_obj.raw_id:
                logging.info(f"Update data client {client_obj.name} in collection")
                collection.client_cellphone = client_obj.full_phone_number()
                collection.client_full_name = client_obj.full_name()
