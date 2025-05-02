import logging

import gradio as gr
from gradio_pdf import PDF
from difflib import Differ

from metadata_extraction_demo.constants import DIRECTORY_PATH, DOCLING_BASE_URL
from metadata_extraction_demo.convert import convert_pdf_to_text
from metadata_extraction_demo.metadata_tagger import build_model_from_yaml, text_to_metadata
from metadata_extraction_demo.utils import get_models, has_ocrmac

logfile = DIRECTORY_PATH / "logfile.txt"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

INSTRUCTIONS = (DIRECTORY_PATH / "Instructions.md").read_text().strip()
DEFAULT_METADATA = (DIRECTORY_PATH / "metadata.yaml").read_text().strip()
DEFAULT_METADATA_NUM_LINES = len(DEFAULT_METADATA.splitlines())
DEFAULT_PDF_PATH = str(DIRECTORY_PATH / "Sample_Contract.pdf")
DEFAULT_MODELS = get_models()
AVAILABLE_OCR_METHODS = ["EasyOCR"]
AVAILABLE_OCR_METHODS += ["OCRMac"] if has_ocrmac() else []
AVAILABLE_OCR_METHODS += ["Server"] if DOCLING_BASE_URL is not None else []
AVAILABLE_OCR_METHODS += ["VLM"]


def process_pdf(pdf_file, llm_name: str, method: str, system_prompt: str, force_full_page_ocr: str, yaml_string: str):
    """Process the PDF."""
    response_format = build_model_from_yaml(yaml_string)
    logger.info("Converting PDF to text")
    pdf_text = convert_pdf_to_text(pdf_path=pdf_file, method=method.lower(), force_full_page_ocr=force_full_page_ocr == "Yes")
    logger.info("Converting text to metadata")
    system_messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
    metadata = text_to_metadata(
        text=pdf_text, model=llm_name, response_format=response_format, system_messages=system_messages, temperature=0, seed=42
    )
    logger.info("DONE")
    return metadata.model_dump_json(indent=2), pdf_text


def compare_ocr_methods(pdf_file, method_1: str, method_2: str, force_full_page_ocr_1: str, force_full_page_ocr_2: str):
    logger.info("Converting PDF to text")
    pdf_text_1 = convert_pdf_to_text(pdf_path=pdf_file, method=method_1.lower(), force_full_page_ocr=force_full_page_ocr_1 == "Yes")
    pdf_text_2 = convert_pdf_to_text(pdf_path=pdf_file, method=method_2.lower(), force_full_page_ocr=force_full_page_ocr_2 == "Yes")
    return pdf_text_1, pdf_text_2, gr.HighlightedText(visible=False)

def make_diffs(pdf_text_1, pdf_text_2):
    logger.info("Making diffs")
    d = Differ()
    diffs_12 = [(token[2:], token[0] if token[0] != " " else None) for token in d.compare(pdf_text_1, pdf_text_2)]
    highlighted_text_12 = gr.HighlightedText(value=diffs_12, label="Diff", combine_adjacent=True, show_legend=True, color_map={"+": "blue", "-": "green"}, visible=True)
    return highlighted_text_12

def view_pdf(pdf_file):
    """View the PDF."""
    return PDF(value=pdf_file)


theme = gr.themes.Base(
    primary_hue="red",
)

with gr.Blocks(theme=theme) as demo:
    gr.Markdown("# Metadata Extraction Demo")
    gr.Markdown("Extract structured data from a PDF using AI.")
    with gr.Tab("Instructions"):
        gr.Markdown(INSTRUCTIONS)
    with gr.Tab("Upload PDF"):
        with gr.Column():
            pdf_file = gr.File(label="Upload PDF", file_types=[".pdf"], file_count="single", value=DEFAULT_PDF_PATH)
            pdf_viewer = PDF(label="PDF Preview", value=DEFAULT_PDF_PATH)
    with gr.Tab("Configuration"):
        with gr.Row():
            llm = gr.Dropdown(label="Extraction Model", choices=DEFAULT_MODELS, interactive=True)
            ocr_method = gr.Radio(label="OCR Method", choices=AVAILABLE_OCR_METHODS, value="EasyOCR", interactive=True)
            force_full_page_ocr = gr.Radio(label="Force Full Page OCR?", choices=["Yes", "No"], value="No")
        with gr.Row(equal_height=True):
            metadata_structure = gr.Code(
                label="Metadata Structure", language="yaml", interactive=True, value=DEFAULT_METADATA, max_lines=25,
            )
            system_prompt = gr.TextArea(label="System Prompt (Optional)", value="", interactive=True)
    with gr.Tab("Metadata Extractor"):
        extract_button = gr.Button("Extract Text + Metadata", variant="primary")
        with gr.Row(equal_height=True):
            extracted_text = gr.Markdown(label="Extracted Text", show_label=True, container=True, max_height=750, show_copy_button=True)
            extracted_metadata = gr.Code(label="Extracted Metadata", language="json", wrap_lines=True)
                
    with gr.Tab("Compare OCR Methods"):
        with gr.Row(equal_height=True):
            with gr.Column():
                ocr_method_1 = gr.Radio(label="OCR Method", choices=AVAILABLE_OCR_METHODS, value="EasyOCR", interactive=True)
                force_full_page_ocr_1 = gr.Radio(label="Force Full Page OCR?", choices=["Yes", "No"], value="No")
            with gr.Column():
                ocr_method_2 = gr.Radio(label="OCR Method", choices=AVAILABLE_OCR_METHODS, value="EasyOCR", interactive=True)
                force_full_page_ocr_2 = gr.Radio(label="Force Full Page OCR?", choices=["Yes", "No"], value="No")
        with gr.Row():
            compare_ocr_button = gr.Button("Extract Text", variant="primary")
        with gr.Row(height=750, equal_height=True):
            with gr.Column():
                extracted_text_1 = gr.Markdown(label="Extracted Text", show_label=True, container=True, max_height=750, show_copy_button=True)
            with gr.Column():
                extracted_text_2 = gr.Markdown(label="Extracted Text", show_label=True, container=True, max_height=750, show_copy_button=True)
        with gr.Row():
            show_diffs_button = gr.Button("Show Differences", variant="secondary")
        with gr.Row():
            differences = gr.HighlightedText(visible=False)

    pdf_file.change(fn=view_pdf, inputs=[pdf_file], outputs=[pdf_viewer])
    extract_button.click(
        fn=process_pdf,
        inputs=[pdf_file, llm, ocr_method, system_prompt, force_full_page_ocr, metadata_structure],
        outputs=[extracted_metadata, extracted_text],
    )
    compare_ocr_button.click(
        fn=compare_ocr_methods,
        inputs=[pdf_file, ocr_method_1, ocr_method_2, force_full_page_ocr_1, force_full_page_ocr_2],
        outputs=[extracted_text_1, extracted_text_2, differences],
    )
    show_diffs_button.click(
        fn=make_diffs,
        inputs=[extracted_text_1, extracted_text_2],
        outputs=[differences],
    )

demo.launch()
