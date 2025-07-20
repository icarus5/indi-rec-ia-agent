import os
import json
import uuid
import redis
import logging

from src.domain.models.user import User, UserType
from src.integrations.indi.provider import IndiProvider

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        self.redis_client = redis.from_url(
            os.getenv("REDIS_INDIBOT"), decode_responses=True
        )
        self.indi_provider = IndiProvider()
        self.redis_prefix = "user"
        self.session_buffer_time = int(os.getenv("SESSION_BUFFER_WAIT_TIME"))

    def get_or_create_user(self, user_id: str, force_anonymous: bool) -> User:
        user = self.redis_client.get(f"{self.redis_prefix}:{user_id}")
        if user:
            logging.info(
                f"Retrieved user from redis: {json.loads(user).get('user_id','')}"
            )
            return User.model_validate_json(user)

        account = (
            None
            if force_anonymous
            else self.indi_provider.get_account_by_user_id(user_id)
        )
        is_enterprise = account.is_enterprise if account else False
        if is_enterprise:
            type_user = UserType.ENTERPRISE
        elif account:
            type_user = UserType.ACREETOR
        else:
            type_user = UserType.ANONYMOUS
        user = User(
            user_id=user_id,
            name=account.name if account else "Unknown",
            is_indi_user=bool(account),
            is_enterprise=bool(is_enterprise),
            type_user=type_user,
            current_session_id=str(uuid.uuid4()),
        )
        logging.info(f"Setting user in redis: {user_id}")
        self.redis_client.set(
            f"{self.redis_prefix}:{user_id}",
            user.model_dump_json(),
            ex=self.session_buffer_time,
        )
        return user
