# Build stage for development dependencies
FROM python:3.13-slim AS base

# Install system dependencies for Docling
RUN apt-get update && apt-get install -y \
    # Essential for building Python packages
    gcc g++ \
    # Tesseract OCR with German language support
    tesseract-ocr tesseract-ocr-deu \
    && rm -rf /var/lib/apt/lists/*

# Set Tesseract data path
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy and install application
COPY . /app
RUN pip install --no-cache-dir -e .

# Pre-download models for both EasyOCR and Tesseract support
RUN mkdir -p /app/models && \
    HF_HOME=/app/models TORCH_HOME=/app/models \
    echo "Pre-downloading models for both EasyOCR and Tesseract support..." && \
    echo "Downloading EasyOCR models..." && \
    docling-tools models download easyocr --output-dir /app/models && \
    echo "Moving EasyOCR models to expected location..." && \
    mkdir -p /root/.EasyOCR/model && \
    mv /app/models/EasyOcr/* /root/.EasyOCR/model/ && \
    rmdir /app/models/EasyOcr && \
    echo "Downloading layout models..." && \
    docling-tools models download layout --output-dir /app/models && \
    echo "Both EasyOCR and Tesseract OCR engines are now available" && \
    echo "Use DOCLING_OCR_ENGINE environment variable to choose at runtime"

# Create cache directory
RUN mkdir -p /app/cache

# Production stage
FROM base AS production

# Set model cache environment variables
ENV HF_HOME=/app/models
ENV TORCH_HOME=/app/models
ENV DOCLING_MODEL_CACHE_DIR=/app/models
ENV CACHE_ROOT=/app/cache
ENV PYTHONWARNINGS=ignore::UserWarning

ENTRYPOINT ["python", "-m", "rubot"]