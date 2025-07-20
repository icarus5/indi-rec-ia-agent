import logging
from src.domain.models.client import Client

from src.ai.memory import RedisMemory
from src.domain.models.collection_register import CollectionRegister
from src.integrations.indi.provider import IndiProvider
from src.utils.date.date_utils import get_current_day

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_wrapper_register_client(user_id: any, memory: RedisMemory, session_id: str = "", invoke_id: str = ""):
    def register_client(name: str, phone_number: str, surname: str = "", code_phone: str = "PE", prefix_phone: str = "+51", email: str = "") -> str:
        client = Client(
            id=f"{prefix_phone}{phone_number}",
            name=name,
            surname=surname,
            code_phone=code_phone,
            prefix_phone=prefix_phone,
            phone_number=phone_number,
            email=email,
            creditor_id=user_id
        )
        try:
            indi_provider = IndiProvider()
            logger.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Calling tool register_client with params: name={name}\
                        , phone_number={phone_number}, surname={surname}, code_phone={code_phone}, prefix_phone={prefix_phone}, email={email}")
            client = indi_provider.create_client(client)
            memory.add_client(client)
            memory.save()
            logger.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Se registro un nuevo cliente, con numero de telefono: {client.prefix_phone}{client.phone_number}")
            return f"Se registro un nuevo cliente, con numero de telefono: {client.prefix_phone}{client.phone_number}"
        except Exception as e:
            logger.error(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Error al registrar el cliente: {e}")
            return f"Error al registrar el cliente"

    return register_client

def get_wrapper_register_collection(user_id: str, memory: RedisMemory, session_id: str = "", invoke_id: str = ""):
    def register_collection(subject: str, amount: float, name: str, clientPhoneNumber: str, surname: str = '', code_phone: str ='PE', prefix_phone: str = "+51"
                            , date = get_current_day(), frequency_payment = "ÚNICO", total_quotas = 1, currency = "Soles (S/)", is_indefinite = False) -> str:
        collection_register = CollectionRegister(
            name=name,
            surname=surname,
            code_phone=code_phone,
            prefix_phone=prefix_phone,
            clientPhoneNumber=clientPhoneNumber,
            description=subject,
            currency=currency,
            amount=amount,
            collection_date=date,
            total_quotas=total_quotas,
            frequency_payment=frequency_payment,
            creditor_id=user_id,
            is_indefinite=is_indefinite,
        )
        try:
            provider = IndiProvider()
            logging.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Calling tool register_collection with params: {collection_register}")
            clients, collections = provider.create_collection(collection_register)
            logging.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Successful call tool register_collection: {collections}")
            [memory.add_client(client) for client in clients]
            [memory.add_collection(collection) for collection in collections]
            memory.save()
            return f"Se registró un nuevo cobro de tipo {frequency_payment} con {total_quotas} cuota(s)."
        except Exception as e:
            logger.error(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Error al registrar el cobro: {e}")
            return f"Error al registrar el cobro"

    return register_collection

def get_wrapper_to_register_transfer(shared_state, session_id: str = "", invoke_id: str = ""):
    def to_register_transfer(receiver_name: str, amount: float,  receiver_phone: str = None) -> str:
        """Tool para registrar una transferencia de dinero a un usuario de la plataforma de pagos de Indi
        :param receiver_name: Nombre del receptor de la transferencia.
        :param receiver_phone: Numero de celular del receptor de la transferencia.
        :amount: Monto de la transferencia."""

        if amount > 0:
            
            url = "https://indibcp.short.gy/indiyape"
            shared_state["url_payment"] = url
            return f"Responde al usuario con este text (asegurate que incluya [LINK]): 'Indica al usuario que para proceder con la transferencia, debe ingresar a este link [LINK]'"

    return to_register_transfer

def get_wrapper_delete_collection(user_id: any, memory: RedisMemory, session_id: str = "", invoke_id: str = ""):
    def delete_collection(collection_id: str) -> str:
        logger.info(f"Invocando delete_collection con collection_id: {collection_id} y user_id: {user_id}")
        try:
            indi_provider = IndiProvider()
            logger.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Calling tool delete_collection with params: collection_id:{collection_id}, user_id:{user_id}")
            indi_provider.delete_collection(collection_id, user_id)
            memory.delete_collection(collection_id)
            memory.save()
            
            return f"Se eliminó la colección con ID: {collection_id}"
        except Exception as e:
            logger.error(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Error al eliminar la colección: {e}")
            return f"Error al eliminar la colección"

    return delete_collection

def get_wrapper_verify_client_by_phone_number(user_id: any, memory: RedisMemory, session_id: str = "", invoke_id: str = ""):
    def verify_client_by_phone_number(phone_number: str) -> str:
        try:
            logger.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Calling tool verify_client_by_phone_number with params: phone_number:{phone_number}")
            indi_provider = IndiProvider()
            data = indi_provider.get_clients_by_phone_number(phone_number, memory)
            return data
        except Exception as e:
            logger.error(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Error al verificar si el cliente existe: {e}")
            return f"Error al verificar si el cliente existe"

    return verify_client_by_phone_number

def get_wrapper_verify_client_by_name(user_id: any, memory: RedisMemory, session_id: str = "", invoke_id: str = ""):
    def verify_client_by_name(name: str) -> str:
        try:
            logger.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Calling tool verify_client_by_name with params: name: {name}")
            indi_provider = IndiProvider()
            data = indi_provider.get_clients_by_name(name, memory)
            return data
        except Exception as e:
            logger.error(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Error al verificar si el cliente existe: {e}")
            return f"Error al verificar si el cliente existe"

    return verify_client_by_name

def get_wrapper_get_all_clients(user_id: any, memory: RedisMemory, session_id: str = "", invoke_id: str = ""):
    def get_all_clients() -> str:
        try:
            logger.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Calling tool get_all_clients with params: user_id: {user_id}")
            indi_provider = IndiProvider()
            data = indi_provider.get_all_clients_from_user(memory)
            return data
        except Exception as e:
            logger.error(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Error al obtener a los clientes: {e}")
            return f"Error al verificar si el cliente existe"

    return get_all_clients

def get_wrapper_get_all_collections(user_id: any, memory: RedisMemory, session_id: str = "", invoke_id: str = ""):
    def get_all_collections() -> str:
        try:
            logger.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Calling tool get_all_collections with params: user_id: {user_id}")
            indi_provider = IndiProvider()
            data = indi_provider.get_all_collections_from_user(memory)
            return data
        except Exception as e:
            logger.error(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Error al obtener los cobros: {e}")
            return f"Error al verificar si el cliente existe"

    return get_all_collections

def get_wrapper_phone_validation(user_id: any, memory: RedisMemory, session_id: str = "", invoke_id: str = ""):
    def get_phone_validation(prefix_phone: str, phone_number: str) -> str:
        try:
            logger.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Calling tool get_phone_validation with params: prefix_phone: {prefix_phone}, phone_number: {phone_number}")
            indi_provider = IndiProvider()
            data = indi_provider.phone_validator(prefix_phone, phone_number)
            return data
        except Exception as e:
            logger.error(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Error al verificar si el numero de telefono es valido: {e}")
            return f"Error al verificar si el cliente existe"

    return get_phone_validation