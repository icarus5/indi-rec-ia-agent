import openai
from src.utils.logger import logger
from src.domain.models.payload import PayloadAgent
from src.ai.memory import get_memory
from src.ai.builder import build_agent
from src.ai.refusal import handle_content_filter_error
from src.utils.tools.util import get_tools_result, get_tools_log, trim_messages, filtered_bad_words_from_ai
from src.domain.services.messages import MessageService
from src.domain.models.message import Message

message_service = MessageService()

def _build_shared_state(username: str, user_type: str, user_id: str) -> dict:
    """Construye el estado compartido para la sesión del usuario."""
    return {
        "username": username,
        "tools": [],
        "user_id": None if user_type == "anonymous" else user_id
    }

def _build_model_input_data(messages_trimmed, username, user_type, user_id):
    """Construye el input de modelo para el guardado de mensajes."""
    return {
        "messages": messages_trimmed,
        "username": username,
        "user_type": user_type,
        "user_id": user_id
    }

async def _handle_content_filter_error(error_obj, shared_state, user_id, invoke_id, user):
    """Maneja el error de filtro de contenido y guarda el mensaje filtrado."""
    model_output_data = error_obj
    output = handle_content_filter_error(error_obj)
    provider = getattr(user, 'provider', None) or getattr(user, 'source', None) or 'system'
    if not isinstance(output, Message):
        output = Message(sender="ia", message=str(output), provider=provider)
    await message_service.save_message(
        message=output,
        user_id=user_id,
        invoke_id=invoke_id,
        user=user,
        model_data=model_output_data,
        content_filtered=True,
        is_outcome=True
    )
    return {
        "text": output.message if hasattr(output, 'message') else str(output),
        "state": shared_state,
        "all_output": None,
        "tools": [],
    }

async def invoke(payload: PayloadAgent):
    """
    Invoca el agente principal para procesar el mensaje del usuario y manejar la respuesta.
    """
    user_id = payload.user.user_id
    invoke_id = payload.invoke_id
    username = payload.user.name
    user_type = payload.user.get_type()
    memory = get_memory(user_id)
    memory.add_user_message(payload.message)
    messages = memory.messages()
    messages_trimmed = trim_messages(messages)
    shared_state = _build_shared_state(username, user_type, user_id)
    model_input_data = _build_model_input_data(messages_trimmed, username, user_type, user_id)
    is_chit_chat = payload.is_chit_chat

    await message_service.save_message(
        message=payload.message_object,
        user_id=user_id,
        invoke_id=invoke_id,
        user=payload.user,
        model_data=model_input_data,
        is_outcome=False
    )

    logger.info(f"Session ID: {payload.user.current_session_id} - Invoke ID: {invoke_id} - Type user: {user_type}")
    #logger.info(f"Shared state: {shared_state}")

    agent = build_agent(user_type, user_id, shared_state, memory, payload.user.current_session_id, invoke_id, is_chit_chat)
    config = {"configurable": {"thread_id": user_id}}
    output = ""
    if agent.executor:
        #logger.info(f"Session ID: {payload.user.current_session_id} - Invoke ID: {invoke_id} - Invoke agent")
        try:
            result = agent.executor.invoke(
                {
                    "messages": messages_trimmed,
                },
                config=config,
            )
            output = result["messages"][-1].content
            logger.info(f"Session ID: {payload.user.current_session_id} - Invoke ID: {invoke_id} - Output: {output}")
        except openai.BadRequestError as e:
            logger.error(f"Session ID: {payload.user.current_session_id} - Invoke ID: {invoke_id} - Error invoking agent: {str(e)}")
            error_obj = e.body
            if error_obj.get("code") == "content_filter":
                return await _handle_content_filter_error(error_obj, shared_state, user_id, invoke_id, payload.user)
            else:
                output = "Estoy teniendo problemas para responder tu pregunta 😔. Por favor, intenta de nuevo, con otras palabras"
                return {
                    "text": output,
                    "state": shared_state,
                    "all_output": None,
                    "tools": [],
                }
        except Exception as e:
            logger.error(f"Session ID: {payload.user.current_session_id} - Invoke ID: {invoke_id} - Error invoking agent: {str(e)}")
            output = "Estoy teniendo problemas para responder tu pregunta 😩. Por favor, intenta de nuevo, con otras palabras"
            result = None
        memory.add_ai_message(output)
        if '[LINK]' in output:
            output = output.replace('[LINK]', shared_state.get("url_payment", ""))
        if result:
            num_messages = len(messages_trimmed)
            tools_log = get_tools_log(result["messages"], num_messages)
            tool_messages = get_tools_result(result["messages"], num_messages)
            for msg in tool_messages:
                memory.add_ai_message(msg)
            memory.save()
            filtered_messages = filtered_bad_words_from_ai(result["messages"])
            if filtered_messages:
                ai_msg = filtered_messages[0]
                error_obj = {
                    "innererror": {
                        "content_filter_result": ai_msg.response_metadata.get("content_filter_results", {{}})
                    }
                }
                reason = handle_content_filter_error(error_obj)
                logger.warning(f"Session ID: {payload.user.current_session_id} - Invoke ID: {invoke_id} - Mensajes AI filtrados por contenido: {filtered_messages}")
                output = reason
                model_output_data = message_service.build_model_data(
                    tools=tools_log,
                    message=output
                )
                await message_service.save_message(
                    message=output,
                    user_id=user_id,
                    invoke_id=invoke_id,
                    user=payload.user,
                    model_data=model_output_data,
                    content_filtered=True,
                    is_outcome=True
                )
                return {
                    "text": output,
                    "state": shared_state,
                    "all_output": result,
                    "tools": tools_log,
                }
            else:
                model_output_data = message_service.build_model_data(
                    tools=tools_log,
                    message=output
                )
                await message_service.save_message(
                    message=output,
                    user_id=user_id,
                    invoke_id=invoke_id,
                    user=payload.user,
                    model_data=model_output_data,
                    is_outcome=True
                )
                return {
                    "text": output,
                    "state": shared_state,
                    "all_output": result,
                    "tools": tools_log,
                }
        else:
            await message_service.save_message(
                message=output,
                user_id=user_id,
                invoke_id=invoke_id,
                user=payload.user,
                model_data=None,
                is_outcome=True
            )
            return {
                "text": output,
                "state": shared_state,
                "all_output": None,
                "tools": [],
            }
