# Multi-stage build for optimized production image
FROM python:3.13-slim AS builder

# Install minimal build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application code and install
COPY . .
RUN pip install --no-cache-dir --user -e .

# Production stage - minimal runtime image
FROM python:3.13-slim AS production

# Install only essential runtime dependencies
RUN apt-get update && apt-get install -y \
    libffi8 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -r -s /bin/bash rubot

# Create cache directory and set permissions before switching user
RUN mkdir -p /app/cache && chown rubot:rubot /app/cache

# Create cache directory with proper permissions
RUN mkdir -p /tmp/cache && \
    chown -R rubot:rubot /tmp/cache

# Copy installed packages from builder
COPY --from=builder /root/.local /home/rubot/.local

# Copy application code
COPY --from=builder /app /app

# Set up environment
ENV PATH=/home/rubot/.local/bin:$PATH
ENV PYTHONPATH=/home/rubot/.local/lib/python3.13/site-packages
ENV CACHE_ROOT=/tmp/cache
ENV XDG_CACHE_HOME=/tmp/cache

# Create writable directories and fix permissions before switching to rubot user
RUN mkdir -p /tmp/cache && \
    chown -R rubot:rubot /tmp/cache

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
    bash \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e ".[dev]"

CMD ["bash"]