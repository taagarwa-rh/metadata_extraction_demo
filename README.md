# Metadata Extraction Demo

Demo showcasing metadata extraction from PDFs using a combination of Docling and LLMs

## Table of Contents

- [Metadata Extraction Demo](#metadata-extraction-demo)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Initial Steps](#initial-steps)
      - [Option 1. Local Setup](#option-1-local-setup)
      - [Option 2. Local Setup With LLMaaS](#option-2-local-setup-with-llmaas)
      - [Option 3. Local Setup With Remote LLM](#option-3-local-setup-with-remote-llm)
  - [Run the Demo](#run-the-demo)


## Getting Started

### Prerequisites

In order to work on this project, the following tools *must* be installed:

- [`poetry`](https://python-poetry.org/)

### Initial Steps
To begin working on this project:

1. Clone the repository to your local system via `git clone`
2. Change directory to the project `cd metadata_extraction_demo`
3. Make a copy of `sample.env` and rename it as `.env`
4. Choose one of the following paths depending on your environment:

#### Option 1. Local Setup

1. Install the project dependencies `poetry install --only main`
   1. If running on Mac, you can install optional dependencies for Mac with `poetry install --only main,mac`
2. Install [Ollama](https://ollama.com/)
3. Pull a model, e.g. `ollama pull qwen2.5`

#### Option 2. Local Setup With LLMaaS

1. Install the project dependencies `poetry install --only main`
2. Sign up for API keys for Docling and an LLM from [LLMaaS](https://maas.apps.prod.rhoai.rh-aiservices-bu.com/)
3. Add/replace the following environment variables in `.env`:
    ```bash
    OPENAI_BASE_URL="https://maas.example-llm-url.com/v1"
    OPENAI_API_KEY="<KEY>"

    DOCLING_BASE_URL="https://maas.example-docling-url.com"
    DOCLING_API_KEY="<KEY>"
    ```

#### Option 3. Local Setup With Remote LLM

1. Install the project dependencies `poetry install --only main`
   1. If running on Mac, you can install optional dependencies for Mac with `poetry install --only main,mac`
2. Add/replace the following environment variables in `.env`:
    ```bash
    OPENAI_BASE_URL="https://your.example-llm-url.com/v1"
    OPENAI_API_KEY="<KEY>"
    OPENAI_IGNORE_SSL=True # Optional: Disable SSL verification for remote server
    ```

## Run the Demo

To start the demo, run:
```sh
poetry run gradio metadata_extraction_demo/gradio.py
```

You can access the application at [http://localhost:7860](http://localhost:7860).
Once the application is running, you can see usage instructions on the Instructions tab.
You can also see this information in [INSTRUCTIONS.md](./INSTRUCTIONS.md).
