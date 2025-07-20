import io
import re
import time
import json
import traceback
import pandas as pd

from src.ai.llm import get_model
from src.ai.prompts.base import get_prompt
from src.utils.logger import get_function_logger

logger = get_function_logger("function_app")


def get_file_mime_type(file_info):
    """Determina el tipo MIME del archivo basándose en su contenido."""
    valid_mime_types = [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    return file_info if file_info in valid_mime_types else None


def clean_response(content):
    """Limpia la respuesta eliminando backticks y bloques de código."""
    content = re.sub(r"^```[\w]*\n|```$", "", content, flags=re.MULTILINE)
    return content.strip()


def excel_date_to_str(excel_date):
    """Convierte una fecha numérica de Excel a formato YYYY-MM-DD."""
    try:
        if pd.isna(excel_date) or not isinstance(excel_date, (int, float)):
            return None
        excel_epoch = pd.Timestamp("1900-01-01")
        return (excel_epoch + pd.Timedelta(days=excel_date - 2)).strftime("%Y-%m-%d")
    except Exception as e:
        logger.warning(f"Error al convertir fecha {excel_date}: {e}")
        return None


def prepare_ai_task_from_excel(content: bytes, user_id: str) -> dict:
    """
    Paso 1 (RÁPIDO): Lee los bytes de un Excel, lo convierte a CSV y prepara el payload para la IA.
    Esta función NO llama a la IA. Es rápida y se puede ejecutar en el trigger inicial.

    Args:
        content: Bytes del archivo Excel.
        user_id: ID del usuario que envía el archivo, usado para personalizar el prompt.

    Returns:
        Un diccionario listo para ser encolado como una tarea para la IA.

    Raises:
        ValueError: Si el archivo Excel no es válido o está vacío.
    """
    try:
        logger.info("Leyendo archivo Excel con Pandas...")
        df = pd.read_excel(io.BytesIO(content))
        df.dropna(how="all", inplace=True)

        if df.empty:
            raise ValueError(
                "La primera hoja del archivo Excel está vacía o no contiene datos."
            )

        df.fillna({"TOTAL": 0, "SALDO": 0, "A CUENTA": 0}, inplace=True)
        if "FECHA" in df.columns:
            df["FECHA"] = df["FECHA"].apply(excel_date_to_str)

        excel_as_csv = df.to_csv(index=False, sep=";", na_rep="")
        logger.info("Archivo Excel convertido a CSV exitosamente.")

        if not user_id or not isinstance(user_id, str):
            raise ValueError("El user_id proporcionado no es válido.")
        user_id = user_id.strip().replace("\r\n", "").replace("\n", "")
        user_id = re.sub(r"[^+\d]", "", user_id)
        if not user_id.startswith("+") or not user_id[1:].isdigit():
            raise ValueError("El user_id debe comenzar con '+' seguido de números.")
        logger.info(f"user_id después de limpieza: {user_id}")

        pre_prompt = get_prompt("AZURE_ENTERPRISE_OCR_PROMPT_ID")

        if "{user_id}" not in pre_prompt or "{current_date}" not in pre_prompt:
            raise ValueError(
                "El prompt descargado no contiene los marcadores {user_id} o {current_date}."
            )

        try:
            current_date = pd.Timestamp.now().strftime("%Y-%m-%d")
            logger.info(
                f"Intentando formatear el prompt con user_id: {user_id} y current_date: {current_date}"
            )

            prompt = pre_prompt.replace("{user_id}", user_id).replace(
                "{current_date}", current_date
            )
            logger.info(f"Prompt final: {prompt}")
        except Exception as format_error:
            logger.error(f"Error al formatear el prompt: {format_error}")
            logger.error(f"Contenido de pre_prompt: {pre_prompt}")
            logger.error(f"Contenido de user_id: {user_id}")
            logger.error(f"Contenido de current_date: {current_date}")
            raise ValueError(
                "Error al formatear el prompt con el user_id proporcionado."
            ) from format_error

        ai_task_payload = {"prompt": prompt, "data": excel_as_csv}
        return ai_task_payload

    except Exception as e:
        logger.error(f"Error al pre-procesar el archivo Excel: {e}")
        raise ValueError(
            f"Error al leer el archivo Excel. Asegúrate de que sea válido. Detalle: {e}"
        ) from e


def prepare_ai_task_from_picture(content: str, user_id: str) -> dict:
    """
    Paso 1 (RÁPIDO): Lee la cadena de texto proveniente de un ocr y prepara el payload para la IA.
    Esta función NO llama a la IA. Es rápida y se puede ejecutar en el trigger inicial.

    Args:
        content: String del contenido extraído por OCR
        user_id: ID del usuario que envía el archivo, usado para personalizar el prompt.

    Returns:
        Un diccionario listo para ser encolado como una tarea para la IA.

    Raises:
        ValueError: Si el archivo Excel no es válido o está vacío.
    """
    try:

        pre_prompt = get_prompt("AZURE_ENTERPRISE_OCR_PROMPT_ID")

        if "{user_id}" not in pre_prompt or "{current_date}" not in pre_prompt:
            raise ValueError(
                "El prompt descargado no contiene los marcadores {user_id} o {current_date}."
            )

        try:
            current_date = pd.Timestamp.now().strftime("%Y-%m-%d")
            logger.info(
                f"Intentando formatear el prompt con user_id: {user_id} y current_date: {current_date}"
            )

            prompt = pre_prompt.replace("{user_id}", user_id).replace(
                "{current_date}", current_date
            )
            logger.info(f"Prompt final: {prompt}")
        except Exception as format_error:
            logger.error(f"Error al formatear el prompt: {format_error}")
            logger.error(f"Contenido de pre_prompt: {pre_prompt}")
            logger.error(f"Contenido de user_id: {user_id}")
            logger.error(f"Contenido de current_date: {current_date}")
            raise ValueError(
                "Error al formatear el prompt con el user_id proporcionado."
            ) from format_error

        ai_task_payload = {"prompt": prompt, "data": content}
        return ai_task_payload

    except Exception as e:
        logger.error(f"Error al pre-procesar el contenido OCR: {e}")
        raise ValueError(
            f"Error al procesar el contenido OCR. Asegúrate de que sea válido. Detalle: {e}"
        ) from e


def execute_ai_processing_task(ai_task_payload: dict) -> dict:
    """
    Paso 2 (LENTO): Recibe el paquete de trabajo, llama a la IA y devuelve el JSON estructurado.
    Esta función será ejecutada por el worker en segundo plano.

    Args:
        ai_task_payload: El diccionario de datos para el procesamiento.

    Returns:
        El diccionario JSON final estructurado por la IA.

    Raises:
        ValueError: Si la llamada a la IA o el parseo del JSON fallan.
    """
    start_time = time.time()

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": ai_task_payload["prompt"]},
                {
                    "type": "text",
                    "text": f"Analiza los siguientes datos y estructúralos en JSON:\n\n{ai_task_payload['data']}",
                },
            ],
        }
    ]

    model = get_model()

    try:
        logger.info("Enviando datos al modelo de IA para estructuración...")
        response = model.invoke(messages)
        content_response = response.content
        cleaned_content = clean_response(content_response)

        try:
            final_response = json.loads(cleaned_content)
        except json.JSONDecodeError as json_error:
            logger.error(
                f"Error: La respuesta del modelo no es un JSON válido. Respuesta recibida:\n{content_response}"
            )
            raise ValueError(
                "La respuesta del modelo no es un JSON válido."
            ) from json_error

        if (
            not isinstance(final_response, dict)
            or "user_id" not in final_response
            or not isinstance(final_response.get("acreetors"), list)
        ):
            logger.error("El JSON generado no cumple con la estructura esperada.")
            raise ValueError("El JSON generado no cumple con la estructura esperada.")

        processing_time = time.time() - start_time
        logger.info(
            f"Procesamiento por IA completado en {processing_time:.2f} segundos."
        )
        return final_response

    except json.JSONDecodeError:
        error_msg = "Error: La respuesta del modelo no es un JSON válido."
        logger.error(error_msg)
        logger.error(f"Respuesta recibida:\n{content_response}")
        raise ValueError(error_msg) from None
    except Exception as e:
        logger.error(f"Error inesperado durante la llamada al modelo: {e}")
        traceback.print_exc()
        raise
