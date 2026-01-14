FROM python:3.13-slim
# Add uv to our image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin

WORKDIR /code
# Add our venv to path
ENV PATH="/code/.venv/bin:$PATH"

# Copy our dependency files and install them
COPY pyproject.toml .python-version uv.lock ./
RUN uv sync --locked

COPY 01-docker-terraform/pipeline.py .

ENV PROGRESS=enlighten

ENTRYPOINT ["python", "pipeline.py" ]