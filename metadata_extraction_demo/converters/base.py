from pathlib import Path


class Converter:
    """Base class for converters."""

    def __init__(self, *args, **kwargs):
        """Initialize."""
        pass

    def convert_to_docling(self, path: Path, *args, **kwargs):
        """Convert a PDF to docling."""
        pass
