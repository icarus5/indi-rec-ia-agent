import os
import urllib.parse


def build_url_with_optional_param(base_url: str, param_name: str, env_var: str, is_first_param: bool = True) -> str:
    """
    Construye una URL con un parámetro opcional basado en una variable de entorno.

    :param base_url: La URL base.
    :param param_name: El nombre del parámetro a agregar.
    :param env_var: El nombre de la variable de entorno que contiene el valor del parámetro.
    :param is_first_param: Indica si este es el primer parámetro en la URL.
    :return: La URL construida.
    """
    param_value = os.getenv(env_var)
    if param_value:
        separator = "?" if is_first_param else "&"
        return f"{base_url}{separator}{param_name}={param_value}"
    return base_url


def build_dynamic_url(base_url: str, path_template: str, path_vars: dict = None, query_params: dict = None) -> str:
    if path_vars:
        for key, value in path_vars.items():
            safe_value = urllib.parse.quote(str(value), safe='')
            path_template = path_template.replace(f":{key}", safe_value)
    url = f"{base_url.rstrip('/')}/{path_template.lstrip('/')}"

    if query_params:
        safe_params = {k: v for k, v in query_params.items() if v is not None}
        url += "?" + urllib.parse.urlencode(safe_params, safe='')
    return url
