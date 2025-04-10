from base64 import b64encode
from pathlib import Path

import requests
from docling_core.types.doc.document import DocTagsDocument

from metadata_extraction_demo.converters.base import Converter
from metadata_extraction_demo.converters.utils import convert_pdf_to_images


class DoclingServerConverter(Converter):
    """Docling converter using docling-serve server."""

    def __init__(self, base_url: str, api_key: str = None, addtl_ocr_options={}):
        """Initialize."""
        self.base_url = base_url
        self.api_key = api_key
        self.addtl_ocr_options = addtl_ocr_options

    def convert_to_docling(self, path: Path) -> DocTagsDocument:
        """Convert a PDF to markdown using the Docling server."""
        # Convert file to bytes
        bytes = path.read_bytes()
        b64_encoded_bytes = b64encode(bytes).decode()

        # Build request
        ocr_options = self.addtl_ocr_options | {"to_formats": "doctags"}
        json_body = {"options": ocr_options, "file_sources": [{"base64_string": b64_encoded_bytes, "filename": "pdf-to-convert.pdf"}]}
        url = self.base_url + "/v1alpha/convert/source"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key is not None else {}

        # Send the request
        response = requests.post(url, json=json_body, headers=headers)
        response.raise_for_status()
        if response.json()["status"] != "success":
            raise Exception(f"Conversion failed with status {response.json()['status']}, errors {response.json()['errors']}")

        # Extract the doctags
        doctags = response.json()["document"]["doctags_content"]

        # Create the docling document
        images = convert_pdf_to_images(path=path)
        docling = DocTagsDocument.from_doctags_and_image_pairs([doctags], [images])
        return docling
