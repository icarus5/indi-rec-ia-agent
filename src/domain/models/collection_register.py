from pydantic import BaseModel


class CollectionRegister(BaseModel):
    name: str
    surname: str = ''
    code_phone: str = 'PE'
    prefix_phone: str = '+51'
    clientPhoneNumber: str
    description: str
    currency: str
    amount: float
    collection_date: str
    total_quotas: int
    frequency_payment: str
    is_indefinite: bool
    creditor_id: str
