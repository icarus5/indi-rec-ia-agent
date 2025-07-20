import logging
from typing import Any, Dict, List

from src.ai.memory import RedisMemory
from src.domain.models.collection import Collection
from src.integrations.indi.provider import IndiProvider

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = [
    "id", "clientId", "clientPhoneNumber", "clientFullName", "userId", "userPhoneNumber", "userFullName",
    "paymentStatus", "description", "currency", "amount", "collectionDate",
    "paymentDate", "totalQuotas", "numberQuota", "frequencyPayment", "active"
]


class CollectionValidationError(Exception):
    """Custom exception for client validation errors."""


class CollectionService:

    def __init__(self):
        self.indi_provider = IndiProvider()

    @staticmethod
    def _validate_data(client: Dict[str, Any]) -> List[str]:
        missing = [field for field in REQUIRED_FIELDS if field not in client]
        return missing

    def add_collections(self, data: list) -> any:
        collections = {}
        errors = []
        user_phone_number = ""

        for idx, collection in enumerate(data):
            missing_fields = self._validate_data(collection)
            if missing_fields:
                errors.append({
                    "index": idx,
                    "missing_fields": missing_fields
                })
                continue

            user_phone_number = collection["userPhoneNumber"]
            collection_id = collection["id"]
            collections[collection_id] = {
                "id": collection_id,
                "client_id": collection["clientId"],
                "client_cellphone": collection["clientPhoneNumber"],
                "client_full_name": collection["clientFullName"],
                "acreetor_id": collection["userId"],
                "acreetor_cellphone": collection["userPhoneNumber"],
                "acreetor_full_name": collection["userFullName"],
                "status": collection["paymentStatus"],
                "description": collection["description"],
                "currency": collection["currency"],
                "amount": collection["amount"],
                "collection_date": collection["collectionDate"],
                "payment_date": collection["paymentDate"],
                "total_quotas": collection["totalQuotas"],
                "quota_number": collection["numberQuota"],
                "frequency_payment": collection["frequencyPayment"],
                "active": collection["active"]
            }

        if errors:
            logging.warning(f"Validation errors: {errors}")
            raise CollectionValidationError(errors)

        logging.info(f"Saving collections for session: {user_phone_number}")
        memory = RedisMemory(user_id=user_phone_number)
        if memory.stored_conversation.collections != {}:
            added_collection_ids: list[str] = []
            for collection_data in collections.values():
                collection_obj = Collection(**collection_data)
                logging.debug(f"Adding collection: {collection_obj.to_dict()}")
                if not collection_obj.active:
                    memory.delete_collection(collection_obj.id)
                else:
                    memory.add_collection(collection_obj)
                    added_collection_ids.append(collection_obj.id)

            memory.save()

            logging.info("Collections saved successfully")
            return added_collection_ids