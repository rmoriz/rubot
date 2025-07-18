# Multi-stage build for optimized Alpine production image
FROM python:3.13-alpine AS builder

# Install build dependencies for PyMuPDF compilation
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    libffi-dev \
    python3-dev \
    linux-headers \
    make \
    cmake \
    clang-dev \
    llvm-dev \
    freetype-dev \
    harfbuzz-dev \
    jpeg-dev \
    openjpeg-dev \
    jbig2dec-dev \
    && pip install --upgrade pip

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application code and install
COPY . .
RUN pip install --no-cache-dir --user -e .

# Production stage - minimal Alpine runtime image
FROM python:3.13-alpine AS production

# Install runtime dependencies including Tesseract
RUN apk add --no-cache \
    libffi \
    tesseract-ocr \
    tesseract-ocr-data-deu \
    tesseract-ocr-data-eng \
    freetype \
    harfbuzz \
    jpeg \
    openjpeg \
    jbig2dec \
    && addgroup -g 1000 rubot \
    && adduser -u 1000 -G rubot -s /bin/sh -D rubot

# Create cache directory and set permissions
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

WORKDIR /app
USER rubot

ENTRYPOINT ["python", "-m", "rubot"]

# Development stage - Alpine development image
FROM python:3.13-alpine AS dev

# Install development dependencies including Tesseract
RUN apk add --no-cache \
    git \
    gcc \
    g++ \
    musl-dev \
    libffi-dev \
    python3-dev \
    linux-headers \
    make \
    cmake \
    clang-dev \
    llvm-dev \
    freetype-dev \
    harfbuzz-dev \
    jpeg-dev \
    openjpeg-dev \
    jbig2dec-dev \
    tesseract-ocr \
    tesseract-ocr-data-deu \
    tesseract-ocr-data-eng \
    bash \
    \u0026\u0026 pip install --upgrade pip

WORKDIR /app

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the application with dev dependencies
COPY . .
RUN pip install --no-cache-dir -e ".[dev]"

# Create cache directory for development
RUN mkdir -p /tmp/cache

CMD ["sh"]