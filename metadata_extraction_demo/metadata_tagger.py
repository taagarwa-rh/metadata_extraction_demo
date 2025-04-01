import asyncio
import io
import logging
import time
from enum import Enum
from pathlib import Path
from typing import List, Literal, Union

import yaml
from openai import Client
from openai.types.chat import ParsedChatCompletion
from pydantic import BaseModel, create_model
from tqdm import tqdm

from metadata_extraction_demo.utils import openai_async_client, openai_client

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


def text_to_metadata(
    text: str,
    model: str,
    response_format: BaseModel,
    client: Client = None,
    system_messages: list[dict] = [],
    verbose: bool = False,
    **kwargs,
) -> BaseModel:
    """Extract structured metadata from text."""
    if client is None:
        client = openai_client()
    # Construct and send the request to the LLM
    messages = system_messages + [{"role": "user", "content": text}]
    start = time.time()
    response: ParsedChatCompletion = client.beta.chat.completions.parse(
        messages=messages,
        model=model,
        response_format=response_format,
        # Added for compatibility with vLLM: https://docs.vllm.ai/en/latest/features/structured_outputs.html
        extra_body={"guided_decoding_backend": "outlines"},
        **kwargs,
    )
    if verbose:
        logger.info(f"Generation took {round(time.time() - start, 1)} seconds")
    metadata: BaseModel = response.choices[0].message.parsed
    return metadata


async def atext_to_metadata(
    text: str,
    model: str,
    response_format: BaseModel,
    client: Client = None,
    system_messages: list[dict] = [],
    verbose: bool = False,
    on_error: Literal["raise", "ignore"] = "raise",
    **kwargs,
) -> Union[BaseModel, str]:
    """Extract structured metadata from text asynchronusly."""
    if client is None:
        client = openai_async_client()
    # Construct and send the request to the LLM
    try:
        messages = system_messages + [{"role": "user", "content": text}]
        start = time.time()
        response: ParsedChatCompletion = await client.beta.chat.completions.parse(
            messages=messages,
            model=model,
            response_format=response_format,
            # Added for compatibility with vLLM: https://docs.vllm.ai/en/latest/features/structured_outputs.html
            extra_body={"guided_decoding_backend": "outlines"},
            **kwargs,
        )
        if verbose:
            logger.info(f"Generation took {round(time.time() - start, 1)} seconds")
        metadata: BaseModel = response.choices[0].message.parsed
        return metadata
    except Exception as e:
        logger.error(f"Failed to extract metadata from text: {e}")
        if on_error == "raise":
            raise e
        elif on_error == "ignore":
            return str(e)


async def texts_to_metadata(
    texts: list[str],
    model: str,
    response_format: BaseModel,
    batch_size: int = 4,
    system_messages: list[dict] = [],
    verbose: bool = False,
    on_error: Literal["raise", "ignore"] = "raise",
    **kwargs,
) -> list[Union[BaseModel, str]]:
    """Extract structured metadata multiple texts in parallel (up to batch_size texts at a time)."""
    client = openai_async_client()
    batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
    results = []
    for batch in tqdm(batches, desc="Processing batches through LLM"):
        batch_results = await asyncio.gather(
            *(
                atext_to_metadata(
                    client=client,
                    text=text,
                    model=model,
                    response_format=response_format,
                    system_messages=system_messages,
                    verbose=verbose,
                    on_error=on_error,
                    **kwargs,
                )
                for text in batch
            )
        )
        results.extend(batch_results)
    return results


type_mapper = {
    "string": str,
    "int": int,
    "float": float,
    "bool": bool,
}


def build_model_from_dict(d: str, model_name: str) -> BaseModel:
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


if __name__ == "__main__":
    file = Path("metadata.yaml")
    yaml_string = file.read_text()
    model = build_model_from_yaml(yaml_string)
    print(model.model_json_schema())
