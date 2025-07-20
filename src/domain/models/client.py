from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Client(BaseModel):
    id: str = ""
    name: str
    surname: Optional[str] = ""
    code_phone: str = "PE"
    prefix_phone: str = "+51"
    phone_number: str
    email: Optional[str] = ""
    creditor_id: str = ""
    raw_id: Optional[str] = ""

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "code_phone": self.code_phone,
            "prefix_phone": self.prefix_phone,
            "phone_number": self.phone_number,
            "email": self.email,
            "creditor_id": self.creditor_id,
            "raw_id": self.raw_id,
        }

    def full_phone_number(self):
        return f"{self.prefix_phone}{self.phone_number}"

    def full_name(self):
        return f"{self.name} {self.surname}".strip()
        