<div align="center">

# 🤖 rubot

**AI-Powered Munich Rathaus-Umschau PDF Processor**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPLv3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Docker](https://img.shields.io/badge/docker-available-blue.svg)](https://github.com/rmoriz/rubot/pkgs/container/rubot)
[![Tests](https://github.com/rmoriz/rubot/workflows/Test%20rubot/badge.svg)](https://github.com/rmoriz/rubot/actions)

*Automate the extraction and analysis of Munich's official municipal announcements*

[🚀 Quick Start](#-quick-start) • [📖 Documentation](#-configuration) • [🐳 Docker](#-docker-usage) • [🤝 Contributing](#-contributing)

</div>

---

## 📱 Follow @lisa_radieschen on Mastodon

<div align="center">

![Lisa Radieschen](docs/lisa_radieschen.jpeg)

**Follow [@lisa_radieschen@social.entrypoint.sh](https://social.entrypoint.sh/@lisa_radieschen) on Mastodon/Fediverse to see the daily results of this workflow at 1 PM**

</div>

---

## ✨ What is rubot?

`rubot` is a powerful CLI tool that transforms Munich's Rathaus-Umschau PDFs into structured, AI-analyzed data. Perfect for journalists, researchers, and citizens who want to stay informed about municipal decisions and events.

### 🔄 How it works

```mermaid
graph LR
    A[📄 PDF Download] --> B[📝 Markdown Conversion]
    B --> C[🤖 AI Analysis]
    C --> D[📊 JSON Output]
```

1. **📥 Downloads** Rathaus-Umschau PDFs from Munich's official website
2. **🔄 Converts** PDFs to structured Markdown using Docling's advanced document understanding
3. **🧠 Analyzes** content with your choice of AI model via OpenRouter
4. **📤 Outputs** structured JSON with extracted announcements and events

## 🚀 Quick Start

### 📋 Prerequisites

- 🐍 **Python 3.13+**
- 🔑 **OpenRouter API key** ([Get yours here](https://openrouter.ai/))
- 💾 **2-4GB RAM** (for PDF processing with Docling and AI models)

### ⚡ One-Line Installation

```bash
curl -sSL https://raw.githubusercontent.com/rmoriz/rubot/main/scripts/install.sh | bash
```

### 🛠️ Manual Installation

<details>
<summary>Click to expand manual installation steps</summary>

```bash
# Clone the repository
git clone https://github.com/rmoriz/rubot.git
cd rubot

# Create virtual environment
python -m venv rubot-env
source rubot-env/bin/activate  # On Windows: rubot-env\Scripts\activate

# Install dependencies
pip install -e .
```

</details>

## ⚙️ Configuration

### 🔐 Required Environment Variables

```bash
# 🔑 API Configuration (Required)
OPENROUTER_API_KEY=your_openrouter_api_key_here
DEFAULT_MODEL=your_preferred_model_here

# 💬 System Prompt (Required - choose one)
DEFAULT_SYSTEM_PROMPT="Analyze the following Rathaus-Umschau content..."
# OR use a prompt file:
# DEFAULT_PROMPT_FILE=prompts/default.txt
```

### 🔧 Optional Configuration

<details>
<summary>All available environment variables</summary>

```bash
# 🌐 Network Settings
REQUEST_TIMEOUT=120          # PDF download timeout in seconds
OPENROUTER_TIMEOUT=120       # OpenRouter API timeout in seconds

# 💾 Cache Settings
CACHE_ENABLED=true           # Enable/disable caching
CACHE_DIR=/tmp/rubot_cache   # Custom cache directory
CACHE_MAX_AGE_HOURS=24       # Cache age in hours

# 🧹 Cache Cleanup Settings
CACHE_CLEANUP_DAYS=14        # Delete cache files after N days (0 = disable)
SKIP_CLEANUP=1               # Skip automatic cache cleanup

# 📄 Processing Settings
DEFAULT_TEMPERATURE=0.8      # LLM temperature (0.0-1.0)
DEFAULT_MAX_TOKENS=4000      # Maximum tokens for LLM response

# 📊 Logging
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR
```

</details>

## 🎯 Usage

### 🏃‍♂️ Basic Usage

```bash
# 📅 Process today's Rathaus-Umschau
rubot

# 🗓️ Process specific date
rubot --date 2025-07-17

# 💾 Save to file
rubot --date 2025-07-17 --output result.json

# 🎨 Use custom prompt and model
rubot --date 2025-07-17 --prompt custom_prompt.txt --model gpt-4

# 🧹 Cache cleanup after 7 days
rubot --date 2025-07-17 --cache-cleanup-days 7

# 🚫 Skip cache cleanup
rubot --date 2025-07-17 --skip-cleanup
```

### 🛠️ CLI Options

| Option | Description | Default | Environment Variable |
|--------|-------------|----------|---------------------|
| `--date` | 📅 Date in YYYY-MM-DD format | today | - |
| `--output` | 📁 Output file path | stdout | - |
| `--prompt` | 📝 Path to system prompt file | - | DEFAULT_PROMPT_FILE |
| `--model` | 🤖 OpenRouter model ID | - | DEFAULT_MODEL |
| `--temperature` | 🌡️ LLM temperature | 0.8 | DEFAULT_TEMPERATURE |
| `--max-tokens` | 🔢 Maximum tokens for response | 4000 | DEFAULT_MAX_TOKENS |
| `--config` | ⚙️ Path to config file | .env | - |
| `--no-cache` | 🚫 Disable caching | false | CACHE_ENABLED=false |
| `--cache-dir` | 📂 Custom cache directory | System temp | CACHE_DIR |
| `--cache-cleanup-days` | 🧹 Delete cache files after N days | 14 | CACHE_CLEANUP_DAYS |
| `--skip-cleanup` | 🚫 Skip cache cleanup | false | SKIP_CLEANUP=1 |
| `--verbose` | 🔍 Enable debug output | false | LOG_LEVEL=DEBUG |
| `-h/--help` | ❓ Show help message | - | - |
| `--version` | 🔢 Show version number | - | - |

### 📝 Prompt File Validation

rubot validates **early** that prompt files exist before starting PDF downloads:

```bash
# ❌ Fails with clear error message (before PDF download)
rubot --prompt /nonexistent/prompt.txt --date 2024-01-15
# Error: Prompt file not found: /nonexistent/prompt.txt

# ❌ Also for DEFAULT_PROMPT_FILE from environment variables
DEFAULT_PROMPT_FILE=/missing/prompt.txt rubot --date 2024-01-15
# Error: Prompt file not found: /missing/prompt.txt

# ✅ Works with valid prompt file
rubot --prompt prompts/default.txt --date 2024-01-15

# ✅ Or with DEFAULT_SYSTEM_PROMPT (no file required)
DEFAULT_SYSTEM_PROMPT="Analyze the document..." rubot --date 2024-01-15
```

**Benefits:**
- 🚀 **Fast failure**: No time wasted downloading PDFs
- 🐳 **Docker-friendly**: Catches volume mount issues early
- 🔍 **Clear error messages**: Shows exactly which file is missing

## 🐳 Docker Usage

### ⚠️ Virtualization Notice

**Important for VM users:** Avoid using the `qemu64` CPU architecture in virtual machines as it can cause PyTorch to crash. See the [Virtualization Documentation](docs/VIRTUALIZATION.md) for more details.

### 🚢 Using Pre-built Image

```bash
docker run --rm \
  -e OPENROUTER_API_KEY=your_key \
  -e DEFAULT_MODEL=your_model \
  -e CACHE_CLEANUP_DAYS=7 \
  -v $(pwd)/output:/app/output \
  ghcr.io/rmoriz/rubot:latest \
  --date 2024-01-15 --output /app/output/result.json
```

### 🐙 Docker Compose

<details>
<summary>Click to see docker-compose.yml</summary>

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
      - CACHE_CLEANUP_DAYS=14
    volumes:
      - ./cache:/app/cache
      - ./output:/app/output
      - ./prompts:/app/prompts  # Mount prompt files
    command: ["--date", "2024-01-15", "--output", "/app/output/result.json", "--prompt", "/app/prompts/default.txt"]
```

</details>

## 🧠 Model Selection

rubot works with **any OpenRouter-compatible model**. Choose based on your needs:

### 🏆 Recommended Models

| Model | Provider | Best For | Cost |
|-------|----------|----------|------|
| `moonshotai/kimi-k2:free` | Moonshot AI | 📝 Text analysis, reasoning | Free |
| `x-ai/grok-3-mini` | xAI | 🎯 Fast, reliable | Cheap |

> 💡 **Tip**: Start with the free `moonshotai/kimi-k2:free` for text analysis.

📋 See the complete list at [OpenRouter Models](https://openrouter.ai/models)

## 📊 Output Format

The tool outputs **structured JSON** with extracted information:

<details>
<summary>📋 <strong>Example Output</strong></summary>

```json
{
  "issue": "134",
  "year": "2025",
  "id": "2025-07-17",
  "summary": "Rathaus-Umschau 134/2025: Sanierung Markt Wiener Platz, Neubau Thomas-Wimmer-Haus in Laim...",
  "social_media_post": "# KI-Kommentar zur Rathaus-Umschau 134 vom 17.07.2025...",
  "announcements": [
    {
      "title": "Markt am Wiener Platz wird saniert",
      "description": "Großreparatur statt Neubau: 3 Mio € Eigenfinanzierung...",
      "category": "construction",
      "date": "Ende 2027",
      "location": "Wiener Platz, Haidhausen"
    }
  ],
  "events": [
    {
      "title": "Eröffnung naturnaher Pausenhof Guardinistraße 60",
      "date": "18. Juli 2025",
      "time": "14:00",
      "location": "Grund- und Mittelschule Guardinistraße 60",
      "description": "Erster naturnaher Pausenhof Münchens mit Bürgermeisterin Dietl"
    }
  ],
  "important_dates": [
    {
      "description": "Akkreditierung für OEZ-Gedenkveranstaltung",
      "date": "19. Juli 2025",
      "details": "für Medienvertreter*innen"
    }
  ]
}
```

</details>

### 📈 Data Structure

- **📝 Summary**: AI-generated overview of the document
- **📢 Announcements**: Municipal decisions, policy changes, public notices
- **🎉 Events**: Upcoming events, meetings, public gatherings  
- **📊 Metadata**: Processing information and source details

## 👨‍💻 Development

### 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rubot --cov-report=html

# Run specific test file
pytest tests/test_simple.py -v
```

### 🔍 Code Quality

```bash
# 🧹 Linting
flake8 rubot/

# 🔍 Type checking  
mypy rubot/

# ✨ Formatting
black rubot/
```

### 📁 Project Structure

```
rubot/
├── 🤖 rubot/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py          # 🖥️ CLI interface
│   ├── config.py       # ⚙️ Configuration management
│   ├── downloader.py   # 📥 PDF downloading
│   ├── llm.py          # 🧠 OpenRouter API integration
│   ├── cache.py        # 💾 Caching functionality
│   ├── retry.py        # 🔄 Retry mechanisms
│   ├── models.py       # 📊 Data models
│   ├── logger.py       # 📝 Logging configuration
│   └── utils.py        # 🛠️ Utility functions
├── 🧪 tests/           # Test suite
├── 💬 prompts/         # System prompt templates
└── 📖 docs/            # Documentation
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. 🍴 **Fork** the repository
2. 🌿 **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. ✨ **Make** your changes
4. 🧪 **Add** tests for new functionality
5. ✅ **Ensure** all tests pass
6. 📝 **Commit** your changes (`git commit -m 'Add amazing feature'`)
7. 🚀 **Push** to the branch (`git push origin feature/amazing-feature`)
8. 🎯 **Submit** a pull request

### 💡 Ideas for Contributions

- 🌍 **Internationalization**: Support for other languages
- 📊 **Export formats**: CSV, Excel, XML output options
- 🔌 **Integrations**: Slack, Discord, email notifications
- 🎨 **UI**: Web interface or desktop app
- 📈 **Analytics**: Trend analysis and reporting

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

### ✅ Dependencies and Licensing

This project uses [Docling](https://github.com/docling-project/docling) for PDF to Markdown conversion. Docling is available under the MIT License.

**Docling Model Data:** The pre-trained models and training data included in Docker images from Docling are licensed under **CDLA-Permissive-2.0**. This license permits commercial use and redistribution of the model data.

## 🆘 Support & Community

<div align="center">

[![GitHub Issues](https://img.shields.io/github/issues/rmoriz/rubot)](https://github.com/rmoriz/rubot/issues)
[![GitHub Discussions](https://img.shields.io/github/discussions/rmoriz/rubot)](https://github.com/rmoriz/rubot/discussions)
[![GitHub Stars](https://img.shields.io/github/stars/rmoriz/rubot?style=social)](https://github.com/rmoriz/rubot/stargazers)

**[🐛 Report Bug](https://github.com/rmoriz/rubot/issues/new?template=bug_report.md)** • **[💡 Request Feature](https://github.com/rmoriz/rubot/issues/new?template=feature_request.md)** • **[💬 Discussions](https://github.com/rmoriz/rubot/discussions)**

</div>

---

<div align="center">

**Made with ❤️ for the Munich community**

*If you find rubot useful, please consider giving it a ⭐ on GitHub!*

</div>