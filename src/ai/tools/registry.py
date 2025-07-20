from src.ai.tools.creditor_schemas import RegisterClientSchema, RegisterCollectionSchema, RegisterTransferSchema, DeleteCollectionSchema, ValidatePhoneNumberSchema, VerifyClientByNameSchema, VerifyClientByPhoneNumberSchema
from src.ai.tools.creditor_tools import get_wrapper_get_all_clients, get_wrapper_get_all_collections, get_wrapper_phone_validation, get_wrapper_register_client, get_wrapper_register_collection, get_wrapper_to_register_transfer, get_wrapper_delete_collection, get_wrapper_verify_client_by_name, get_wrapper_verify_client_by_phone_number
from src.ai.memory import RedisMemory
from langchain.tools import StructuredTool

def get_tools_acreetor(user_id, shared_state, memory: RedisMemory, session_id='', invoke_id=''):
    tools = [
        StructuredTool(
            name="register_client", 
            description="""
            Tool para registrar un nuevo cliente.
            NOTAS:
            - Solo invoca a este tool cuando se tenga todos los datos necesarios para registrar un cliente.
            - Nunca puedes inventar información, siempre debes pedir al usuario que te la proporcione.
            - Solo se puede invocar este tool si se realizo una invocacion de `verify_client_by_phone_number` anteriormente.
            """,
            func=get_wrapper_register_client(user_id, memory, session_id=session_id, invoke_id=invoke_id), 
            args_schema=RegisterClientSchema
        ),
        StructuredTool(
            name="register_collection", 
            description="""
            Tool para registrar un nuevo cobro, registra automaticamente al cliente, en caso este no exista.
            """,
            func=get_wrapper_register_collection(user_id, memory, session_id=session_id, invoke_id=invoke_id), 
            args_schema=RegisterCollectionSchema
        ),
        StructuredTool(
            name="register_transfer", 
            description="""
            Tool para transferir dinero a un cliente.
            """,
            func=get_wrapper_to_register_transfer(shared_state, session_id=session_id, invoke_id=invoke_id), 
            args_schema=RegisterTransferSchema
        ),
        StructuredTool(
            name="delete_collection", 
            description="""
            Tool para eliminar un cobro.
            """,
            func=get_wrapper_delete_collection(user_id, memory, session_id=session_id, invoke_id=invoke_id), 
            args_schema=DeleteCollectionSchema
        ),
        StructuredTool(
            name="verify_client_by_phone_number", 
            description="""
            Tool para verificar la existencia de un cliente mediante su numero de telefono.
            """,
            func=get_wrapper_verify_client_by_phone_number(user_id, memory, session_id=session_id, invoke_id=invoke_id), 
            args_schema=VerifyClientByPhoneNumberSchema
        ),
        StructuredTool(
            name="verify_client_by_name", 
            description="""
            Tool para obtener todos los usuarios existentes en base a la primera letra del nombre.
            Tambien puedes usar este tool para encontrar el [raw_id] de un cliente con su nombre.
            """,
            func=get_wrapper_verify_client_by_name(user_id, memory, session_id=session_id, invoke_id=invoke_id), 
            args_schema=VerifyClientByNameSchema
        ),
        StructuredTool(
            name="get_all_clients", 
            description="""
            Tool para obtener todos clientes registrados del usuario.
            """,
            func=get_wrapper_get_all_clients(user_id, memory, session_id=session_id, invoke_id=invoke_id), 
            args_schema=None
        ),
        StructuredTool(
            name="get_all_collections", 
            description="""
            Tool para obtener todos los cobros registrados del usuario.
            Tambien puedes usar este tool para encontrar el [collection_id] de un cobro.
            """,
            func=get_wrapper_get_all_collections(user_id, memory, session_id=session_id, invoke_id=invoke_id), 
            args_schema=None
        ),
        StructuredTool(
            name="get_phone_validation", 
            description="""
            Tool para validar cualquier numero de telefono otorgado por el usuario.
            Esta tool no requiere confirmacion de usuario para su uso.
            """,
            func=get_wrapper_phone_validation(user_id, memory, session_id=session_id, invoke_id=invoke_id), 
            args_schema=ValidatePhoneNumberSchema
        ),
    ]
    return tools
