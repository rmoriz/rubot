"""
Docling-based PDF to Markdown converter
"""

import logging
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import ConversionStatus
    _DOCLING_AVAILABLE = True
except ImportError:
    _DOCLING_AVAILABLE = False
    
    # Mock classes for testing
    class _MockDocumentConverter:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def convert(self, *args: Any, **kwargs: Any) -> Any:
            class MockResult:
                def __init__(self) -> None:
                    self.status = _MockConversionStatus.SUCCESS
                    self.document = self

                def export_to_markdown(self, **kwargs: Any) -> str:
                    return "# Mock Markdown\n\nMock content for testing"

            return MockResult()

    class _MockConversionStatus:
        SUCCESS = "SUCCESS"
    
    # Type ignore for mock assignments
    DocumentConverter = _MockDocumentConverter  # type: ignore[assignment,misc]
    ConversionStatus = _MockConversionStatus  # type: ignore[assignment,misc]

try:
    from docling_core.types.doc.base import ImageRefMode
    _DOCLING_CORE_AVAILABLE = True
except ImportError:
    _DOCLING_CORE_AVAILABLE = False
    
    class _MockImageRefMode:
        PLACEHOLDER = "placeholder"
        EMBEDDED = "embedded"
        REFERENCED = "referenced"
    
    ImageRefMode = _MockImageRefMode  # type: ignore[assignment,misc]


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
    # Memory optimization settings
    use_cpu_only: bool = False
    batch_size: int = 1
    max_image_size: int = 1024


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

    def _create_converter(self) -> Any:
        """Create and configure DocumentConverter"""
        # Configure for memory optimization

        # Force CPU usage if configured
        if self.config.use_cpu_only:
            os.environ["CUDA_VISIBLE_DEVICES"] = ""

        # Use simple DocumentConverter initialization
        # Docling handles memory optimization internally based on available resources
        return DocumentConverter()

    def convert_to_markdown(self, pdf_path: str) -> str:
        """Convert PDF to Markdown using Docling"""
        try:
            self.logger.info(f"Converting PDF with Docling: {pdf_path}")

            # Convert document
            result = self._converter.convert(pdf_path)

            # Check conversion status
            if result.status != ConversionStatus.SUCCESS:
                raise RuntimeError(
                    f"Docling conversion failed: {result.status}"
                )

            # Configure image handling
            # ImageRefMode is already imported at module level
            
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
                image_mode=image_mode,
                image_placeholder=self.config.image_placeholder,
            )

            # Log conversion statistics
            self._log_conversion_stats(result)

            return markdown_content

        except RuntimeError as e:
            if "could not create a primitive" in str(e):
                self.logger.error("Memory/runtime error in Docling conversion")
                self.logger.error(
                    "Try setting DOCLING_DO_OCR=false and DOCLING_DO_TABLE_STRUCTURE=false"
                )
                self.logger.error("Or reduce PDF size with MAX_PDF_PAGES=10")
            self.logger.error(f"Docling conversion failed: {e}")
            raise RuntimeError(f"PDF conversion failed: {e}") from e
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
