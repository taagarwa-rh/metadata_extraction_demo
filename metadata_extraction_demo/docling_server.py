from base64 import b64encode
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from docling.datamodel.base_models import ConversionStatus
from docling.document_converter import DocumentConverter
from docling_core.types.doc.document import DoclingDocument, DocTagsDocument
from pydantic import BaseModel
from PyPDF2 import PdfReader, PdfWriter

from metadata_extraction_demo.utils import convert_pdf_to_images


class PseudoConversionResult(BaseModel):
    """Pseudo-class to imitate ConversionResult."""

    document: DoclingDocument
    status: ConversionStatus = ConversionStatus.SUCCESS


class DoclingServerConverter(DocumentConverter):
    """Docling converter using docling-serve server."""

    def __init__(self, base_url: str, api_key: str = None, addtl_ocr_options={}):
        """Initialize."""
        self.base_url = base_url
        self.api_key = api_key
        self.addtl_ocr_options = addtl_ocr_options

    def convert(self, path: Path, **kwargs) -> DoclingDocument:
        """Convert a PDF to markdown using the Docling server."""
        # Convert file to bytes
        pdf_obj = open(path, "rb")
        pdf = PdfReader(pdf_obj)
        all_doctags = []
        for page in pdf.pages:
            page_pdf = PdfWriter()
            page_pdf.add_page(page)
            tmp = NamedTemporaryFile(suffix=".pdf")
            with open(tmp.name, "wb") as f:
                page_pdf.write(f)

            # Convert bytes to base64 string
            with open(tmp.name, "rb") as f:
                b64_encoded_bytes = b64encode(f.read()).decode()

            # Build request
            ocr_options = self.addtl_ocr_options | {"to_formats": ["doctags"]}
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
            all_doctags.append(doctags)

        # Create the doctags document
        images = convert_pdf_to_images(path=path)
        doctags_doc = DocTagsDocument.from_doctags_and_image_pairs(all_doctags, images)

        # Create a docling document
        docling = DoclingDocument(name=path.name)
        docling.load_from_doctags(doctags_doc)

        # Create a pseudo conversion result
        conversion_result = PseudoConversionResult(document=docling)

        return conversion_result
