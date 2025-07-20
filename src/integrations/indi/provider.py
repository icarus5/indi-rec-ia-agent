import requests
from pydantic import ValidationError
from typing import List, Optional, Dict, Any, Union


from src.utils.logger import logger
from src.ai.memory import RedisMemory
from src.domain.models.client import Client
from src.domain.models.acreetor import Acreetor
from src.config.auth_config import AuthEnvConfig
from src.domain.models.enterprise import Enterprise
from src.domain.models.collection import Collection
from src.integrations.data_provider import DataProvider
from src.config.collection_config import CollectionEnvConfig
from src.domain.models.collection_register import CollectionRegister
from src.utils.requests.formater import build_dynamic_url


class IndiProvider(DataProvider):
    COLLECTION_BY_USER_PHONE_PATH = "agent/collection-requests"
    COLLECTION_CREATE_PATH = "agent/collection-requests/individual"
    COLLECTION_DELETE_PATH = "agent/collection-requests/:id"
    CLIENT_LIST_BY_USER_PATH = "agent/clients"
    CLIENT_CREATE_PATH = "agent/clients"
    USER_BY_PHONE_PATH = "agent/user/find-phone-number"

    def _build_headers(self, data_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if data_headers:
            for key, value in data_headers.items():
                headers[key] = value
        return headers

    def _handle_response(self, response: requests.Response, error_msg: str) -> Any:
        if response.status_code not in (200, 204):
            logger.error(f"{error_msg}: {response.text}")
            raise Exception(f"{error_msg}: {response.text}")
        if response.status_code == 204:
            return None
        return response.json()

    def _to_collection(self, data) -> List[Collection]:
        collections = []
        for item in data:
            collections.append(Collection(
                id=item.get("id"),
                client_id=item.get("clientId"),
                client_cellphone=item.get("clientPhoneNumber"),
                client_full_name=item.get("clientFullName"),
                acreetor_id=item.get("userId"),
                acreetor_cellphone=item.get("userPhoneNumber"),
                acreetor_full_name=item.get("userFullName"),
                status=item.get("paymentStatus"),
                description=item.get("description"),
                currency=item.get("currency"),
                collection_date=item.get("collectionDate"),
                amount=item.get("amount"),
                payment_date=item.get("paymentDate"),
                frequency_payment=item.get("frequencyPayment"),
                quota_number=item.get("numberQuota"),
                total_quotas=item.get("totalQuotas"),
                active=item.get("active")
            ))
        return collections

    def get_collection_by_user_id(self, user_phone: str) -> List[Collection]:
        """Fetch collections by user phone from the external API."""
        api_url = build_dynamic_url(
            CollectionEnvConfig.COLLECTIONS_API_URL,
            self.COLLECTION_BY_USER_PHONE_PATH,
            None,
            {"code": CollectionEnvConfig.COLLECTIONS_API_CODE}
        )
        logger.info("Fetching collections by user from Indi API: %s", api_url)
        logger.debug("Data fetch user phone: %s", user_phone)
        response = requests.get(api_url, headers=self._build_headers({"X-User-Phone": user_phone}))
        data = self._handle_response(response, "Error fetching collections from Indi API") or []

        collections = self._to_collection(data)
        return collections

    def get_clients_by_user_id(self, user_phone: str) -> List[Client]:
        """Fetch clients by user phone from the external API."""
        api_url = build_dynamic_url(
            CollectionEnvConfig.COLLECTIONS_API_URL,
            self.CLIENT_LIST_BY_USER_PATH,
            None,
            {"code": CollectionEnvConfig.COLLECTIONS_API_CODE}
        )
        logger.info("Fetching clients by user from Indi API: %s", api_url)
        logger.debug("Data fetch user phone: %s", user_phone)
        response = requests.get(api_url, headers=self._build_headers({"X-User-Phone": user_phone}))
        data = self._handle_response(response, "Error fetching clients from Indi API") or []

        clients = []
        for item in data:
            clients.append(Client(
                id=(item.get("prefixPhone") or "") + (item.get("phoneNumber") or ""),
                name=item.get("name"),
                surname=item.get("surname"),
                code_phone=item.get("codePhone"),
                prefix_phone=item.get("prefixPhone"),
                phone_number=item.get("phoneNumber"),
                email=item.get("email") if item.get("email") is not None else None,
                creditor_id=item.get("userId"),
                raw_id=item.get("id")
            ))
        return clients

    def get_account_by_user_id(self, user_phone: str) -> Optional[Union[Acreetor, Enterprise]]:
        """
        Fetch creditor or enterprise by phone number from the external API.

        Args:
            user_phone (str): The phone number of the user to query (e.g., '+51987654321').

        Returns:
            Optional[Union[Acreetor, Enterprise]]: The creditor or enterprise object, or None if not found.

        Raises:
            ValueError: If the user_phone is invalid or empty.
        """
        if not user_phone or not isinstance(user_phone, str):
            logger.error("Invalid or empty user_phone provided")
            raise ValueError("user_phone must be a non-empty string")

        try:
            api_url = build_dynamic_url(
                AuthEnvConfig.AUTH_API_URL,
                self.USER_BY_PHONE_PATH,
                None,
                {"code": AuthEnvConfig.AUTH_API_CODE}
            )
        except Exception as e:
            logger.error(f"Failed to build API URL: {str(e)}")
            raise ValueError(f"Failed to build API URL: {str(e)}")

        logger.info(f"Fetching creditor/enterprise from Indi API: {api_url}")
        logger.debug(f"Querying user phone: {user_phone}")

        try:
            response = requests.get(
                api_url,
                headers=self._build_headers({"X-User-Phone": user_phone}),
                timeout=10
            )
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None

        try:
            data = self._handle_response(response, "Error fetching creditor from Indi API")
            if data is None:
                logger.info(f"[get_account_by_user_id] User not found for phone: {user_phone}")
                return None
        except ValueError as e:
            logger.info(f"[get_account_by_user_id] User not found in Indi API: {str(e)}")
            return None

        try:
            is_enterprise = data.get("isEnterprise", False)
            
            required_fields = ["id", "phoneNumber"]
            missing_fields = [field for field in required_fields if field not in data or data[field] is None]
            if missing_fields:
                logger.error(f"Missing required fields in API response: {missing_fields}")
                raise ValueError(f"Missing required fields: {missing_fields}")

            common_data = {
                "identifier": data["id"],
                "name": f"{data.get('names', '')} {data.get('surnames', '')}".strip() or "Unknown",
                "email": data.get("email"),
                "phone": data["phoneNumber"],
                "raw_id": data.get("recordId"),
                "is_enterprise": data.get("isEnterprise", False)
            }

            model = Enterprise if is_enterprise else Acreetor
            instance = model(**common_data)
            logger.debug(f"Created {'Enterprise' if is_enterprise else 'Acreetor'} instance: {instance}")
            return instance

        except (KeyError, ValidationError) as e:
            logger.error(f"Failed to process API response data: {str(e)}")
            return None
        
    def create_client(self, client: Client) -> Client:
        """Create a client in Indi API."""
        data_client = {
            "name": client.name,
            "codePhone": client.code_phone,
            "prefixPhone": client.prefix_phone,
            "phoneNumber": client.phone_number,
            "email": client.email
        }
        if client.surname:
            data_client["surname"] = client.surname

        api_url = build_dynamic_url(
            CollectionEnvConfig.COLLECTIONS_API_URL,
            self.CLIENT_CREATE_PATH,
            None,
            {"code": CollectionEnvConfig.COLLECTIONS_API_CODE}
        )

        logger.info("Creating client from Indi API: %s, with name: %s", api_url, data_client.get("name"))
        logger.debug("Data to create: %s", data_client)

        response = requests.post(api_url, json=data_client,
                                 headers=self._build_headers({"X-User-Phone": client.creditor_id}))
        result = self._handle_response(response, "Error creating debtor in Indi API")
        client.raw_id = result.get("id")
        logger.info(f"Created debtor in Indi: {result}")
        return client

    def create_collection(self, collection_register: CollectionRegister) -> List[Collection]:
        """Create a collection in Indi API."""
        if collection_register.is_indefinite:
            collection_register.total_quotas = -1
        if not collection_register.clientPhoneNumber.startswith('+51'):
            collection_register.clientPhoneNumber = '+51' + collection_register.clientPhoneNumber
            
        data_collection = {
            "client": {
                "name": collection_register.name,
                "surname": collection_register.surname,
                "code_phone": collection_register.code_phone,
                "prefix_phone": collection_register.prefix_phone,
                "clientPhoneNumber": collection_register.clientPhoneNumber,
            },
            "description": collection_register.description,
            "currency": collection_register.currency,
            "amount": collection_register.amount,
            "collectionDate": collection_register.collection_date,
            "totalQuotas": collection_register.total_quotas,
            "frequencyPayment": collection_register.frequency_payment
        }

        api_url = build_dynamic_url(
            CollectionEnvConfig.COLLECTIONS_API_URL,
            self.COLLECTION_CREATE_PATH,
            None,
            {"code": CollectionEnvConfig.COLLECTIONS_API_CODE}
        )

        logger.info("Creating collection from Indi API: %s, with description: %s", api_url,
                    data_collection.get("description"))
        logger.debug("Data to create: %s", data_collection)

        response = requests.post(api_url, json=data_collection,
                                 headers=self._build_headers({"X-User-Phone": collection_register.creditor_id}))
        result = self._handle_response(response, "Error creating collection in Indi API") or []
        collections = []
        clients = []
        for item in result:
            client = item.get("client")
            acreetor = item.get("user")
            collections.append(Collection(
                id=item.get("id"),
                client_id=client.get("id"),
                client_cellphone=client.get("phoneNumber"),
                client_full_name=client.get("fullName"),
                acreetor_id=acreetor.get("id"),
                acreetor_full_name=acreetor.get("fullName"),
                acreetor_cellphone=acreetor.get("phoneNumber"),
                status=item.get("paymentStatus"),
                description=item.get("description"),
                currency=item.get("currency"),
                amount=item.get("amount"),
                collection_date=item.get("collectionDate"),
                payment_date=None,
                frequency_payment=item.get("frequencyPayment"),
                quota_number=item.get("numberQuota"),
                total_quotas=item.get("totalQuotas"),
                active=item.get("active", True)
            ))
            clients.append(Client(
                id=f'{client.get("prefixPhone")}{client.get("phoneNumber")}',
                name=client.get("name"),
                surname=client.get("surname",''),
                code_phone=client.get("codePhone",'PE'),
                prefix_phone=client.get("prefixPhone",'+51'),
                phone_number=client.get("phoneNumber"),
                email=client.get("email",''),
                creditor_id=collection_register.creditor_id,
            ))
        logger.debug(f"Created collections in Indi: {result}")
        return clients, collections

    def delete_collection(self, collection_id: str, user_id: str) -> str:
        """Delete a collection in Indi API."""
        api_url = build_dynamic_url(
            CollectionEnvConfig.COLLECTIONS_API_URL,
            self.COLLECTION_DELETE_PATH,
            {"id": collection_id},
            {"code": CollectionEnvConfig.COLLECTIONS_API_CODE}
        )
        logger.info("Deleting collection from Indi API: %s", api_url)
        response = requests.delete(api_url, headers=self._build_headers({"X-User-Phone": user_id}))
        self._handle_response(response, "Error deleting collection in Indi API")
        return "Collection deleted successfully"
    
    def get_clients_by_phone_number(self, phone_number: str,  memory: RedisMemory) -> str:
        """Get clients by user phone from Redis memory"""

        if phone_number.startswith('+51') and len(phone_number) == 12:
            pass
        elif len(phone_number) != 9:
            logger.info(f'El numero {phone_number} tiene {len(phone_number)} digitos, lo cual no esta permitido')
            return f'El numero {phone_number} tiene {len(phone_number)} digitos, lo cual no esta permitido'
        else:
            phone_number = '+51' + phone_number

        logger.info(f"Getting clients by user phone: {phone_number}")
        clients = memory.stored_conversation.clients.get(phone_number)
        
        logger.info(clients)
        if clients:
            logger.info(f'El numero {phone_number} ya se encuentra registrado a nombre de {clients.name}')
            return f'El numero {phone_number} ya se encuentra registrado a nombre de {clients.name}'
        else:
            logger.info(f'El cliente con el numero {phone_number} no existe, seguir con la intencion actual si se cumplen los requisitos')
            return f'El cliente con el numero {phone_number} no existe, seguir con la intencion actual si se cumplen los requisitos'
        
    def get_clients_by_name(self, name: str,  memory: RedisMemory) -> str:
        """Get clients by name from Redis memory"""

        logger.info(f"Getting clients by user name: {name}")
        name = name.lower()
        first_char = name[0]
        matched_clients = []
        for client_id, data in memory.stored_conversation.clients.items():
            data_name = data.name.lower()
            data_surname = data.surname.lower()
            if (data_name.startswith(first_char)) or (data_surname.startswith(first_char)) or (data_name==name) or (data_surname==name):
                matched_clients.append(data)
        logger.info(matched_clients)
        if matched_clients:
            logger.info(f'Se encontraron {len(matched_clients)} coincidencias de clientes con el nombre {name} o similares: {matched_clients}')
            return f'Se encontraron {len(matched_clients)} coincidencias de clientes con el nombre {name} o similares: {matched_clients}'
        else:
            logger.info(f'No existe ningun cliente con el nombre {name}')
            return f'No existe ningun cliente con el nombre {name}'
        
    def get_all_clients_from_user(self, memory: RedisMemory) -> str:
        """Get all clients from Redis memory"""

        logger.info(f"Getting all clients from user")
        all_clients = memory.stored_conversation.clients.items()
        if all_clients != []:
            logger.info(f'Se encontraron {len(all_clients)} clientes: {all_clients}')
            return f'Se encontraron {len(all_clients)} clientes: {all_clients}'
        else:
            logger.info(f'No existe ningun cliente registrado por el usuario')
            return f'No existe ningun cliente registrado por el usuario'
        
    def get_all_collections_from_user(self, memory: RedisMemory) -> str:
        """Get all collections from Redis memory"""

        logger.info(f"Getting all clients from user")
        all_collections = {}
        for key,value in memory.stored_conversation.collections.items():
            all_collections[key] = {'collection_id': value.id
                                    , 'client_cellphone': value.client_cellphone
                                    , 'client_full_name': value.client_full_name
                                    , 'status': value.status
                                    , 'description': value.description
                                    , 'amount': value.amount
                                    , 'collection_date': value.collection_date
                                    , 'payment_date': value.payment_date
                                    , 'frecuency_payment': value.frequency_payment
                                    , 'quota/total_quotas': str(value.quota_number)+'/'+str(value.total_quotas)}
        if all_collections != {}:
            logger.info(f'Se encontraron {len(all_collections)} cobros: {all_collections}')
            return f'Se encontraron {len(all_collections)} cobros: {all_collections}'
        else:
            logger.info(f'No existe ningun cliente registrado por el usuario')
            return f'No existe ningun cliente registrado por el usuario'
        
    def phone_validator(self,prefix_phone: str ='+51', phone_number: str='') -> str:
        """Validate phone number format"""
        logger.info(f"Getting all clients from user")
        if ((prefix_phone=='+51') or prefix_phone=='') and (len(phone_number) == 9):
            logger.info(f'Telefono valido: {prefix_phone}{phone_number}')
            return f'El telefono {prefix_phone}{phone_number} es valido, puede ser usado para registrar un cliente o un cobro'
        elif (prefix_phone.startswith('+51')==False):
            logger.info(f'Telefono invalido: {prefix_phone}{phone_number}, el prefijo debe ser +51')
            return f'El telefono {prefix_phone}{phone_number} es invalido, debe comenzar con +51, solo ofrecemos servicio para numeros de Peru'
        elif (len(phone_number) != 9) or (phone_number.startswith('9')==False):
            logger.info(f'Telefono invalido: {prefix_phone}{phone_number}, el numero debe tener 9 digitos')
            return f'El telefono {prefix_phone}{phone_number} es invalido, debe tener 9 digitos sin contar el prefijo'
        elif (phone_number.startswith('9')==False):
            logger.info(f'Telefono invalido: {prefix_phone}{phone_number}, el numero debe empezar con 9')
            return f'El telefono {prefix_phone}{phone_number} es invalido, el numero debe empezar con 9'
        else:
            logger.info(f'Telefono invalido: {prefix_phone}{phone_number}, el numero debe tener 9 digitos y comenzar con +51')
            return f'El telefono {prefix_phone}{phone_number} es invalido, debe tener 9 digitos y comenzar con +51'