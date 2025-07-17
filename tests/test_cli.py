"""
Tests for CLI module
"""

import os
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from rubot.cli import main


class TestCLI:
    
    def setup_method(self):
        """Setup test runner"""
        self.runner = CliRunner()
    
    @patch('rubot.cli.process_with_openrouter')
    @patch('rubot.cli.convert_pdf_to_markdown')
    @patch('rubot.cli.download_pdf')
    @patch('rubot.cli.RubotConfig.from_env')
    def test_cli_basic_usage(self, mock_config, mock_download, mock_convert, mock_llm):
        """Test basic CLI usage"""
        # Mock config object
        mock_config_obj = MagicMock()
        mock_config_obj.default_model = 'test/model'
        mock_config_obj.default_prompt_file = None
        mock_config_obj.request_timeout = 120
        mock_config_obj.marker_timeout = 600
        mock_config_obj.openrouter_timeout = 120
        mock_config_obj.cache_enabled = False
        mock_config_obj.cache_dir = None
        mock_config_obj.cache_max_age_hours = 24
        mock_config_obj.to_dict.return_value = {}
        mock_config.return_value = mock_config_obj
        
        mock_download.return_value = '/tmp/test.pdf'
        mock_convert.return_value = 'test markdown content'
        mock_llm.return_value = '{"result": "test"}'
        
        with patch.dict(os.environ, {'DEFAULT_SYSTEM_PROMPT': 'Test prompt'}):
            result = self.runner.invoke(main, ['--date', '2024-01-15'])
        
        assert result.exit_code == 0
        mock_download.assert_called_once()
        mock_convert.assert_called_once()
        mock_llm.assert_called_once()
    
    @patch('rubot.cli.process_with_openrouter')
    @patch('rubot.cli.convert_pdf_to_markdown')
    @patch('rubot.cli.download_pdf')
    @patch('rubot.cli.RubotConfig.from_env')
    def test_cli_with_output_file(self, mock_config, mock_download, mock_convert, mock_llm):
        """Test CLI with output file"""
        # Mock config object
        mock_config_obj = MagicMock()
        mock_config_obj.default_model = 'test/model'
        mock_config_obj.default_prompt_file = None
        mock_config_obj.request_timeout = 120
        mock_config_obj.marker_timeout = 600
        mock_config_obj.openrouter_timeout = 120
        mock_config_obj.cache_enabled = False
        mock_config_obj.cache_dir = None
        mock_config_obj.cache_max_age_hours = 24
        mock_config.return_value = mock_config_obj
        
        mock_download.return_value = '/tmp/test.pdf'
        mock_convert.return_value = 'test markdown content'
        mock_llm.return_value = '{"result": "test"}'
        
        with self.runner.isolated_filesystem():
            with patch.dict(os.environ, {'DEFAULT_SYSTEM_PROMPT': 'Test prompt'}):
                result = self.runner.invoke(main, [
                    '--date', '2024-01-15',
                    '--output', 'result.json'
                ])
            
            assert result.exit_code == 0
            assert 'saved to: result.json' in result.output
            
            # Check file was created
            with open('result.json', 'r') as f:
                content = f.read()
                assert '"result": "test"' in content
    
    @patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key', 'DEFAULT_MODEL': 'test_model', 'DEFAULT_SYSTEM_PROMPT': 'test'})
    def test_cli_invalid_date(self):
        """Test CLI with invalid date"""
        result = self.runner.invoke(main, ['--date', 'invalid-date'])
        
        assert result.exit_code == 1
        assert 'Invalid date format' in result.output
    
    @patch('rubot.cli.download_pdf')
    @patch('rubot.cli.RubotConfig.from_env')
    def test_cli_download_error(self, mock_config, mock_download):
        """Test CLI with download error"""
        # Mock config object
        mock_config_obj = MagicMock()
        mock_config_obj.default_model = 'test/model'
        mock_config_obj.default_prompt_file = None
        mock_config_obj.request_timeout = 120
        mock_config_obj.marker_timeout = 600
        mock_config_obj.openrouter_timeout = 120
        mock_config_obj.cache_enabled = False
        mock_config_obj.cache_dir = None
        mock_config_obj.cache_max_age_hours = 24
        mock_config.return_value = mock_config_obj
        
        mock_download.side_effect = FileNotFoundError("PDF not found")
        
        with patch.dict(os.environ, {'DEFAULT_SYSTEM_PROMPT': 'Test prompt'}):
            result = self.runner.invoke(main, ['--date', '2024-01-15'])
        
        assert result.exit_code == 1
        assert 'Error: PDF not found' in result.output