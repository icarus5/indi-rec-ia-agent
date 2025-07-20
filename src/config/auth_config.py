import os

def get_env_var(name):
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Environment variable `{name}` is not set or is empty")
    return value

class AuthEnvConfig:
    AUTH_API_URL = get_env_var("AUTH_API_URL")
    AUTH_API_CODE = get_env_var("AUTH_API_CODE")
