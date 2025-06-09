import logging

from docling.datamodel.document import ConversionResult
from docling.document_converter import DocumentConverter
from openai import Client
from openai.types.chat import ParsedChatCompletion
from pydantic import BaseModel

from metadata_extraction_demo.utils import openai_client

logger = logging.getLogger(__name__)


class MetadataExtractionPipeline:
    """Pipeline class for metadata extraction from files."""

    def __init__(
        self, converter: DocumentConverter, model: str, response_format: BaseModel, system_prompt: str = None, client: Client = None
    ):
        """Initialize."""
        self.converter = converter
        self.model = model
        self.response_format = response_format
        self.system_prompt = system_prompt
        self.client = openai_client() if client is None else client

    def path_to_text(self, path: str, **kwargs):
        """Convert a file to text using the converter."""
        logger.info("Converting file to text")
        conversion_result: ConversionResult = self.converter.convert(path, **kwargs)
        text = conversion_result.document.export_to_markdown()
        return text

    def text_to_metadata(
        self,
        text: str,
        **kwargs,
    ) -> BaseModel:
        """Extract structured metadata from text."""
        logger.info("Converting text to metadata")
        # Construct and send the request to the LLM
        system_messages = [{"role": "system", "content": self.system_prompt}] if self.system_prompt else []
        messages = system_messages + [{"role": "user", "content": text}]
        response: ParsedChatCompletion = self.client.beta.chat.completions.parse(
            messages=messages,
            model=self.model,
            response_format=self.response_format,
            # Added for compatibility with vLLM: https://docs.vllm.ai/en/latest/features/structured_outputs.html
            extra_body={"guided_decoding_backend": "outlines"},
            **kwargs,
        )
        metadata: BaseModel = response.choices[0].message.parsed
        return metadata

    def extract(self, path: str, convert_kwargs: dict = {}, llm_kwargs: dict = {}):
        """Execute the pipeline."""
        # Extract text
        text = self.path_to_text(path=path, **convert_kwargs)

        # Extract metadata
        metadata = self.text_to_metadata(text=text, **llm_kwargs)
        return metadata, text
