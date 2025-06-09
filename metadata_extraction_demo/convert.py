import logging
from pathlib import Path
from typing import Literal

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    EasyOcrOptions,
    PdfPipelineOptions,
    VlmPipelineOptions,
    smoldocling_vlm_conversion_options,
    smoldocling_vlm_mlx_conversion_options,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling_core.types.doc.document import DoclingDocument

from metadata_extraction_demo.constants import DOCLING_API_KEY, DOCLING_BASE_URL
from metadata_extraction_demo.docling_server import DoclingServerConverter
from metadata_extraction_demo.utils import has_mlx_vlm

logger = logging.getLogger(__name__)


def build_local_docling_converter(
    ocr_engine: Literal["easyocr", "ocrmac", "vlm"], ocr_options: dict = {}, allowed_formats: list[InputFormat] = None
):
    """Create docling document converter."""
    # Set default pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_cls = StandardPdfPipeline

    # Add OCR Options
    if ocr_engine == "ocrmac":
        from docling.datamodel.pipeline_options import OcrMacOptions

        pipeline_options.ocr_options = OcrMacOptions(**ocr_options)
    elif ocr_engine == "easyocr":
        pipeline_options.ocr_options = EasyOcrOptions(**ocr_options)
    elif ocr_engine == "vlm":
        pipeline_cls = VlmPipeline
        pipeline_options = VlmPipelineOptions()
        pipeline_options.force_backend_text = False
        if has_mlx_vlm():
            logger.info("Loading model to MLX")
            pipeline_options.vlm_options = smoldocling_vlm_mlx_conversion_options
        else:
            logger.info("Loading model to CPU")
            pipeline_options.vlm_options = smoldocling_vlm_conversion_options
    else:
        raise ValueError(f"Unsupported OCR engine: {ocr_engine}")

    # Create converter
    format_options = {
        InputFormat.PDF: PdfFormatOption(
            pipeline_cls=pipeline_cls,
            pipeline_options=pipeline_options,
        )
    }
    converter = DocumentConverter(
        format_options=format_options,
        allowed_formats=[
            InputFormat.PDF,
            InputFormat.IMAGE,
            InputFormat.DOCX,
            InputFormat.HTML,
            InputFormat.PPTX,
            InputFormat.ASCIIDOC,
            InputFormat.CSV,
            InputFormat.MD,
        ],
    )
    return converter


def build_document_converter(method: str, force_full_page_ocr: bool = False) -> DocumentConverter:
    """Build the Docling document converter."""
    if method == "server":
        addtl_ocr_options = {"force_ocr": force_full_page_ocr, "image_export_mode": "placeholder"}
        converter = DoclingServerConverter(base_url=DOCLING_BASE_URL, api_key=DOCLING_API_KEY, addtl_ocr_options=addtl_ocr_options)

    elif method in ["easyocr", "ocrmac", "vlm"]:
        ocr_options = {"force_full_page_ocr": force_full_page_ocr}
        converter = build_local_docling_converter(ocr_engine=method, ocr_options=ocr_options)

    else:
        raise ValueError(f"Unsupported conversion method: {method}")

    return converter


def convert_pdf_to_docling(pdf_path: str, method: str, force_full_page_ocr: bool = False) -> DoclingDocument:
    """Convert a PDF to a docling document."""
    path = Path(pdf_path)
    converter = build_document_converter(method=method, force_full_page_ocr=force_full_page_ocr)
    conversion_result = converter.convert(path)
    docling = conversion_result.document

    return docling


def convert_pdf_to_text(pdf_path: str, method: str, force_full_page_ocr: bool = False):
    """Convert a PDF to Markdown text."""
    # Convert file to docling
    docling = convert_pdf_to_docling(pdf_path, method, force_full_page_ocr)
    # Convert docling to text
    text = docling.export_to_markdown()
    return text
