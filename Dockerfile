FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/pyproject.toml backend/README.md ./
RUN pip install --no-cache-dir '.[inference]'
COPY backend/ ./
RUN useradd --create-home --uid 10001 app && mkdir -p /data /cache && chown -R app:app /data /cache
USER app
ENV DATA_DIR=/data HF_HOME=/cache/huggingface API_PORT=7102
EXPOSE 7102
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7102/ready',timeout=3)"
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${API_PORT}"]
