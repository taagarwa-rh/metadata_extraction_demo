from pathlib import Path
from typing import List

from pdf2image import convert_from_bytes


def convert_pdf_to_images(path: Path, **kwargs) -> List:
    """
    Convert a PDF to an image.

    Args:
    ----
        path (Path): Path to PDF file to convert.
        kwargs: Keyword arguments to pass to `convert_from_bytes`.

    Returns:
    -------
        list[Image]: List of PDF images, one for each page.

    """
    # Convert the PDF to bytes if it isn't already
    pdf = path.read_bytes()

    # Convert the pdf to images
    pdf_images = convert_from_bytes(pdf, **kwargs)

    return pdf_images
