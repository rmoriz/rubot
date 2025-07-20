# Migration Plan: PyMuPDF to Docling

## Overview

This document outlines the migration plan to replace PyMuPDF with [Docling](https://github.com/docling-project/docling) for PDF to Markdown conversion in rubot. Docling provides superior document understanding, advanced OCR capabilities, and better structured output for AI processing.

## Current State Analysis

### Current PyMuPDF Implementation
- **File**: `rubot/cli.py` (lines 244-472)
- **Features**:
  - Basic text extraction with `page.get_text("text")`
  - Fallback OCR using PyMuPDF's Tesseract integration
  - Streaming processing for large files
  - Markdown caching with SHA256 content hashing
  - Page-by-page processing with memory management

### Current Dependencies
```toml
# pyproject.toml
dependencies = [
    "PyMuPDF>=1.23.0",  # Will be removed
    # ... other deps
]
```

## Migration Benefits

### Advantages of Docling
1. **Advanced PDF Understanding**: Layout analysis, reading order, table structure
2. **Superior OCR**: Multiple OCR engines (EasyOCR, Tesseract, RapidOCR, OnnxTR)
3. **Structured Output**: Native DoclingDocument format with semantic understanding
4. **Better Markdown Export**: Preserves document structure and formatting
5. **Multi-format Support**: PDF, DOCX, PPTX, HTML, images, audio
6. **Production Ready**: Used by IBM Research, actively maintained

### Specific Improvements for Rathaus-Umschau
1. **Table Extraction**: Better handling of municipal data tables
2. **Layout Understanding**: Proper section and subsection detection
3. **Image Processing**: OCR for embedded images and diagrams
4. **Metadata Extraction**: Document properties and structure

## Implementation Plan

### Phase 1: Dependencies and Environment Setup

#### 1.1 Update Dependencies
```toml
# pyproject.toml - Remove PyMuPDF, add Docling
dependencies = [
    "click>=8.1.0",
    "requests>=2.31.0", 
    "python-dotenv>=1.0.0",
    "docling>=2.41.0",  # NEW: Main docling package
    # PyMuPDF>=1.23.0",  # REMOVE
]

[project.optional-dependencies]
dev = [
    # ... existing dev deps
]
# NEW: OCR engine options
ocr-tesseract = ["docling[tesserocr]"]
ocr-rapid = ["docling[rapidocr]"]
vlm = ["docling[vlm]"]  # For future VLM integration
```

#### 1.2 Update requirements.txt
```txt
# Remove PyMuPDF, add docling
click>=8.1.0
requests>=2.31.0
python-dotenv>=1.0.0
docling>=2.41.0
```

### Phase 2: Core Implementation Changes

#### 2.1 Create New Docling Converter Module
**New file**: `rubot/docling_converter.py`

```python
"""
Docling-based PDF to Markdown converter
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import ConversionStatus
from docling.datamodel.pipeline_options import (
    PipelineOptions, 
    EasyOcrOptions, 
    TesseractOcrOptions
)

@dataclass
class DoclingConfig:
    """Configuration for Docling converter"""
    ocr_engine: str = "easyocr"  # easyocr, tesseract, rapidocr
    do_ocr: bool = True
    do_table_structure: bool = True
    table_structure_options: Optional[Dict[str, Any]] = None
    ocr_options: Optional[Dict[str, Any]] = None

class DoclingPDFConverter:
    """PDF to Markdown converter using Docling"""
    
    def __init__(self, config: DoclingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._converter = self._create_converter()
    
    def _create_converter(self) -> DocumentConverter:
        """Create and configure DocumentConverter"""
        pipeline_options = PipelineOptions()
        pipeline_options.do_ocr = self.config.do_ocr
        pipeline_options.do_table_structure = self.config.do_table_structure
        
        # Configure OCR options based on engine choice
        if self.config.do_ocr:
            if self.config.ocr_engine == "tesseract":
                pipeline_options.ocr_options = TesseractOcrOptions()
            elif self.config.ocr_engine == "easyocr":
                pipeline_options.ocr_options = EasyOcrOptions()
            # Add other OCR engines as needed
        
        return DocumentConverter(pipeline_options=pipeline_options)
    
    def convert_to_markdown(self, pdf_path: str) -> str:
        """Convert PDF to Markdown using Docling"""
        try:
            self.logger.info(f"Converting PDF with Docling: {pdf_path}")
            
            # Convert document
            result = self._converter.convert(pdf_path)
            
            # Check conversion status
            if result.status != ConversionStatus.SUCCESS:
                raise RuntimeError(f"Docling conversion failed: {result.status}")
            
            # Export to markdown
            markdown_content = result.document.export_to_markdown()
            
            # Log conversion statistics
            self._log_conversion_stats(result)
            
            return markdown_content
            
        except Exception as e:
            self.logger.error(f"Docling conversion failed: {e}")
            raise RuntimeError(f"PDF conversion failed: {e}") from e
    
    def _log_conversion_stats(self, result) -> None:
        """Log conversion statistics"""
        doc = result.document
        self.logger.info(f"Docling conversion complete:")
        self.logger.info(f"  - Pages: {len(doc.pages) if hasattr(doc, 'pages') else 'unknown'}")
        self.logger.info(f"  - Characters: {len(doc.export_to_markdown())}")
        
        # Log detected elements
        if hasattr(doc, 'texts'):
            self.logger.info(f"  - Text elements: {len(doc.texts)}")
        if hasattr(doc, 'tables'):
            self.logger.info(f"  - Tables: {len(doc.tables)}")
        if hasattr(doc, 'pictures'):
            self.logger.info(f"  - Images: {len(doc.pictures)}")
```

#### 2.2 Update CLI Module
**Modified file**: `rubot/cli.py`

Replace the `_convert_to_markdown` function:

```python
def _convert_to_markdown(
    pdf_path: str, app_config: RubotConfig, cache_dir: Optional[str], logger: logging.Logger
) -> str:
    """Convert PDF to markdown using Docling with caching."""
    from .docling_converter import DoclingPDFConverter, DoclingConfig
    
    # Create cache directory for markdown
    cache_root = cache_dir or app_config.cache_dir or os.getenv("CACHE_ROOT", tempfile.gettempdir()) or "/tmp"
    markdown_cache_dir = os.path.join(cache_root, "markdown")
    os.makedirs(markdown_cache_dir, exist_ok=True)
    
    # Generate cache key from PDF file (streaming hash)
    import hashlib
    hasher = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    content_hash = hasher.hexdigest()
    
    cache_key = f"{content_hash}_docling.md"
    cache_file = os.path.join(markdown_cache_dir, cache_key)
    
    # Check if markdown is cached
    if os.path.exists(cache_file):
        cache_age = time.time() - os.path.getmtime(cache_file)
        cache_max_age = app_config.cache_max_age_hours * 3600
        
        if cache_age < cache_max_age:
            cache_file_size = os.path.getsize(cache_file)
            logger.info(f"Markdown Cache HIT: {cache_file} ({cache_file_size:,} bytes)")
            with open(cache_file, "r", encoding="utf-8") as f:
                content = f.read()
                logger.info(f"Markdown loaded from cache: {len(content):,} characters")
                return content
        else:
            logger.info(f"Markdown Cache EXPIRED: {cache_file} (age: {cache_age/3600:.1f}h)")
    else:
        logger.info("Markdown Cache MISS: Converting PDF with Docling...")
    
    # Configure Docling
    docling_config = DoclingConfig(
        ocr_engine=os.getenv("DOCLING_OCR_ENGINE", "easyocr"),
        do_ocr=os.getenv("DOCLING_DO_OCR", "true").lower() == "true",
        do_table_structure=os.getenv("DOCLING_DO_TABLE_STRUCTURE", "true").lower() == "true"
    )
    
    # Convert with Docling
    converter = DoclingPDFConverter(docling_config)
    markdown_content = converter.convert_to_markdown(pdf_path)
    
    # Cache the markdown
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    logger.info(f"Docling conversion complete: {len(markdown_content):,} characters")
    logger.debug(f"Markdown cached to: {cache_file}")
    
    return markdown_content
```

Remove the old PyMuPDF functions:
- `_convert_pdf_standard()`
- `_convert_large_pdf_streaming()`

#### 2.3 Update Configuration
**Modified file**: `rubot/config.py`

Add Docling-specific configuration options:

```python
@dataclass
class RubotConfig:
    """Configuration class for rubot"""
    
    # ... existing fields ...
    
    # NEW: Docling configuration
    docling_ocr_engine: str = "easyocr"
    docling_do_ocr: bool = True
    docling_do_table_structure: bool = True
    docling_model_cache_dir: Optional[str] = None
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "RubotConfig":
        # ... existing code ...
        
        return cls(
            # ... existing fields ...
            
            # NEW: Docling configuration
            docling_ocr_engine=os.getenv("DOCLING_OCR_ENGINE", "easyocr"),
            docling_do_ocr=os.getenv("DOCLING_DO_OCR", "true").lower() == "true",
            docling_do_table_structure=os.getenv("DOCLING_DO_TABLE_STRUCTURE", "true").lower() == "true",
            docling_model_cache_dir=os.getenv("DOCLING_MODEL_CACHE_DIR"),
        )
```

### Phase 3: Docker and Infrastructure Updates

#### 3.1 Update Dockerfile
**Modified file**: `Dockerfile`

```dockerfile
FROM python:3.13-slim

# Install system dependencies for Docling
RUN apt-get update && apt-get install -y \
    # Tesseract OCR (optional but recommended)
    tesseract-ocr \
    tesseract-ocr-deu \
    # System libraries for image processing
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # For building some Python packages
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set Tesseract data path
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/
COPY pyproject.toml /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download Docling models to avoid first-run delays
RUN python -c "
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PipelineOptions, EasyOcrOptions
import os
os.makedirs('/app/models', exist_ok=True)
os.environ['HF_HOME'] = '/app/models'
os.environ['TORCH_HOME'] = '/app/models'
# Initialize converter to trigger model downloads
pipeline_options = PipelineOptions()
pipeline_options.ocr_options = EasyOcrOptions()
converter = DocumentConverter(pipeline_options=pipeline_options)
print('Docling models pre-downloaded successfully')
"

# Copy application code
COPY . /app

# Set model cache environment variables
ENV HF_HOME=/app/models
ENV TORCH_HOME=/app/models
ENV DOCLING_MODEL_CACHE_DIR=/app/models

ENTRYPOINT ["python", "-m", "rubot"]
```

#### 3.2 Update Docker Compose
**Modified file**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  rubot:
    build: .
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - DEFAULT_MODEL=${DEFAULT_MODEL:-oonshotai/kimi-k2:free}
      - CACHE_ROOT=/app/cache
      - DOCLING_OCR_ENGINE=${DOCLING_OCR_ENGINE:-easyocr}
      - DOCLING_MODEL_CACHE_DIR=/app/models
      - HF_HOME=/app/models
      - TORCH_HOME=/app/models
    volumes:
      - ./cache:/app/cache
      - ./models:/app/models  # Persist model cache
    command: ["--date", "2024-01-15", "--verbose"]
```

#### 3.3 Update .dockerignore
**Modified file**: `.dockerignore`

```
# Add model cache directories
models/
*.pt
*.bin
*.onnx
```

### Phase 4: CI/CD Updates

#### 4.1 Update GitHub Actions - Test Workflow
**Modified file**: `.github/workflows/test.yml`

```yaml
name: Test rubot

on:
  push:
    branches: [main, docling]  # Add docling branch
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12", "3.13"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      # Install system dependencies for Docling
      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y tesseract-ocr tesseract-ocr-deu libgl1-mesa-glx
          
      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov mypy
          
      - name: Run type checking
        run: mypy rubot/
        
      - name: Run tests
        run: pytest --cov=rubot tests/
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          DEFAULT_MODEL: "oonshotai/kimi-k2:free"
```

#### 4.2 Update Release Workflow
**Modified file**: `.github/workflows/release.yml`

```yaml
name: Build and Release

on:
  push:
    tags:
      - "v*"

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ghcr.io/rmoriz/rubot:latest
            ghcr.io/rmoriz/rubot:${{ github.ref_name }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64
```

### Phase 5: Testing Strategy

#### 5.1 Update Test Files
**Modified file**: `tests/test_docling_converter.py` (NEW)

```python
"""
Tests for Docling converter module
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

from rubot.docling_converter import DoclingPDFConverter, DoclingConfig


class TestDoclingConverter:
    
    def test_converter_initialization(self):
        """Test DoclingPDFConverter initialization"""
        config = DoclingConfig()
        converter = DoclingPDFConverter(config)
        assert converter.config == config
        assert converter._converter is not None
    
    @patch('rubot.docling_converter.DocumentConverter')
    def test_convert_to_markdown_success(self, mock_converter_class):
        """Test successful PDF to markdown conversion"""
        # Setup mocks
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"  # ConversionStatus.SUCCESS
        mock_result.document.export_to_markdown.return_value = "# Test Markdown"
        
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_converter_class.return_value = mock_converter
        
        # Test conversion
        config = DoclingConfig()
        converter = DoclingPDFConverter(config)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_file:
            result = converter.convert_to_markdown(tmp_file.name)
            
        assert result == "# Test Markdown"
        mock_converter.convert.assert_called_once_with(tmp_file.name)
    
    @patch('rubot.docling_converter.DocumentConverter')
    def test_convert_to_markdown_failure(self, mock_converter_class):
        """Test PDF conversion failure handling"""
        mock_result = MagicMock()
        mock_result.status = "FAILURE"
        
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_converter_class.return_value = mock_converter
        
        config = DoclingConfig()
        converter = DoclingPDFConverter(config)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_file:
            with pytest.raises(RuntimeError, match="Docling conversion failed"):
                converter.convert_to_markdown(tmp_file.name)
```

#### 5.2 Update Integration Tests
**Modified file**: `tests/test_integration.py`

```python
# Update existing tests to use Docling mocks instead of PyMuPDF
@patch("rubot.cli.DoclingPDFConverter")
def test_full_workflow_with_docling(self, mock_converter_class, cli_runner, temp_config):
    """Test complete workflow with Docling converter"""
    # Setup mocks
    mock_converter = MagicMock()
    mock_converter.convert_to_markdown.return_value = "# Docling Test Content"
    mock_converter_class.return_value = mock_converter
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b"mock pdf content")
        tmp_path = tmp_file.name

    try:
        with patch("rubot.cli.download_pdf", return_value=tmp_path), \
             patch("rubot.cli.process_with_openrouter", return_value='{"result": "success"}') as mock_llm:
            
            with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config):
                result = cli_runner.invoke(main, ["--date", "2024-01-15"])

            assert result.exit_code == 0
            mock_converter.convert_to_markdown.assert_called_once()
            mock_llm.assert_called_once()

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
```

### Phase 6: Documentation Updates

#### 6.1 Update README.md
Add Docling-specific information:

```markdown
## 🔄 PDF Processing

rubot uses [Docling](https://github.com/docling-project/docling) for advanced PDF processing:

- **Advanced Layout Understanding**: Proper section detection and reading order
- **Superior OCR**: Multiple OCR engines (EasyOCR, Tesseract, RapidOCR)
- **Table Extraction**: Structured table data extraction
- **Image Processing**: OCR for embedded images and diagrams

### OCR Configuration

Configure OCR engine via environment variables:

```bash
# OCR Engine (easyocr, tesseract, rapidocr)
export DOCLING_OCR_ENGINE=easyocr

# Enable/disable OCR
export DOCLING_DO_OCR=true

# Enable table structure detection
export DOCLING_DO_TABLE_STRUCTURE=true
```

### Model Caching

Docling downloads AI models on first use. To pre-download in Docker:

```bash
# Models are cached in /app/models in Docker
docker run -v ./models:/app/models ghcr.io/rmoriz/rubot --help
```
```

#### 6.2 Update Environment Variables Documentation
**Modified file**: `.env.example`

```bash
# ... existing vars ...

# Docling Configuration
DOCLING_OCR_ENGINE=easyocr
DOCLING_DO_OCR=true
DOCLING_DO_TABLE_STRUCTURE=true
DOCLING_MODEL_CACHE_DIR=/path/to/model/cache
```

### Phase 7: Migration Execution Plan

#### 7.1 Development Phase (Week 1)
1. **Day 1-2**: Implement `docling_converter.py` module
2. **Day 3-4**: Update CLI module and configuration
3. **Day 5**: Update tests and fix issues

#### 7.2 Testing Phase (Week 2)
1. **Day 1-2**: Comprehensive testing with real Rathaus-Umschau PDFs
2. **Day 3**: Performance comparison with PyMuPDF
3. **Day 4-5**: Docker and CI/CD testing

#### 7.3 Infrastructure Phase (Week 3)
1. **Day 1-2**: Update Docker images and model pre-downloading
2. **Day 3**: Update CI/CD workflows
3. **Day 4-5**: Documentation and examples

#### 7.4 Deployment Phase (Week 4)
1. **Day 1**: Merge to main branch
2. **Day 2**: Release new version
3. **Day 3-5**: Monitor and fix any issues

## Risk Assessment and Mitigation

### High Risk
1. **Model Download Size**: Docling models are large (~1-2GB)
   - **Mitigation**: Pre-download in Docker image, persistent volume mounting
   
2. **Memory Usage**: Docling may use more memory than PyMuPDF
   - **Mitigation**: Monitor memory usage, implement streaming for very large files

### Medium Risk
1. **OCR Accuracy Changes**: Different OCR engine may produce different results
   - **Mitigation**: Extensive testing with real PDFs, fallback options
   
2. **Performance Impact**: Docling may be slower than PyMuPDF
   - **Mitigation**: Benchmark and optimize, improve caching

### Low Risk
1. **Dependency Conflicts**: New dependencies may conflict
   - **Mitigation**: Use virtual environments, test thoroughly

## Success Metrics

1. **Functionality**: All existing features work with Docling
2. **Quality**: Better text extraction and structure preservation
3. **Performance**: Conversion time within 2x of current implementation
4. **Reliability**: 99%+ success rate on Rathaus-Umschau PDFs
5. **Maintainability**: Clean, testable code with good documentation

## Rollback Plan

If migration fails:
1. Revert to PyMuPDF implementation
2. Keep Docling code in feature branch
3. Address issues and retry migration

The migration maintains backward compatibility through environment variable configuration, allowing gradual rollout and easy rollback if needed.