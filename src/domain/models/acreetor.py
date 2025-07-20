from pydantic import BaseModel


class Acreetor(BaseModel):
    identifier: str
    name: str
    email: str = ""
    phone: str = ""
    raw_id: str = ""
    is_enterprise: bool = False
