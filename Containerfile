# Builder image to install dependencies from pyproject and lock file
FROM python:3.11-slim as builder

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Copy the project into the image
ADD . /app/

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked

#-----------------------------------------------------------------------
# Final image to run the application
FROM python:3.11-slim AS final
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .
EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"

RUN .venv/bin/docling-tools models download

CMD [".venv/bin/gradio", "metadata_extraction_demo/app.py"]