"""
Integration tests for rubot workflow
"""

import pytest
import tempfile
import json
from unittest.mock import patch, MagicMock, mock_open
from click.testing import CliRunner

from rubot.cli import main


class TestIntegration:
    
    def setup_method(self):
        """Setup test runner"""
        self.runner = CliRunner()
    
    @patch('rubot.cli.os.remove')
    @patch('rubot.cli.process_with_openrouter')
    @patch('rubot.cli.convert_pdf_to_markdown')
    @patch('rubot.cli.download_pdf')
    @patch('rubot.cli.RubotConfig.from_env')
    def test_full_workflow_success(self, mock_config, mock_download, mock_convert, mock_llm, mock_remove):
        """Test complete workflow from download to output"""
        # Setup mocks
        mock_config_obj = MagicMock()
        mock_config_obj.default_model = 'anthropic/claude-3-haiku'
        mock_config_obj.default_prompt_file = None
        mock_config_obj.cache_enabled = False
        mock_config_obj.request_timeout = 30
        mock_config_obj.json_indent = 2
        mock_config.return_value = mock_config_obj
        mock_download.return_value = '/tmp/test.pdf'
        mock_convert.return_value = '# Test Document\n\nThis is test content.'
        mock_llm.return_value = json.dumps({
            "summary": "Test document analysis",
            "announcements": [
                {
                    "title": "Test Announcement",
                    "description": "Test description",
                    "category": "test",
                    "date": "2024-01-15"
                }
            ]
        }, indent=2)
        
        result = self.runner.invoke(main, ['--date', '2024-01-15'])
        
        assert result.exit_code == 0
        assert 'Processing Rathaus-Umschau for date: 2024-01-15' in result.output
        assert 'Downloading PDF...' in result.output
        assert 'Converting PDF to Markdown...' in result.output
        assert 'Processing with LLM...' in result.output
        assert '"summary": "Test document analysis"' in result.output
        
        # Verify all steps were called
        mock_download.assert_called_once_with('2024-01-15')
        mock_convert.assert_called_once_with('/tmp/test.pdf')
        mock_llm.assert_called_once()
        # Note: os.remove is only called if file exists, which is mocked differently
    
    @patch('rubot.cli.process_with_openrouter')
    @patch('rubot.cli.convert_pdf_to_markdown')
    @patch('rubot.cli.download_pdf')
    @patch('rubot.cli.load_env_config')
    def test_workflow_with_custom_prompt_and_model(self, mock_config, mock_download, mock_convert, mock_llm):
        """Test workflow with custom prompt file and model"""
        mock_config.return_value = {
            'DEFAULT_MODEL': 'default-model',
            'DEFAULT_PROMPT_FILE': None
        }
        mock_download.return_value = '/tmp/test.pdf'
        mock_convert.return_value = 'Test markdown'
        mock_llm.return_value = '{"result": "custom test"}'
        
        with self.runner.isolated_filesystem():
            # Create custom prompt file
            with open('custom_prompt.txt', 'w') as f:
                f.write('Custom prompt for testing')
            
            result = self.runner.invoke(main, [
                '--date', '2024-01-15',
                '--prompt', 'custom_prompt.txt',
                '--model', 'custom-model'
            ])
            
            assert result.exit_code == 0
            
            # Verify LLM was called with custom parameters
            mock_llm.assert_called_once_with(
                'Test markdown',
                'custom_prompt.txt',
                'custom-model'
            )
    
    @patch('rubot.cli.load_env_config')
    def test_workflow_date_validation_error(self, mock_config):
        """Test workflow with invalid date"""
        mock_config.return_value = {
            'DEFAULT_MODEL': 'test-model',
            'DEFAULT_PROMPT_FILE': None
        }
        
        result = self.runner.invoke(main, ['--date', 'invalid-date'])
        
        assert result.exit_code == 1
        assert 'Invalid date format' in result.output
    
    @patch('rubot.cli.download_pdf')
    @patch('rubot.cli.load_env_config')
    def test_workflow_download_error_handling(self, mock_config, mock_download):
        """Test workflow error handling for download failures"""
        mock_config.return_value = {
            'DEFAULT_MODEL': 'test-model',
            'DEFAULT_PROMPT_FILE': None
        }
        mock_download.side_effect = FileNotFoundError("PDF not found for date 2024-01-15")
        
        result = self.runner.invoke(main, ['--date', '2024-01-15'])
        
        assert result.exit_code == 1
        assert 'Error: PDF not found for date 2024-01-15' in result.output