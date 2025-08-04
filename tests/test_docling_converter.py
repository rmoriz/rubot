"""
Tests for Docling converter module
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

from rubot.docling_converter import DoclingPDFConverter, DoclingConfig


class TestDoclingConfig:
    """Test DoclingConfig dataclass"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = DoclingConfig()
        assert config.ocr_engine == "easyocr"
        assert config.do_ocr is True
        assert config.do_table_structure is False  # Disabled for faster processing
        assert config.table_structure_options is None
        assert config.ocr_options is None
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = DoclingConfig(
            ocr_engine="tesseract",
            do_ocr=False,
            do_table_structure=False
        )
        assert config.ocr_engine == "tesseract"
        assert config.do_ocr is False
        assert config.do_table_structure is False


class TestDoclingPDFConverter:
    """Test DoclingPDFConverter class"""
    
    def test_converter_initialization(self):
        """Test DoclingPDFConverter initialization"""
        config = DoclingConfig()
        converter = DoclingPDFConverter(config)
        assert converter.config == config
        assert converter._converter is not None
    
    @patch('rubot.docling_converter.DocumentConverter')
    def test_create_converter_easyocr(self, mock_converter_class):
        """Test converter creation with EasyOCR"""
        config = DoclingConfig(ocr_engine="easyocr")
        converter = DoclingPDFConverter(config)
        
        # Verify DocumentConverter was called (may have format_options or fallback to no args)
        mock_converter_class.assert_called_once()
    
    @patch('rubot.docling_converter.DocumentConverter')
    def test_create_converter_tesseract(self, mock_converter_class):
        """Test converter creation with Tesseract"""
        config = DoclingConfig(ocr_engine="tesseract")
        converter = DoclingPDFConverter(config)
        
        # Verify DocumentConverter was called (may have format_options or fallback to no args)
        mock_converter_class.assert_called_once()
    
    @patch('rubot.docling_converter.DocumentConverter')
    def test_convert_to_markdown_success(self, mock_converter_class):
        """Test successful PDF to markdown conversion"""
        # Setup mocks
        from docling.datamodel.base_models import ConversionStatus
        mock_result = MagicMock()
        mock_result.status = ConversionStatus.SUCCESS
        mock_result.document.export_to_markdown.return_value = "# Test Markdown\n\nContent here"
        mock_result.document.pages = [MagicMock(), MagicMock()]  # 2 pages
        mock_result.document.texts = ["text1", "text2"]
        mock_result.document.tables = [MagicMock()]
        mock_result.document.pictures = []
        
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_converter_class.return_value = mock_converter
        
        # Test conversion
        config = DoclingConfig()
        converter = DoclingPDFConverter(config)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_path = tmp_file.name
        
        try:
            result = converter.convert_to_markdown(tmp_path)
            
            assert result == "# Test Markdown\n\nContent here"
            mock_converter.convert.assert_called_once_with(tmp_path)
        finally:
            os.unlink(tmp_path)
    
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
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_path = tmp_file.name
        
        try:
            with pytest.raises(RuntimeError, match="Docling conversion failed"):
                converter.convert_to_markdown(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    @patch('rubot.docling_converter.DocumentConverter')
    def test_convert_to_markdown_exception(self, mock_converter_class):
        """Test PDF conversion with exception"""
        mock_converter = MagicMock()
        mock_converter.convert.side_effect = Exception("Test error")
        mock_converter_class.return_value = mock_converter
        
        config = DoclingConfig()
        converter = DoclingPDFConverter(config)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_path = tmp_file.name
        
        try:
            with pytest.raises(RuntimeError, match="PDF conversion failed"):
                converter.convert_to_markdown(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    @patch('rubot.docling_converter.DocumentConverter')
    def test_log_conversion_stats(self, mock_converter_class):
        """Test conversion statistics logging"""
        from docling.datamodel.base_models import ConversionStatus
        mock_result = MagicMock()
        mock_result.status = ConversionStatus.SUCCESS
        mock_result.document.export_to_markdown.return_value = "Test content"
        mock_result.document.pages = [MagicMock(), MagicMock()]
        mock_result.document.texts = ["text1"]
        mock_result.document.tables = []
        mock_result.document.pictures = [MagicMock()]
        
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_converter_class.return_value = mock_converter
        
        config = DoclingConfig()
        converter = DoclingPDFConverter(config)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_path = tmp_file.name
        
        try:
            # This should not raise an exception
            result = converter.convert_to_markdown(tmp_path)
            assert result == "Test content"
        finally:
            os.unlink(tmp_path)
    
    def test_file_not_found(self):
        """Test handling of non-existent PDF file"""
        config = DoclingConfig()
        converter = DoclingPDFConverter(config)
        
        # Mock the DocumentConverter.convert method to raise an exception
        with patch.object(converter._converter, 'convert', side_effect=FileNotFoundError("File not found")):
            with pytest.raises(RuntimeError, match="PDF conversion failed"):
                converter.convert_to_markdown("/nonexistent/file.pdf")