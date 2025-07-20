from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Collection(BaseModel):
    id: str
    client_id: str
    client_cellphone: str
    client_full_name: str
    acreetor_id: str
    acreetor_full_name: str
    acreetor_cellphone: str
    status: str
    description: str
    currency: str
    amount: float
    collection_date: str
    payment_date: Optional[str] = ""
    total_quotas: Optional[int] = 1
    quota_number: Optional[int] = 1
    frequency_payment: str
    active: Optional[bool] = True

    
    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "client_cellphone": self.client_cellphone,
            "client_full_name": self.client_full_name,
            "acreetor_id": self.acreetor_id,
            "acreetor_full_name": self.acreetor_full_name,
            "acreetor_cellphone": self.acreetor_cellphone,
            "status": self.status,
            "description": self.description,
            "currency": self.currency,
            "collection_date": self.collection_date,
            "payment_date": self.payment_date,
            "amount": self.amount,
            "total_quotas": self.total_quotas,
            "quota_number": self.quota_number,
            "frequency_payment": self.frequency_payment,
            "active": self.active
        }
