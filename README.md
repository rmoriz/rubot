# rubot

A CLI tool for downloading and processing Rathaus-Umschau PDFs with AI analysis.

## Overview

`rubot` automates the process of:
1. Downloading Rathaus-Umschau PDFs from Munich's official website
2. Converting PDFs to Markdown using `marker-pdf`
3. Processing content with LLM via OpenRouter API
4. Outputting structured JSON results

## Installation

### Prerequisites

- Python 3.13+
- OpenRouter API key

### Install from Source

```bash
git clone https://github.com/rmoriz/rubot.git
cd rubot
python -m venv rubot-env
source rubot-env/bin/activate  # On Windows: rubot-env\Scripts\activate
pip install -r requirements.txt
pip install git+https://github.com/datalab-to/marker.git
```

### Using Installation Script

```bash
curl -sSL https://raw.githubusercontent.com/rmoriz/rubot/main/scripts/install.sh | bash
```

## Configuration

Create a `.env` file or set environment variables:

```bash
# Required
OPENROUTER_API_KEY=your_openrouter_api_key_here
DEFAULT_MODEL=your_preferred_model_here

# Optional - System Prompt (choose one)
DEFAULT_SYSTEM_PROMPT="Analyze the following Rathaus-Umschau content..."
# OR use a prompt file:
# DEFAULT_PROMPT_FILE=prompts/default.txt

# Optional - Network Settings
REQUEST_TIMEOUT=120
OPENROUTER_TIMEOUT=120
MARKER_TIMEOUT=600
MAX_RETRIES=3
RETRY_DELAY=1.0

# Optional - Cache Settings
CACHE_ENABLED=true
CACHE_DIR=
CACHE_MAX_AGE_HOURS=24

# Optional - Processing Settings
MAX_PDF_PAGES=100

# Optional - Output Settings
OUTPUT_FORMAT=json
JSON_INDENT=2
```

## Usage

### Basic Usage

```bash
# Process today's Rathaus-Umschau
rubot

# Process specific date
rubot --date 2024-01-15

# Save to file
rubot --date 2024-01-15 --output result.json

# Use custom prompt and model
rubot --date 2024-01-15 --prompt custom_prompt.txt --model gpt-4
```

### CLI Options

```
Options:
  --date TEXT        Date in YYYY-MM-DD format (default: today)
  --output TEXT      Output file path (default: stdout)
  --prompt TEXT      Path to system prompt file
  --model TEXT       OpenRouter model ID
  --temperature FLOAT LLM temperature (default: 0.1)
  --max-tokens INT   Maximum tokens for response (default: 4000)
  --verbose          Enable debug output
  --help             Show this message and exit
```

## Docker Usage

### Using Pre-built Image

```bash
docker run --rm \
  -e OPENROUTER_API_KEY=your_key \
  -e DEFAULT_MODEL=your_model \
  -v $(pwd)/output:/app/output \
  ghcr.io/rmoriz/rubot:latest \
  --date 2024-01-15 --output /app/output/result.json
```

### Docker Compose

```yaml
version: '3.8'
services:
  rubot:
    image: ghcr.io/rmoriz/rubot:latest
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - DEFAULT_MODEL=${DEFAULT_MODEL}
      - CACHE_ENABLED=true
      - CACHE_MAX_AGE_HOURS=24
    volumes:
      - ./cache:/app/cache
      - ./output:/app/output
    command: ["--date", "2024-01-15", "--output", "/app/output/result.json", "--verbose"]
```

## Model Selection

rubot works with any OpenRouter-compatible model. Popular choices include:

- `anthropic/claude-3-5-sonnet`
- `openai/gpt-4o`
- `google/gemini-pro`
- `meta-llama/llama-3.1-70b-instruct`

See [OpenRouter Models](https://openrouter.ai/models) for the complete list.

## Output Format

The tool outputs structured JSON with extracted information:

```json
{
  "summary": "Brief summary of the document",
  "announcements": [
    {
      "title": "Announcement Title",
      "description": "Detailed description",
      "category": "municipal_decision",
      "date": "2024-01-15",
      "location": "Munich City Hall"
    }
  ],
  "events": [
    {
      "title": "Event Title",
      "date": "2024-01-20",
      "time": "14:00",
      "location": "Event Location",
      "description": "Event description"
    }
  ],
  "metadata": {
    "source_date": "2024-01-15",
    "processed_at": "2024-01-15T10:30:00Z",
    "model_used": "anthropic/claude-3-5-sonnet"
  }
}
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Linting
flake8 rubot/

# Type checking
mypy rubot/

# Formatting
black rubot/
```

### Project Structure

```
rubot/
├── rubot/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py          # CLI interface
│   ├── config.py       # Configuration management
│   ├── downloader.py   # PDF downloading
│   ├── marker.py       # PDF to Markdown conversion
│   ├── llm.py          # OpenRouter API integration
│   ├── cache.py        # Caching functionality
│   ├── retry.py        # Retry mechanisms
│   ├── models.py       # Data models
│   └── utils.py        # Utility functions
├── tests/              # Test suite
├── examples/           # Usage examples
├── prompts/            # System prompt templates
└── docs/               # Documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/rmoriz/rubot/issues)
- Documentation: [docs/](docs/)
- Examples: [examples/](examples/)