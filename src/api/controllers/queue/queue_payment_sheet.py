import os
import json
import azure.functions as func

from src.utils.logger import get_function_logger
from src.domain.services.service_bus import send_message_to_queue
from src.utils.ocr.files_utils import execute_ai_processing_task

logger = get_function_logger("function_app")

queue_bp = func.Blueprint()


@queue_bp.service_bus_queue_trigger(
    arg_name="msg",
    queue_name=os.getenv("AZURE_SERVICE_BUS_MA_FIRST_STEP_QUEUE"),
    connection="AZURE_SERVICE_BUS_MA_CONNECTION_STRING",
)
def service_bus_trigger_ai_worker(msg: func.ServiceBusMessage):
    """
    Función principal que se activa con un mensaje de la cola de Service Bus.
    """
    logger.info(
        f"Worker recibió un nuevo mensaje de la cola '{os.getenv('AZURE_SERVICE_BUS_MA_FIRST_STEP_QUEUE')}'."
    )

    try:
        message_body = msg.get_body().decode("utf-8")
        ai_task_payload = json.loads(message_body)

        print("#########################################################################################################################################################")
        final_json_result = execute_ai_processing_task(ai_task_payload)

        print(final_json_result)

        send_message_to_queue(
            final_json_result, os.getenv("AZURE_SERVICE_BUS_MA_FINAL_STEP_QUEUE")
        )

        logger.info(
            f"Tarea completada. Resultado enviado a la cola '{os.getenv('AZURE_SERVICE_BUS_MA_FINAL_STEP_QUEUE')}'."
        )

    except Exception as e:
        logger.error(f"El worker falló al procesar el mensaje: {e}")
        raise
