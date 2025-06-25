# --- 1. Builder Stage ---
# This stage installs dependencies using Poetry and creates a virtual environment.
FROM python:3.13-slim as builder

# Set the working directory
WORKDIR /app

# Install a specific, stable version of Poetry
RUN pip install poetry

# Copy only the files needed to install dependencies
# This leverages Docker's layer caching. The layer will only be rebuilt
# if these files change.
COPY poetry.lock pyproject.toml ./

# Install dependencies into a virtual environment
# We are installing all dependencies for now to ensure the build passes.
# --no-root: Don't install the project itself, just the dependencies
RUN poetry install --no-root

# --- 2. Final Stage ---
# This stage creates the final, lean production image.
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Set the PATH to include the virtual environment's binaries
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application source code
COPY src/ ./src/

# EXPOSE 8000
# We will uncomment this later when we have an API to run.

# CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
# We will define the command to run the API server once we create it. 