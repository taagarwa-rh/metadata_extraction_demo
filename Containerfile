# Builder image to install dependencies from pyproject and lock file
FROM python:3.11-slim AS builder
WORKDIR /app/
RUN pip install poetry
COPY . .
RUN poetry config virtualenvs.in-project true
RUN poetry install --only main

#-----------------------------------------------------------------------
# Final image to run the application
FROM python:3.11-slim AS final
WORKDIR /app/
COPY --from=builder /app/.venv /app/.venv
COPY . .
EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"

RUN .venv/bin/docling-tools models download

CMD [".venv/bin/gradio", "metadata_extraction_demo/app.py"]