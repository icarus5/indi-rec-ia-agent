import os
from langchain_openai import AzureChatOpenAI

def get_model_for_image():
    return AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_IMAGE"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION_IMAGE"),
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=1,
        model=os.getenv("AZURE_OPENAI_MODEL_IMAGE"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT_IMAGE"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY_IMAGE"),
    )


def get_model():
    return AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=1,
        model=os.getenv("AZURE_OPENAI_MODEL"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )
