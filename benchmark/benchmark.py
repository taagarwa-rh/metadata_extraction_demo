import argparse
import logging
import tempfile
from pathlib import Path

import yaml
from datasets import load_dataset
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
from PIL.Image import Image
from pydantic import BaseModel
from traceloop.sdk import Traceloop

from metadata_extraction_demo.convert import build_document_converter
from metadata_extraction_demo.pipeline import MetadataExtractionPipeline
from metadata_extraction_demo.utils import build_model_from_dict

logger = logging.getLogger(__name__)


class DocumentConverterConfig(BaseModel):
    ocr_method: str
    force_full_page_ocr: bool = False


class LLMConfig(BaseModel):
    model: str
    system_prompt: str = None


class BenchmarkConfig(BaseModel):

    document_converter: DocumentConverterConfig
    llm: LLMConfig


def load_data():
    ds = load_dataset("lmms-lab/DocVQA", "DocVQA", split="validation")
    question_types = ["form", "free_text", "table/list"]
    ds = ds.filter(lambda x: any(q in x["question_types"] for q in question_types))
    return ds


def score_pred(prediction: str, answers: list[str]):
    print(prediction)
    print(answers)
    return 1 if prediction in answers else 0


def evaluate_one(test: dict, converter: DocumentConverter, model: str, system_prompt: str = None):
    # Get test elements
    image: Image = test["image"]
    question: str = test["question"]
    answers: list[str] = test["answers"]

    # Build the response model
    response_dict = {question: {"type": "string"}}
    response_format = build_model_from_dict(response_dict, "ResponseFormat")

    # Construct the metadata extraction pipeline
    pipeline = MetadataExtractionPipeline(
        converter=converter,
        model=model,
        response_format=response_format,
        system_prompt=system_prompt,
    )

    # Extract the requested info
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        image.save(tmp.name)
        response_model, _ = pipeline.extract(tmp.name)

    # Get the prediction
    prediction = response_model.model_dump()[question]

    # Score the prediction
    score = score_pred(prediction, answers)

    return score


def parse_args() -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    config_path = args.config
    with open(config_path) as f:
        config_dict = yaml.safe_load(f)
    return config_dict


def main():
    # Load the config
    config_dict = parse_args()
    config = BenchmarkConfig(**config_dict)

    # Load the dataset
    ds = load_data()

    converter = build_document_converter(
        method=config.document_converter.ocr_method, force_full_page_ocr=config.document_converter.force_full_page_ocr
    )
    # scores = ds.map(lambda x: evaluate_one(x, converter=converter, model=config.llm.model, system_prompt=config.llm.system_prompt))
    # print(scores)

    load_dotenv()
    Traceloop.init()
    for test in ds:
        score = evaluate_one(test, converter=converter, model=config.llm.model, system_prompt=config.llm.system_prompt)
        print(test)
        print(score)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    main()
