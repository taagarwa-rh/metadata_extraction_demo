from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc.document import DoclingDocument

from metadata_extraction_demo.constants import DEVICE
from metadata_extraction_demo.converters.base import Converter


def has_ocrmac():
    """Check if the system has ocrmac installed."""
    try:
        import ocrmac  # noqa: F401

        return True
    except ImportError:
        return False


class DoclingLocalConverter(Converter):
    """Docling converter using local docling package."""

    def __init__(self, ocr_options: dict):
        """Initialize."""
        self.converter: DocumentConverter = self.create_document_converter(ocr_options=ocr_options)

    def create_document_converter(self, ocr_options: dict = {}, allowed_formats: list[InputFormat] = None) -> DocumentConverter:
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

    def convert_to_docling(self, path: Path, **kwargs) -> DoclingDocument:
        """Convert a PDF to a Docling document."""
        result = self.converter.convert(path, **kwargs)
        return result.document
