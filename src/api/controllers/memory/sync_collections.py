import json
import logging

import azure.functions as func

from src.domain.services.collections import CollectionService, CollectionValidationError

logging.basicConfig(level=logging.INFO)
post_memory_sync_collections = func.Blueprint()


@post_memory_sync_collections.route(route="memory/collections", methods=["POST"])
def memory_sync_collections(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Starting synchronization of collections")
    try:
        data = req.get_json()
        logging.debug(f"Payload request: {data}")

        if not isinstance(data, list):
            return func.HttpResponse(
                json.dumps({"error": "El payload debe ser una lista de cobros."}),
                mimetype="application/json",
                status_code=400
            )

        collection_service = CollectionService()

        summary = collection_service.add_collections(data)

        return func.HttpResponse(
            json.dumps({"status": "OK", "result": summary}),
            mimetype="application/json",
        )
    except CollectionValidationError as errors:
        logging.error("Collection invalid request: %s", errors)
        error_details = getattr(errors, 'args', None)
        if error_details and len(error_details) == 1:
            error_details = error_details[0]
        else:
            error_details = str(errors)
        return func.HttpResponse(
            json.dumps({
                "error": "Algunos solicitudes tienen campos faltantes.",
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
        logging.error(f"Error during saving: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
