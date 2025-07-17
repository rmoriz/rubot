# Multi-stage build for optimized production image
FROM python:3.13-slim AS builder

# Install build dependencies in builder stage
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    python3-dev \
    libopenblas-dev \
    gfortran \
    pkg-config \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

WORKDIR /app

# Copy and install requirements including marker-pdf
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application code and install
COPY . .
RUN pip install --no-cache-dir --user -e .

# Production stage - minimal runtime image
FROM python:3.13-slim AS production

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libffi8 \
    libopenblas0 \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -r -s /bin/bash rubot

# Create cache directory and set permissions before switching user
RUN mkdir -p /app/cache && chown rubot:rubot /app/cache

# Create marker cache directory in /tmp with proper permissions
RUN mkdir -p /tmp/marker-pdf /tmp/cache /tmp/huggingface && chown -R rubot:rubot /tmp/marker-pdf /tmp/cache /tmp/huggingface

# Copy installed packages from builder
COPY --from=builder /root/.local /home/rubot/.local

# Copy application code
COPY --from=builder /app /app

# Set up environment
ENV PATH=/home/rubot/.local/bin:$PATH
ENV PYTHONPATH=/home/rubot/.local/lib/python3.13/site-packages
ENV HF_HOME=/tmp/huggingface
ENV XDG_CACHE_HOME=/tmp/cache

WORKDIR /app
USER rubot

ENTRYPOINT ["python", "-m", "rubot"]

# Development stage - for local development
FROM python:3.13-slim AS dev

RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    python3-dev \
    libopenblas-dev \
    gfortran \
    pkg-config \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    wget \
    bash \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e ".[dev]"

CMD ["bash"]