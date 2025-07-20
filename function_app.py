import json
import azure.functions as func

from src.api.controllers.agent.query import post_agent_query
from src.api.controllers.queue.queue_payment_sheet import queue_bp
from src.api.controllers.memory.sync_clients import post_memory_sync_clients
from src.api.controllers.memory.sync_collections import post_memory_sync_collections
from src.utils.logger import get_function_logger

logger = get_function_logger("function_app")

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

app.register_functions(post_agent_query)
app.register_functions(post_memory_sync_collections)
app.register_functions(post_memory_sync_clients)
app.register_functions(queue_bp)

print("Registered all functions successfully.")


@app.route(route="status", methods=["GET"], auth_level="anonymous")
def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info("Health check endpoint '/status' was called.")
    response = {"status": "ok", "message": "API is running"}
    logger.info("Returning status OK.")

    return func.HttpResponse(json.dumps(response), mimetype="application/json")
