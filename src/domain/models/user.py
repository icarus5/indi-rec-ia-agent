from enum import Enum
from pydantic import BaseModel

class UserType(Enum):
    ANONYMOUS = "anonymous"
    ACREETOR = "acreetor"
    ENTERPRISE = "enterprise"

class User(BaseModel):
    user_id: str = ""
    name: str = ""
    is_indi_user: bool = False
    is_enterprise: bool = False
    type_user: UserType = UserType.ANONYMOUS
    current_session_id: str = ''

    def get_type(self) -> str:
        if hasattr(self, 'type_user'):
            if isinstance(self.type_user, UserType):
                return self.type_user.value
            if isinstance(self.type_user, str) and self.type_user:
                return self.type_user
        return 'anonymous'