from pydantic import BaseModel


class Enterprise(BaseModel):
    identifier: str
    name: str
    email: str = ""
    phone: str = ""
    raw_id: str = ""
    is_enterprise: bool = True
