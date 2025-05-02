import httpx
from openai import AsyncClient, Client

from metadata_extraction_demo.constants import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_IGNORE_SSL


def openai_client():
    """Create an OpenAI client."""
    verify = False if OPENAI_IGNORE_SSL else True
    http_client = httpx.Client(verify=verify, timeout=600)
    client = Client(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, http_client=http_client, timeout=600)
    return client


def openai_async_client():
    """Create an OpenAI client."""
    verify = False if OPENAI_IGNORE_SSL else True
    http_client = httpx.AsyncClient(verify=verify, timeout=600)
    client = AsyncClient(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, http_client=http_client, timeout=600)
    return client


def get_models():
    """Get available models on the OpenAI client."""
    client = openai_client()
    response = client.models.list()
    models = [model.id for model in response.data]
    return sorted(models)


def has_ocrmac():
    """Check if the system has ocrmac installed."""
    try:
        import ocrmac  # noqa: F401

        return True
    except ImportError:
        return False
