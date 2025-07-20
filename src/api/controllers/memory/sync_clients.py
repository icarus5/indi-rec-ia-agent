import json
import logging

import azure.functions as func

from src.domain.services.clients import ClientService, ClientValidationError

logging.basicConfig(level=logging.DEBUG)
post_memory_sync_clients = func.Blueprint()


@post_memory_sync_clients.route(route="memory/clients", methods=["POST"], auth_level="function")
def memory_sync_clients(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Starting synchronization of clients")
    try:
        data = req.get_json()
        logging.info(f"Payload request: {data}")

        if not isinstance(data, list):
            return func.HttpResponse(
                json.dumps({"error": "El payload debe ser una lista de clientes."}),
                mimetype="application/json",
                status_code=400
            )

        client_service = ClientService()
        summary = client_service.add_clients(data)

        return func.HttpResponse(
            json.dumps({"status": "OK", "result": summary}),
            mimetype="application/json",
        )

    except ClientValidationError as errors:
        logging.error("Client invalid request: %s", errors)
        error_details = getattr(errors, 'args', None)
        if error_details and len(error_details) == 1:
            error_details = error_details[0]
        else:
            error_details = str(errors)
        return func.HttpResponse(
            json.dumps({
                "error": "Algunos clientes tienen campos faltantes.",
                "details": error_details
            }),
            mimetype="application/json",
            status_code=400
        )
    except json.JSONDecodeError:
        logging.error("Invalid JSON payload")
        return func.HttpResponse(
            json.dumps({"error": "JSON inválido."}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Unexpected error during grouping: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
