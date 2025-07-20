import os


def get_env_var(name):
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Environment variable `{name}` is not set or is empty")
    return value

class AirtableEnvConfig:
    AIRTABLE_API_KEY = get_env_var("AIRTABLE_API_KEY")
    AIRTABLE_BASE_ID = get_env_var("AIRTABLE_BASE_ID")
    AIRTABLE_TABLE_COLLECTIONS = get_env_var("AIRTABLE_TABLE_COLLECTIONS")
    AIRTABLE_TABLE_CLIENTS = get_env_var("AIRTABLE_TABLE_CLIENTS")
    AIRTABLE_TABLE_USERS = get_env_var("AIRTABLE_TABLE_USERS")
