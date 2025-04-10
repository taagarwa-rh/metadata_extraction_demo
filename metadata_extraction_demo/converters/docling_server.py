from base64 import b64encode
from pathlib import Path

import requests
from docling_core.types.doc.document import DocTagsDocument, DoclingDocument
from PyPDF2 import PdfReader, PdfWriter
from tempfile import NamedTemporaryFile

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
        pdf_obj = open(path, 'rb')
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
        docling = DoclingDocument(name="SampleDocument")
        docling.load_from_doctags(doctags_doc)
        
        return docling

if __name__ == "__main__":
    from metadata_extraction_demo.constants import DOCLING_API_KEY, DOCLING_BASE_URL
    path = Path("Sample_Contract.pdf")
    addtl_ocr_options = {"force_ocr": True, "image_export_mode": "placeholder"}
    converter = DoclingServerConverter(
        base_url=DOCLING_BASE_URL,
        api_key=DOCLING_API_KEY,
        addtl_ocr_options=addtl_ocr_options,
    )
    docling = converter.convert_to_docling(path=path)
    print(docling.export_to_markdown())