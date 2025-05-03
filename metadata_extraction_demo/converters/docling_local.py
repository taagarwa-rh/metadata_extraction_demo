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

from metadata_extraction_demo.converters.base import Converter

logger = logging.getLogger(__name__)


def is_mlx():
    """Check if mlx-vlm is available."""
    try:
        import mlx_vlm  # noqa: F401

        return True
    except ImportError:
        return False


class DoclingLocalConverter(Converter):
    """Docling converter using local docling package."""

    def __init__(self, ocr_engine: Literal["easyocr", "ocrmac", "vlm"], ocr_options: dict = {}):
        """Initialize."""
        self.ocr_engine = ocr_engine
        self.ocr_options = ocr_options
        self.converter: DocumentConverter = self.create_document_converter(ocr_engine=self.ocr_engine, ocr_options=self.ocr_options)

    def create_document_converter(
        self, ocr_engine: Literal["easyocr", "ocrmac", "vlm"], ocr_options: dict = {}, allowed_formats: list[InputFormat] = None
    ) -> DocumentConverter:
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
            pipeline_options = VlmPipelineOptions()
            pipeline_options.force_backend_text = False
            if is_mlx():
                logger.info("Loading model to MLX")
                pipeline_options.vlm_options = smoldocling_vlm_mlx_conversion_options
                pipeline_cls = VlmPipeline
            else:
                logger.info("Loading model to CPU")
                pipeline_options.vlm_options = smoldocling_vlm_conversion_options
                pipeline_cls = VlmPipeline
        else:
            raise ValueError(f"Unsupported OCR engine: {ocr_engine}")

        # Create converter
        format_options = {
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=pipeline_cls,
                pipeline_options=pipeline_options,
            )
        }
        converter = DocumentConverter(format_options=format_options, allowed_formats=allowed_formats)
        return converter

    def convert_to_docling(self, path: Path, **kwargs) -> DoclingDocument:
        """Convert a PDF to a Docling document."""
        result = self.converter.convert(path, **kwargs)
        return result.document
