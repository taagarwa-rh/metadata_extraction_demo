import os
from pathlib import Path

import torch
from dotenv import load_dotenv

load_dotenv()

DIRECTORY_PATH = Path(__file__).parent.parent

# LLM Host info
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "xxxxxx")
OPENAI_IGNORE_SSL = os.getenv("OPENAI_IGNORE_SSL", False)

# Docling Host info (Optional)
DOCLING_BASE_URL = os.getenv("DOCLING_BASE_URL", None)
DOCLING_API_KEY = os.getenv("DOCLING_API_KEY", None)

# Tracing (Optional)
TRACELOOP_BASE_URL = os.getenv("TRACELOOP_BASE_URL", None)
TRACELOOP_DISABLE_BATCH = os.getenv("TRACELOOP_DISABLE_BATCH", True)

# Device
DEVICE = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
