import logging
from enum import Enum

class CustomBlocklistEnum(Enum):
    """
    Enum para los tipos de listas de bloqueo personalizadas.
    """
    AbuseList = "abusos"
    RudenessList = "lenguaje grosero"
    DiscriminatoryList = "lenguaje discriminatorio"
    SexualList = "contenido sexual"
    ViolenceList = "violencia"

class GenericFilterEnum(Enum):
    """
    Enum para los tipos de filtros genéricos.
    """
    sexual = "contenido sexual inapropiado"
    hate = "discurso de odio"
    self_harm = "autolesiones"
    violence = "violencia"
    jailbreak = "evasión de políticas de seguridad"

def _process_custom_blocklists(custom_blocklists):
    """
    Procesa la lista de custom_blocklists y retorna los mensajes de filtro encontrados SOLO si 'filtered' es True.
    Recibe siempre un objeto con 'details' y 'filtered'.
    """
    if not isinstance(custom_blocklists, dict) or 'details' not in custom_blocklists:
        logging.warning("Estructura inesperada en custom_blocklists: %s", custom_blocklists)
        return []
    if not custom_blocklists.get('filtered', False):
        return []
    return [
        CustomBlocklistEnum.__members__[detail["id"]].value
        for detail in custom_blocklists["details"]
        if detail.get("filtered", False) is True and detail.get("id") in CustomBlocklistEnum.__members__
    ]

def _process_generic_filters(filter_results):
    """
    Procesa los filtros genéricos (sexual, hate, self_harm, etc.) y retorna los mensajes de filtro encontrados.
    """
    return [
        GenericFilterEnum.__members__[filter_type].value
        for filter_type, result_error in filter_results.items()
        if filter_type != "custom_blocklists"
        and isinstance(result_error, dict)
        and result_error.get("filtered") is True
        and filter_type in GenericFilterEnum.__members__
    ]

def handle_content_filter_error(error_obj):
    """
    Orquesta el manejo de errores de filtro de contenido, utilizando funciones auxiliares para desacoplar la lógica.
    """
    filter_results = error_obj.get("innererror", {}).get("content_filter_result", {})

    filter_messages = []
    if "custom_blocklists" in filter_results:
        filter_messages.extend(_process_custom_blocklists(filter_results["custom_blocklists"]))
    filter_messages.extend(_process_generic_filters(filter_results))

    if filter_messages:
        reason = ", ".join(filter_messages)
        return f"Lo siento, no puedo procesar tu mensaje porque:\nTu mensaje esta relacionado con: {reason}.\nPor favor, reformula tu mensaje de manera apropiada."
    else:
        return "Estoy teniendo problemas para responder tu pregunta. Por favor, intenta de nuevo, con otras palabras"
