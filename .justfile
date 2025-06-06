default_version := `poetry version -s`
project_name := "metadata_extraction_demo"

_default:
    @ just --list

# Run recipes for MR approval
pre-mr: format lint

# Formats Code
format:
    poetry run ruff check --select I --fix metadata_extraction_demo 
    poetry run ruff format metadata_extraction_demo 

# Tests Code
# test *options:
#     poetry run pytest -s tests/ {{ options }}

# Lints Code
lint *options:
    poetry run ruff check metadata_extraction_demo  {{ options }}

# Increments the code version
bump type:
    poetry run bump2version --current-version={{ default_version }} {{ type }}

test-container: (build-image "testing-latest")
    - podman run --rm \
        -p 7860:7860 \
        -e OPENAI_BASE_URL=http://host.docker.internal:11434/v1 \
        --name metadata-extraction-demo \
        -it metadata-extraction-demo:testing-latest


# Deploy application to openshift - WILL BE DEPRECATED IN A FUTURE RELEASE
oc-deploy env:
    oc apply -k oc-templates/{{ env }}

# DEPRECATED - WILL BE REMOVED - Run the openshift build
oc-build-tag version=("v" + default_version):
    oc start-build -n sandbox-ssa-gfa -w metadata-extraction-demo
    oc tag -n sandbox-ssa-gfa metadata-extraction-demo:latest metadata-extraction-demo:{{ version }}

[private]
build-image tag:
    podman build -t metadata-extraction-demo:{{ tag }} .