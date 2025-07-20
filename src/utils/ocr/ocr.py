import os
import re
import ast
import json
import time
import base64
import logging
import traceback

from src.ai.llm import get_model_for_image
from src.utils.logger import get_function_logger
from src.utils.ocr.doc_int import analyze_invoice, analyze_receipt
from src.domain.services.service_bus import send_message_to_queue
from src.utils.ocr.files_utils import get_file_mime_type, prepare_ai_task_from_excel, prepare_ai_task_from_picture
from src.utils.ocr.image_utils import (
    download_image_url,
    get_image_mime_type,
    get_ocr_acreetor_prompt,
)

logger = get_function_logger("function_app")

def get_text_from_image(content, prompt=str, media_url='', session_id='', invoke_id=''):
    """
    Extrae texto de una imagen usando el modelo de OCR y el prompt definido.

    Args:
        content: Bytes de la imagen.
        prompt: Prompt a utilizar para el modelo de OCR.

    Returns:
        Tuple[bool, str]: (Éxito, Resultado o mensaje de error).
    """
    start_time = time.time()
    logging.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Procesando imagen de {len(content)} bytes")

    mime_type = get_image_mime_type(content)
    if not mime_type:
        logging.error(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Formato de imagen no soportado")
        return False, "Formato de imagen no soportado. Por favor, envía una imagen JPG o PNG."

    try:
        base64_image = base64.b64encode(content).decode("utf-8")
    except Exception as e:
        logging.error(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Error al codificar imagen: {str(e)}")
        return False, "Error al procesar la imagen. Por favor, verifica el contenido."

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                },
            ],
        }
    ]

    model = get_model_for_image()
    try:
        response = model.invoke(messages)
        content_response = response.content
        cleaned_content = clean_response(content_response)
        logging.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Output OCR: {cleaned_content}")
        try:
            final_response = json.loads(cleaned_content)
        except json.JSONDecodeError:
            final_response = ast.literal_eval(cleaned_content)
        except ValueError as ve:
            logging.error(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Error parsing response: {str(ve)}")
            return False, "Error al interpretar la respuesta del modelo. Por favor, verifica el contenido."
        
        if final_response.get('isReceipt', False) and final_response.get('success', False):
            logging.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Processing with Doc Intelligence")
            final_response = analyze_receipt(media_url, session_id, invoke_id)

        logging.info(f"Session ID: {session_id} - Invoke ID: {invoke_id} - Procesamiento completado en {time.time() - start_time:.2f} segundos")
        return True, final_response

    except ConnectionError:
        logging.error("Error de conexión con el modelo")
        return False, "No se pudo conectar al servicio. Por favor, intenta de nuevo."
    except ValueError as ve:
        logging.error(f"Error en el procesamiento: {str(ve)}")
        return False, "Error en los datos de la imagen. Por favor, verifica el contenido."
    except Exception as e:
        logging.error(f"Error inesperado al procesar imagen: {str(e)}")
        traceback.print_exc()
        return False, "Hubo un error al procesar la imagen, por favor intenta de nuevo."

def clean_response(content):
    """Limpia la respuesta eliminando backticks y bloques de código."""
    content = re.sub(r'^```[\w]*\n|```$', '', content, flags=re.MULTILINE)
    return content.strip()

def process_image_ocr(media_url, caption=None, session_id='', invoke_id=''):
    """
    Descarga la imagen desde la URL y realiza el procesamiento OCR.
    Devuelve un diccionario con el resultado y el texto extraído.
    """
    try:
        image_content = download_image_url(media_url)
        mime_type = get_image_mime_type(image_content)
        if not mime_type:
            logging.info(f"Formato de imagen no soportado mime type: {mime_type}")
            return {"success": False, "message": "Formato de imagen no soportado. Por favor, envía una imagen JPG o PNG.", 'ocr_context': "Formato de imagen no soportado.", "image": {}}
        prompt = get_ocr_acreetor_prompt(
            caption=caption,
            session_id=session_id,
            invoke_id=invoke_id,
        )
        _, body = get_text_from_image(image_content, prompt, media_url, session_id, invoke_id)
        if body.get("success", False) and caption:
                body["message"] = f"{caption} {body['message']}"
        return body
    except Exception as e:
        logging.error(f"Error procesando imagen para OCR: {e}")
        return {"success": False, "message": "Hubo un error procesando la imagen, por favor intentalo de nuevo.",'ocr_context': "No se pudo procesar la imagen", "image": {}}

def process_enterprise_image_ocr(media_url, user_id=None, session_id="", invoke_id=""):
    """
    Descarga la imagen desde la URL y realiza el procesamiento OCR.
    Devuelve un diccionario con el resultado estructurado.
    Envia el procesamiento a la cola de Azure Service Bus para su procesamiento posterior.
    Esta función es específica para usuarios de tipo enterprise.
    """
    try:
        image_content = download_image_url(media_url)
        mime_type = get_image_mime_type(image_content)
        if not mime_type:
            logger.error("Formato de imagen no soportado")
            return {
                "success": False,
                "message": "Formato de imagen no soportado. Por favor, envía una imagen JPG o PNG.",
                "image": {},
            }

        invoice_summary = analyze_invoice(media_url, session_id, invoke_id)

        if not invoice_summary.get("success"):
            return {
                "success": False,
                "message": "No se pudo analizar correctamente la imagen.",
                "image": {},
            }

        ocr_context = invoice_summary["ocr_context"]

        ai_task_payload = prepare_ai_task_from_picture(ocr_context, user_id)

        send_message_to_queue(
            ai_task_payload, os.getenv("AZURE_SERVICE_BUS_MA_FIRST_STEP_QUEUE")
        )

        return {
            "success": True,
            "message": "El archivo ha sido recibido correctamente y el procesamiento de los datos ya está en curso.\nEstoy aqui para ayudarte. ¿Tienes alguna consulta? ¡Escribeme!",
            "file": {},
        }

    except Exception as e:
        logger.error(f"Error procesando imagen para OCR enterprise: {e}")
        return {
            "success": False,
            "message": "Hubo un error procesando la imagen, por favor intentalo de nuevo.",
            "ocr_context": "No se pudo procesar la imagen",
            "image": {},
        }


def process_enterprise_file_ocr(media_url, original_mime_type=None, user_id=None):
    """
    Descarga el archivo desde la URL y realiza el procesamiento OCR.
    Devuelve un diccionario con el resultado y el texto extraído.
    """
    try:
        file_content = download_image_url(media_url)
        mime_type = get_file_mime_type(original_mime_type)
        if not mime_type:
            logger.error("Formato de archivo no soportado")
            return {
                "success": False,
                "message": "Formato de archivo no soportado. Por favor, envía un XLS o XLSX.",
                "file": {},
            }

        ai_task_payload = prepare_ai_task_from_excel(file_content, user_id)

        send_message_to_queue(
            ai_task_payload, os.getenv("AZURE_SERVICE_BUS_MA_FIRST_STEP_QUEUE")
        )

        return {
            "success": True,
            "message": "El archivo ha sido recibido correctamente y el procesamiento de los datos ya está en curso.\nEstoy aqui para ayudarte. ¿Tienes alguna consulta? ¡Escribeme!",
            "file": {},
        }

    except Exception as e:
        logger.error(f"Error procesando archivo para OCR: {e}")
        return {"success": False, "message": "", "file": {}}  
