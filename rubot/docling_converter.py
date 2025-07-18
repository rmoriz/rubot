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


@dataclass
class DoclingConfig:
    """Configuration for Docling converter"""

    ocr_engine: str = "easyocr"  # easyocr, tesseract, rapidocr
    do_ocr: bool = True
    do_table_structure: bool = False  # Disabled for faster processing
    table_structure_options: Optional[Dict[str, Any]] = None
    ocr_options: Optional[Dict[str, Any]] = None
    # Image handling options
    image_mode: str = "placeholder"  # placeholder, embedded, referenced
    image_placeholder: str = "<!-- image -->"


class DoclingPDFConverter:
    """PDF to Markdown converter using Docling"""

    def __init__(self, config: DoclingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"Initializing Docling converter with OCR engine: {config.ocr_engine}"
        )
        self.logger.info(
            f"OCR enabled: {config.do_ocr}, Table structure: {config.do_table_structure}"
        )
        self._converter = self._create_converter()

    def _create_converter(self) -> DocumentConverter:
        """Create and configure DocumentConverter"""
        # Use default DocumentConverter which provides excellent performance
        # Docling has built-in optimizations for text extraction vs OCR
        return DocumentConverter()

    def convert_to_markdown(self, pdf_path: str) -> str:
        """Convert PDF to Markdown using Docling"""
        try:
            self.logger.info(f"Converting PDF with Docling: {pdf_path}")

            # Convert document
            result = self._converter.convert(pdf_path)

            # Check conversion status
            if result.status != ConversionStatus.SUCCESS:
                raise RuntimeError(f"Docling conversion failed: {result.status}")

            # Configure image handling
            from docling_core.types.doc.base import ImageRefMode

            # Map string config to enum
            image_mode_map = {
                "placeholder": ImageRefMode.PLACEHOLDER,
                "embedded": ImageRefMode.EMBEDDED,
                "referenced": ImageRefMode.REFERENCED,
            }

            image_mode = image_mode_map.get(
                self.config.image_mode, ImageRefMode.PLACEHOLDER
            )

            # Export to markdown with image configuration
            markdown_content: str = result.document.export_to_markdown(
                image_mode=image_mode, image_placeholder=self.config.image_placeholder
            )

            # Log conversion statistics
            self._log_conversion_stats(result)

            return markdown_content

        except Exception as e:
            self.logger.error(f"Docling conversion failed: {e}")
            raise RuntimeError(f"PDF conversion failed: {e}") from e

    def _log_conversion_stats(self, result: Any) -> None:
        """Log conversion statistics"""
        doc = result.document
        self.logger.info(f"Docling conversion complete:")
        self.logger.info(
            f"  - Pages: {len(doc.pages) if hasattr(doc, 'pages') else 'unknown'}"
        )
        self.logger.info(f"  - Characters: {len(doc.export_to_markdown())}")

        # Log detected elements
        if hasattr(doc, "texts"):
            self.logger.info(f"  - Text elements: {len(doc.texts)}")
        if hasattr(doc, "tables"):
            self.logger.info(f"  - Tables: {len(doc.tables)}")
        if hasattr(doc, "pictures"):
            self.logger.info(f"  - Images: {len(doc.pictures)}")
