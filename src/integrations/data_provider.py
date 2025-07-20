from abc import ABC, abstractmethod
from typing import List, Union

from src.domain.models.client import Client
from src.domain.models.acreetor import Acreetor
from src.domain.models.collection import Collection
from src.domain.models.enterprise import Enterprise
from src.domain.models.collection_register import CollectionRegister


class DataProvider(ABC):
    @abstractmethod
    def get_collection_by_user_id(self, user_phone: str) -> List[Collection]:
        """Get creditor collections"""
        pass

    @abstractmethod
    def get_clients_by_user_id(self, cellphone: str) -> List[Client]:
        """Get creditors clients"""
        pass

    @abstractmethod
    def get_account_by_user_id(self, cellphone: str) -> List[Union[Acreetor, Enterprise]]:
        
        """Get creditor or enterprise by cellphone"""
        pass


    @abstractmethod
    def create_client(self, client: Client) -> Client:
        """ Create a client in Indi API"""
        pass

    @abstractmethod
    def create_collection(self, collection_register: CollectionRegister) -> List[Collection]:
        """Create a client in Indi API"""
        pass

    @abstractmethod
    def delete_collection(self, collection_id: str, user_id: str) -> str:
        """Delete a collection in Indi API"""
        pass