import io
from enum import Enum
from pathlib import Path
from typing import List

import httpx
import yaml
from openai import AsyncClient, Client
from pdf2image import convert_from_bytes
from pydantic import BaseModel, create_model

from metadata_extraction_demo.constants import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_IGNORE_SSL

type_mapper = {
    "str": str,
    "string": str,
    "int": int,
    "integer": int,
    "float": float,
    "bool": bool,
    "boolean": bool,
}


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


def has_mlx_vlm():
    """Check if mlx-vlm is available."""
    try:
        import mlx_vlm  # noqa: F401

        return True
    except ImportError:
        return False


def build_model_from_dict(d: dict, model_name: str) -> BaseModel:
    """Build a Pydantic model from a dictionary."""
    model = {}
    for attribute in d:
        attribute_info = d[attribute]
        if attribute_info["type"] == "object":
            model[attribute] = (build_model_from_dict(attribute_info["properties"], attribute), ...)
        elif attribute_info["type"] == "array":
            if attribute_info["items"] == "object":
                model[attribute] = (List[build_model_from_dict(attribute_info["properties"], attribute + "_item")], ...)
            else:
                model[attribute] = (List[type_mapper[attribute_info["items"]]], ...)  # noqa: F821
        elif attribute_info["type"] == "enum":
            enum_options = {opt.lower().replace(" ", "_"): opt for opt in attribute_info["options"]}
            model[attribute] = (Enum(attribute, enum_options), ...)
        elif attribute_info["type"] in type_mapper:
            model[attribute] = (type_mapper[attribute_info["type"]], ...)
        else:
            raise ValueError(f"Unknown type: {attribute_info['type']}")

    model = create_model(model_name, **model)
    return model


def build_model_from_yaml(string: str):
    """Build a pydantic model from YAML."""
    yaml_dict = yaml.safe_load(io.StringIO(string))
    metadata_model = build_model_from_dict(d=yaml_dict, model_name="Metadata")
    return metadata_model


def convert_pdf_to_images(path: Path, **kwargs) -> List:
    """
    Convert a PDF to an image.

    Args:
    ----
        path (Path): Path to PDF file to convert.
        kwargs: Keyword arguments to pass to `convert_from_bytes`.

    Returns:
    -------
        list[Image]: List of PDF images, one for each page.

    """
    # Convert the PDF to bytes if it isn't already
    pdf = path.read_bytes()

    # Convert the pdf to images
    pdf_images = convert_from_bytes(pdf, **kwargs)

    return pdf_images
