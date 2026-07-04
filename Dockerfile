# Hacktrek WebCrawler API — backend image.
# Build:  docker build -t hacktrek-api .
# Run:    docker run --rm -p 8000:8000 hacktrek-api
FROM python:3.13-slim

# Keep Python lean and predictable inside the container.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install runtime dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code (the api package is the entrypoint module).
COPY api ./api

# Run as a non-root user for safety.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Basic container healthcheck against the API's /health route.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
