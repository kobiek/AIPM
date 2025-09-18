# Simple Dockerfile for AI Product Manager
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps (build tools for some libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project
COPY ai_product_manager /app/ai_product_manager

# Install dependencies
RUN pip install --upgrade pip \
    && pip install -e /app/ai_product_manager \
    && pip install -r /app/ai_product_manager/requirements.txt

# Artifacts directory
ENV AIPM_ARTIFACTS_DIR=/app/artifacts
RUN mkdir -p ${AIPM_ARTIFACTS_DIR}

# Default command runs Streamlit UI
EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "ai_product_manager/ui/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
