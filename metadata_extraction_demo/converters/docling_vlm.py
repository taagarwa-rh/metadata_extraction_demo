import logging
from pathlib import Path
from typing import List

import torch
from docling_core.types.doc import DoclingDocument
from docling_core.types.doc.document import DocTagsDocument
from PIL.Image import Image
from transformers import AutoModelForVision2Seq, AutoProcessor

from metadata_extraction_demo.converters.base import Converter
from metadata_extraction_demo.converters.utils import convert_pdf_to_images

logger = logging.getLogger(__name__)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def is_mlx():
    """Check if mlx-vlm is available."""
    try:
        import mlx_vlm  # noqa: F401

        return True
    except ImportError:
        return False


class DoclingVLMConverter(Converter):
    """Docling converter using VLMs."""

    def __init__(self, max_new_tokens: int = 8192):
        """Initialize."""
        self.mlx = is_mlx()
        self.model, self.processor, self.config = self.load_model_mlx() if self.mlx else self.load_model()
        self.extractor = self.extract_docling_mlx if self.mlx else self.extract_docling
        self.max_new_tokens = max_new_tokens

    # From: https://huggingface.co/ds4sd/SmolDocling-256M-preview
    def load_model(self):
        """Load a CPU or CUDA based docling VLM."""
        logger.info(f"Loading Docling VLM to {DEVICE}")
        processor = AutoProcessor.from_pretrained("ds4sd/SmolDocling-256M-preview")
        model = AutoModelForVision2Seq.from_pretrained(
            "ds4sd/SmolDocling-256M-preview",
            torch_dtype=torch.bfloat16,
            _attn_implementation="flash_attention_2" if DEVICE == "cuda" else "eager",
        ).to(DEVICE)
        logger.info("Model successfully loaded")
        return model, processor, None

    def load_model_mlx(self):
        """Load an MLX docling VLM."""
        from mlx_vlm import load
        from mlx_vlm.utils import load_config

        logger.info("Loading Docling VLM to MLX")
        model_path = "ds4sd/SmolDocling-256M-preview-mlx-bf16"
        model, processor = load(model_path)
        config = load_config(model_path)
        logger.info("Model successfully loaded")

        return model, processor, config

    def extract_docling(self, model, processor, images: List[Image], **kwargs) -> DoclingDocument:
        """Extract docling using a CPU or CUDA based model."""
        messages = [
            {"role": "user", "content": [{"type": "image"}, {"type": "text", "text": "Convert this page to docling."}]},
        ]

        all_doctags = []
        for image in images:
            # Prepare inputs
            prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
            inputs = processor(text=prompt, images=[image], return_tensors="pt")
            inputs = inputs.to(DEVICE)

            # Generate outputs
            generated_ids = model.generate(**inputs, max_new_tokens=self.max_new_tokens)
            prompt_length = inputs.input_ids.shape[1]
            trimmed_generated_ids = generated_ids[:, prompt_length:]
            doctags = processor.batch_decode(
                trimmed_generated_ids,
                skip_special_tokens=False,
            )[0].lstrip()
            all_doctags.append(doctags)

        # Populate document
        doctags_doc = DocTagsDocument.from_doctags_and_image_pairs(all_doctags, images)
        # create a docling document
        doc = DoclingDocument(name="Document")
        doc.load_from_doctags(doctags_doc)

        return doc

    def extract_docling_mlx(self, model, processor, config, images: list[Image], **kwargs):
        """Extract a docling document using MLX model."""
        from mlx_vlm.prompt_utils import apply_chat_template
        from mlx_vlm.utils import stream_generate

        all_doctags = []
        for image in images:
            prompt = "Convert this page to docling."
            # Apply chat template
            formatted_prompt = apply_chat_template(processor, config, prompt, num_images=1)

            # Generate output
            doctags = ""
            for token in stream_generate(model, processor, formatted_prompt, [image], max_tokens=self.max_new_tokens, verbose=False):
                doctags += token.text
                if "</doctag>" in token.text:
                    break
            all_doctags.append(doctags)

        # Populate document
        doctags_doc = DocTagsDocument.from_doctags_and_image_pairs(all_doctags, images)
        # create a docling document
        doc = DoclingDocument(name="SampleDocument")
        doc.load_from_doctags(doctags_doc)
        return doc

    def convert_to_docling(self, path: Path) -> DoclingDocument:
        """Convert a PDF file to Markdown."""
        images = convert_pdf_to_images(path)

        docling = self.extractor(model=self.model, processor=self.processor, config=self.config, images=images)

        return docling


if __name__ == "__main__":
    path = Path("Sample_Menu.pdf")
    converter = DoclingVLMConverter()
    docling = converter.convert_to_docling(path=path)
    print(docling.export_to_markdown())
