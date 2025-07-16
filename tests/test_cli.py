"""
Tests for CLI module
"""

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
    @patch('rubot.cli.load_env_config')
    def test_cli_basic_usage(self, mock_config, mock_download, mock_convert, mock_llm):
        """Test basic CLI usage"""
        # Setup mocks
        mock_config_obj = MagicMock()
        mock_config_obj.default_model = 'test_model'
        mock_config_obj.default_prompt_file = None
        mock_config_obj.cache_enabled = False
        mock_config_obj.request_timeout = 30
        mock_config_obj.json_indent = 2
        mock_config.return_value = mock_config_obj
        mock_download.return_value = '/tmp/test.pdf'
        mock_convert.return_value = 'test markdown content'
        mock_llm.return_value = '{"result": "test"}'
        
        result = self.runner.invoke(main, ['--date', '2024-01-15'])
        
        assert result.exit_code == 0
        assert '{"result": "test"}' in result.output
        mock_download.assert_called_once_with('2024-01-15')
        mock_convert.assert_called_once_with('/tmp/test.pdf')
        mock_llm.assert_called_once()
    
    @patch('rubot.cli.process_with_openrouter')
    @patch('rubot.cli.convert_pdf_to_markdown')
    @patch('rubot.cli.download_pdf')
    @patch('rubot.cli.RubotConfig.from_env')
    def test_cli_with_output_file(self, mock_config, mock_download, mock_convert, mock_llm):
        """Test CLI with output file"""
        mock_config.return_value = {
            'DEFAULT_MODEL': 'test_model',
            'DEFAULT_PROMPT_FILE': None
        }
        mock_download.return_value = '/tmp/test.pdf'
        mock_convert.return_value = 'test markdown content'
        mock_llm.return_value = '{"result": "test"}'
        
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(main, [
                '--date', '2024-01-15',
                '--output', 'result.json'
            ])
            
            assert result.exit_code == 0
            assert 'Result saved to: result.json' in result.output
            
            # Check file was created
            with open('result.json', 'r') as f:
                content = f.read()
                assert content == '{"result": "test"}'
    
    @patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'})
    def test_cli_invalid_date(self):
        """Test CLI with invalid date"""
        result = self.runner.invoke(main, ['--date', 'invalid-date'])
        
        assert result.exit_code == 1
        assert 'Invalid date format' in result.output
    
    @patch('rubot.cli.download_pdf')
    @patch('rubot.cli.RubotConfig.from_env')
    def test_cli_download_error(self, mock_config, mock_download):
        """Test CLI with download error"""
        mock_config.return_value = {
            'DEFAULT_MODEL': 'test_model',
            'DEFAULT_PROMPT_FILE': None
        }
        mock_download.side_effect = FileNotFoundError("PDF not found")
        
        result = self.runner.invoke(main, ['--date', '2024-01-15'])
        
        assert result.exit_code == 1
        assert 'Error: PDF not found' in result.output