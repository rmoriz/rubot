# Multi-stage build for smaller production image
FROM python:3.13-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Development stage
FROM base as dev
RUN pip install -e ".[dev]"
COPY . .
CMD ["bash"]

# Production stage
FROM base as production

# Install marker-pdf
RUN pip install git+https://github.com/datalab-to/marker.git

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash rubot && \
    chown -R rubot:rubot /app

USER rubot

# Create cache directory
RUN mkdir -p /app/cache

ENTRYPOINT ["python", "-m", "rubot"]