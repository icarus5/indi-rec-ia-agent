import imghdr
import requests

from src.ai.prompts.base import get_prompt


def download_image_url(url: str) -> bytes:
    """Descarga una imagen desde una URL y retorna su contenido en bytes."""
    response = requests.get(url, headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        return response.content
    else:
        raise ValueError(
            f"Error al descargar la imagen: {response.status_code} {response.text}"
        )


def get_image_mime_type(content) -> str:
    """Determina el tipo MIME de la imagen."""
    image_type = imghdr.what(None, h=content)
    if image_type in ["jpeg", "png"]:
        return f"image/{image_type}"
    return None


def get_image_name(image_id: str, mime_type: str) -> str:
    """Obtiene el nombre de archivo de la imagen basado en el ID y el tipo MIME."""
    MIME_TYPE_MAPPING = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/bmp": "bmp",
        "image/webp": "webp",
    }
    extension = MIME_TYPE_MAPPING.get(mime_type, "jpg")
    return f"{image_id}.{extension}"


def get_ocr_acreetor_prompt(caption="", session_id="", invoke_id="") -> str:
    """
    Obtiene el prompt para el acreedor y lo formatea con el caption proporcionado.
    """

    pre_prompt = get_prompt(
        "AZURE_OCR_PROMPT_ID", session_id=session_id, invoke_id=invoke_id
    )
    prompt = pre_prompt.format(caption=caption)
    return prompt
