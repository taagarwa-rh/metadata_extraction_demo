from base64 import b64encode
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Union

import requests
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc.document import DoclingDocument

from metadata_extraction_demo.constants import DEVICE, DOCLING_API_KEY, DOCLING_BASE_URL


def has_ocrmac():
    """Check if the system has ocrmac installed."""
    try:
        import ocrmac  # noqa: F401

        return True
    except ImportError:
        return False


def create_document_converter(ocr_options: dict = {}, allowed_formats: list[InputFormat] = None):
    """Create docling document converter."""
    # Set default pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True

    # Add OCR Options
    if DEVICE == "mps" and has_ocrmac():
        from docling.datamodel.pipeline_options import OcrMacOptions

        ocr_options_ = OcrMacOptions(**ocr_options)
    else:
        ocr_options_ = EasyOcrOptions(**ocr_options)
    pipeline_options.ocr_options = ocr_options_

    # Create converter
    format_options = {
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options,
        )
    }
    converter = DocumentConverter(format_options=format_options, allowed_formats=allowed_formats)
    return converter


def convert_pdf_to_docling(path_or_bytes: Union[Path, bytes], ocr_options: dict = {}, debug: bool = False, **kwargs) -> DoclingDocument:
    """Convert a PDF to a Docling document."""
    if debug:
        # Turn on inline debug visualizations:
        settings.debug.visualize_layout = True
        settings.debug.visualize_ocr = True
        settings.debug.visualize_tables = True
        settings.debug.visualize_cells = True

    # Convert the PDF to filepath if it isn't already
    pdf_path = None
    if isinstance(path_or_bytes, Path):
        pdf_path = path_or_bytes
    elif isinstance(path_or_bytes, bytes):
        tmp = NamedTemporaryFile(suffix=".pdf")
        with open(tmp.name, "wb") as f:
            f.write(path_or_bytes)
        pdf_path = Path(tmp.name)

    if pdf_path is None:
        raise TypeError(f"Unsupported type {type(path_or_bytes)} for argument path_or_bytes")

    converter = create_document_converter(ocr_options=ocr_options)
    result = converter.convert(pdf_path, **kwargs)
    return result.document


def convert_pdf_to_markdown(path_or_bytes: Union[Path, bytes], **kwargs) -> str:
    """
    Convert a PDF to markdown.

    Args:
    ----
        path_or_bytes (Union[Path, bytes]): PDF file to convert, either a path or bytes.
        kwargs: Keyword arguments to pass to `docling.document.export_to_markdown`.

    Returns:
    -------
        str: The entire PDF file as a markdown string.

    """
    # Convert to docling
    docling_doc = convert_pdf_to_docling(path_or_bytes=path_or_bytes, **kwargs)

    # Convert to markdown
    markdown = docling_doc.export_to_markdown()
    return markdown


def convert_pdf_docling_server(
    path_or_bytes: Union[Path, bytes], base_url: str, api_key: str = None, ocr_options: dict = {}, **kwargs
) -> str:
    """Convert a PDF to markdown using the Docling server."""
    if isinstance(path_or_bytes, Path):
        bytes = path_or_bytes.read_bytes()
    else:
        bytes = path_or_bytes
    b64_encoded_bytes = b64encode(bytes).decode()
    json_body = {"options": ocr_options, "file_sources": [{"base64_string": b64_encoded_bytes, "filename": "pdf-to-convert.pdf"}]}
    url = base_url + "/v1alpha/convert/source"
    response = requests.post(url, json=json_body, headers={"Authorization": f"Bearer {api_key}"})
    response.raise_for_status()
    if response.json()["status"] != "success":
        raise Exception(f"Conversion failed with status {response.json()['status']}, errors {response.json()['errors']}")
    text = response.json()["document"]["md_content"]
    return text


def convert_pdf_to_text(pdf_path: str, force_full_page_ocr: bool = False):
    """Convert a PDF to text using either remote or local Docling."""
    # Use remote docling if it's available
    if DOCLING_BASE_URL is not None:
        ocr_options = {"force_ocr": force_full_page_ocr, "to_formats": ["md"], "image_export_mode": "placeholder"}
        text = convert_pdf_docling_server(
            path_or_bytes=Path(pdf_path), base_url=DOCLING_BASE_URL, api_key=DOCLING_API_KEY, ocr_options=ocr_options
        )
    # Otherwise use local docling
    else:
        ocr_options = {"force_full_page_ocr": force_full_page_ocr}
        text = convert_pdf_to_markdown(Path(pdf_path), ocr_options=ocr_options)
    return text
