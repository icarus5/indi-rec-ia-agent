import json
import logging
import azure.functions as func

from src.domain.services.conversation import ConversationService
from src.domain.services.processor import ProcessorService
from src.domain.services.users import UserService
from src.channels.factory import ChannelFactory

logging.basicConfig(level=logging.DEBUG)
post_agent_query = func.Blueprint()

message_processor = ProcessorService()


@post_agent_query.route(route="agent/query", methods=["POST"])
async def agent_query(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Start request")

    if not req.get_body():
        return func.HttpResponse(
            json.dumps({"error": "El cuerpo de la solicitud está vacío."}),
            mimetype="application/json",
            status_code=400,
        )

    try:
        data = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps(
                {"error": "El cuerpo de la solicitud no contiene un JSON válido."}
            ),
            mimetype="application/json",
            status_code=400,
        )

    logging.info(f"Payload request: {data}")

    user_service = UserService()
    user = user_service.get_or_create_user(
        data.get("sender"), data.get("forceAnonymous", False)
    )
    logging.info(f"Current Session ID: {user.current_session_id}")

    jelou_channel = ChannelFactory.create_channel("jelou")
    message, is_enterprise, is_enterprise_file = await jelou_channel.parse_message(data, user)

    if message is None:
        return func.HttpResponse(
            json.dumps({"error": "Invalid request"}), mimetype="application/json"
        )

    elif is_enterprise and message["status"] == "complete" and is_enterprise_file:
        logging.info("Message is an enterprise file with complete status")
        conversation_service = ConversationService()
        conversation_service.get_or_create_conversation(user)
        raw_message = message["message"]
        response = raw_message.message
        logging.info("Finish request")
        return func.HttpResponse(
            json.dumps({"status": "ok", "tools": [], "message": response}),
            mimetype="application/json",
        )

    elif message["status"] == "complete":
        conversation_service = ConversationService()
        conversation_service.get_or_create_conversation(user)
        response = await message_processor.process_message(message["message"], user, is_enterprise)
        logging.info("Finish request")
        return func.HttpResponse(
            json.dumps(
                {
                    "status": "ok",
                    "tools": response.get("tools"),
                    "message": response.get("text"),
                }
            ),
            mimetype="application/json",
        )

    elif message["status"] == "interal_failure":
        return func.HttpResponse(
            json.dumps(
                {
                    "status": "ok",
                    "tools": message.get("tools", []),
                    "message": message.get("message"),
                }
            ),
            mimetype="application/json",
        )

    else:
        logging.info("Finish request")
        return func.HttpResponse(
            json.dumps({"status": "message buffered, waiting for buffer time to end"}),
            status_code=500,
            mimetype="application/json",
        )
