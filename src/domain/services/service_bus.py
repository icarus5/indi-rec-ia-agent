import os
import json
from azure.servicebus import ServiceBusClient, ServiceBusMessage

from src.utils.logger import get_function_logger

logger = get_function_logger("function_app")


def send_message_to_queue(json_data: dict, queue_name: str):
    """
    Envía un mensaje JSON a una cola específica de Azure Service Bus.

    Args:
        json_data: El diccionario a enviar.
        queue_name: El nombre de la cola de destino.
    """
    connection_string = os.getenv("AZURE_SERVICE_BUS_MA_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_SERVICE_BUS_MA_CONNECTION_STRING no está configurado.")
        raise ValueError("La cadena de conexión del Service Bus no está configurada.")

    if not queue_name:
        logger.error("queue_name no está configurado.")
        raise ValueError("El nombre de la cola del Service Bus no está configurado.")

    try:
        with ServiceBusClient.from_connection_string(connection_string) as client:
            sender = client.get_queue_sender(queue_name=queue_name)
            message_body = json.dumps(json_data).encode("utf-8")
            message = ServiceBusMessage(message_body)
            sender.send_messages(message)
            logger.info(f"Mensaje enviado exitosamente a la cola '{queue_name}'.")
    except Exception as e:
        logger.error(f"Error al enviar mensaje a la cola '{queue_name}': {e}")
        raise
