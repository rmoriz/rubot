# Multi-stage build for optimized production image
FROM python:3.13-alpine as builder

# Install build dependencies in builder stage
RUN apk add --no-cache \
    git \
    gcc \
    musl-dev \
    libffi-dev \
    python3-dev \
    && pip install --upgrade pip

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Install marker-pdf in builder stage
RUN pip install --no-cache-dir --user git+https://github.com/datalab-to/marker.git

# Copy application code and install
COPY . .
RUN pip install --no-cache-dir --user -e .

# Production stage - minimal runtime image
FROM python:3.13-alpine as production

# Install only runtime dependencies
RUN apk add --no-cache \
    libffi \
    && adduser -D -s /bin/sh rubot

# Copy installed packages from builder
COPY --from=builder /root/.local /home/rubot/.local

# Copy application code
COPY --from=builder /app /app

# Set up environment
ENV PATH=/home/rubot/.local/bin:$PATH
ENV PYTHONPATH=/home/rubot/.local/lib/python3.13/site-packages:$PYTHONPATH

WORKDIR /app
USER rubot

# Create cache directory
RUN mkdir -p /app/cache

ENTRYPOINT ["python", "-m", "rubot"]

# Development stage - for local development
FROM python:3.13-alpine as dev

RUN apk add --no-cache \
    git \
    gcc \
    musl-dev \
    libffi-dev \
    python3-dev \
    bash \
    && pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/datalab-to/marker.git

COPY . .
RUN pip install --no-cache-dir -e ".[dev]"

CMD ["bash"]