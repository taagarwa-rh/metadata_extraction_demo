from pathlib import Path

from docling_core.types.doc.document import DoclingDocument, DocTagsDocument

from metadata_extraction_demo.constants import DOCLING_API_KEY, DOCLING_BASE_URL
from metadata_extraction_demo.converters import DoclingLocalConverter, DoclingServerConverter


def convert_pdf_to_docling(pdf_path: str, method: str, force_full_page_ocr: bool = False) -> DoclingDocument | DocTagsDocument | None:
    """Convert a PDF to a docling document."""
    path = Path(pdf_path)

    if method == "server":
        addtl_ocr_options = {"force_ocr": force_full_page_ocr, "image_export_mode": "placeholder"}
        converter = DoclingServerConverter(base_url=DOCLING_BASE_URL, api_key=DOCLING_API_KEY, addtl_ocr_options=addtl_ocr_options)
        docling = converter.convert_to_docling(path)

    elif method in ["easyocr", "ocrmac", "vlm"]:
        ocr_options = {"force_full_page_ocr": force_full_page_ocr}
        converter = DoclingLocalConverter(ocr_engine=method, ocr_options=ocr_options)
        docling = converter.convert_to_docling(path)

    else:
        raise ValueError(f"Unsupported conversion method: {method}")

    return docling


def convert_pdf_to_text(pdf_path: str, method: str, force_full_page_ocr: bool = False):
    """Convert a PDF to Markdown text."""
    # Convert file to docling
    docling = convert_pdf_to_docling(pdf_path, method, force_full_page_ocr)
    # Convert docling to text
    text = docling.export_to_markdown()
    return text
