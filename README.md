# rubot

CLI tool for downloading and processing Rathaus-Umschau PDFs from Munich with AI analysis.

## Features

- Downloads Rathaus-Umschau PDFs from Munich's official website
- Converts PDFs to Markdown using marker-pdf with intelligent caching
- Processes content with OpenRouter LLM API
- Outputs structured JSON with parsed content (not wrapped in OpenRouter format)
- Intelligent caching for both PDFs and Markdown conversion
- Comprehensive debug output and transparency
- Docker support for easy deployment

## Installation

### Prerequisites

- Python 3.13+ 
- OpenRouter API key
- marker-pdf (installed automatically)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/rmoriz/rubot.git
cd rubot
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install git+https://github.com/datalab-to/marker.git
```

4. Configure environment (ALL REQUIRED):
```bash
cp .env.example .env
# Edit .env and configure ALL REQUIRED variables:
```

## Configuration

### Required Environment Variables

**ALL of these are REQUIRED - the tool will fail with clear error messages if any are missing:**

```env
# REQUIRED: OpenRouter API Key
OPENROUTER_API_KEY=your_api_key_here

# REQUIRED: LLM Model to use
DEFAULT_MODEL=moonshotai/kimi-k2:free

# REQUIRED: System prompt (choose ONE of the following)
DEFAULT_SYSTEM_PROMPT=Analyze the following Rathaus-Umschau content and extract key information in a structured format.
# OR
DEFAULT_PROMPT_FILE=prompts/default.txt
```

### Optional Configuration

```env
# Network Settings
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=1.0

# Cache Settings
CACHE_ENABLED=true
CACHE_DIR=
CACHE_MAX_AGE_HOURS=24

# Processing Settings
MAX_PDF_PAGES=100
BATCH_MULTIPLIER=2

# Output Settings
OUTPUT_FORMAT=json
JSON_INDENT=2
```

## Usage

### Basic usage (today's date):
```bash
python -m rubot
```

### Specify date:
```bash
python -m rubot --date 2024-01-15
```

### Save to file:
```bash
python -m rubot --date 2024-01-15 --output result.json
```

### Custom prompt and model:
```bash
python -m rubot --prompt custom_prompt.txt --model anthropic/claude-3-haiku
```

### Verbose mode with debug output:
```bash
python -m rubot --date 2024-01-15 --verbose
```

### All CLI Options

```bash
python -m rubot --help
```

Available options:
- `--date YYYY-MM-DD`: Date of the Rathaus-Umschau (default: today)
- `--output FILE`: Output file path for JSON result (default: stdout)
- `--prompt FILE`: Path to custom prompt file (default: from config)
- `--model MODEL`: OpenRouter model ID (default: from config)
- `--config FILE`: Path to config file (default: .env)
- `--no-cache`: Disable PDF caching
- `--cache-dir DIR`: Custom cache directory
- `--temperature FLOAT`: LLM temperature (0.0-1.0, default: 0.1)
- `--max-tokens INT`: Maximum tokens for LLM response (default: 4000)
- `--verbose, -v`: Enable verbose output

## Output Format

The tool outputs a **complete OpenRouter response** with **parsed JSON content** (not a string):

```json
{
  "id": "gen-1752709707-6SfthRohEm7t6qB2lE4t",
  "provider": "Chutes",
  "model": "moonshotai/kimi-k2:free",
  "object": "chat.completion",
  "created": 1752709707,
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": {
          "summary": "Brief overview...",
          "announcements": [...],
          "events": [...],
          "important_dates": [...]
        }
      }
    }
  ],
  "usage": {
    "prompt_tokens": 12622,
    "completion_tokens": 1185,
    "total_tokens": 13807
  }
}
```

### Output Streams

- **STDOUT**: Clean JSON output (perfect for piping)
- **STDERR**: All logs, debug info, cache status, progress

```bash
# Only JSON data:
rubot --date 2024-01-15 > result.json

# Only log messages:
rubot --date 2024-01-15 2> logs.txt

# Both separated:
rubot --date 2024-01-15 > result.json 2> logs.txt

# Only JSON (suppress logs):
rubot --date 2024-01-15 2>/dev/null
```

## Caching

The tool uses intelligent caching for performance:

- **PDF Cache**: `/tmp/rubot_cache/` (24 hours default)
- **Markdown Cache**: `/tmp/rubot_markdown_cache/` (1 week default)

Cache status is shown on STDERR:
```
PDF Cache HIT: /tmp/rubot_cache/abc123.pdf
Markdown Cache HIT: /tmp/rubot_markdown_cache/def456.md
```

## Docker Usage

### Quick Start with Docker

```bash
# Pull the latest image
docker pull ghcr.io/rmoriz/rubot:latest

# Run with environment variables
docker run --rm \
  -e OPENROUTER_API_KEY=your_api_key_here \
  -e DEFAULT_MODEL=moonshotai/kimi-k2:free \
  -e DEFAULT_SYSTEM_PROMPT="Analyze the content..." \
  -v $(pwd)/output:/app/output \
  ghcr.io/rmoriz/rubot:latest \
  --date 2024-01-15 --output /app/output/result.json --verbose
```

### Build from source

```bash
# Build image
docker build -t rubot .

# Run with environment file
docker run --rm --env-file .env rubot --date 2024-01-15
```

### Docker Compose

```bash
# Copy docker-compose.yml and set environment variables in .env
docker-compose up rubot
```

## Development

### Install development dependencies:
```bash
pip install -e ".[dev]"
```

### Run tests:
```bash
pytest
```

### Code formatting:
```bash
black rubot/
flake8 rubot/
mypy rubot/
```

## Performance Notes

Processing time depends on several factors:

- **Input size**: Large PDFs (39k+ characters) take longer
- **Model choice**: Free models are slower than paid ones
- **Complexity**: Structured JSON output requires more processing
- **Network**: API latency and server load

**Typical times:**
- Free models: 30-60 seconds
- Paid models (Claude-3-Haiku): 10-20 seconds
- With caching: 2-5 seconds (subsequent runs)

## Troubleshooting

### Common Issues

1. **"Configuration error: OPENROUTER_API_KEY environment variable is required"**
   - Set all required environment variables in `.env`

2. **"marker-pdf not found"**
   - Install with: `pip install git+https://github.com/datalab-to/marker.git`

3. **"PDF not found for date"**
   - Check if Rathaus-Umschau was published on that date
   - Try a different date

4. **Slow processing**
   - Use a paid model instead of free ones
   - Reduce `--max-tokens`
   - Use caching for repeated runs

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request