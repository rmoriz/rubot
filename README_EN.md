<div align="center">

# 🤖 rubot

**AI-Powered Munich Rathaus-Umschau PDF Processor**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Docker](https://img.shields.io/badge/docker-available-blue.svg)](https://github.com/rmoriz/rubot/pkgs/container/rubot)
[![Tests](https://github.com/rmoriz/rubot/workflows/Test%20rubot/badge.svg)](https://github.com/rmoriz/rubot/actions)

*Automate the extraction and analysis of Munich's official municipal announcements*

[🚀 Quick Start](#-quick-start) • [📖 Documentation](#-configuration) • [🐳 Docker](#-docker-usage) • [🤝 Contributing](#-contributing)

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
2. **🔄 Converts** PDFs to clean Markdown using `PyMuPDF`
3. **🧠 Analyzes** content with your choice of AI model via OpenRouter
4. **📤 Outputs** structured JSON with extracted announcements and events

## 🚀 Quick Start

### 📋 Prerequisites

- 🐍 **Python 3.13+**
- 🔑 **OpenRouter API key** ([Get yours here](https://openrouter.ai/))
- 💾 **1-2GB RAM** (for PDF conversion with `PyMuPDF`, also in Docker)

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
pip install -r requirements.txt
```

</details>

## ⚙️ Configuration

Create a `.env` file with your settings:

<details>
<summary>📝 <strong>Required Configuration</strong></summary>

```bash
# 🔑 API Configuration (Required)
OPENROUTER_API_KEY=your_openrouter_api_key_here
DEFAULT_MODEL=your_preferred_model_here

# 💬 System Prompt (Required - choose one)
DEFAULT_SYSTEM_PROMPT="Analyze the following Rathaus-Umschau content..."
# OR use a prompt file:
# DEFAULT_PROMPT_FILE=prompts/default.txt
```

</details>

<details>
<summary>🔧 <strong>Optional Configuration</strong></summary>

```bash
# 🌐 Network Settings
REQUEST_TIMEOUT=120
OPENROUTER_TIMEOUT=120
MARKER_TIMEOUT=600
MAX_RETRIES=3
RETRY_DELAY=1.0

# 💾 Cache Settings
CACHE_ENABLED=true
CACHE_DIR=
CACHE_MAX_AGE_HOURS=24

# 📄 Processing Settings
MAX_PDF_PAGES=100

# 📊 Output Settings
OUTPUT_FORMAT=json
JSON_INDENT=2
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
```

### 🛠️ CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--date` | 📅 Date in YYYY-MM-DD format | today |
| `--output` | 📁 Output file path | stdout |
| `--prompt` | 📝 Path to system prompt file | - |
| `--model` | 🤖 OpenRouter model ID | from config |
| `--temperature` | 🌡️ LLM temperature | 0.1 |
| `--max-tokens` | 🔢 Maximum tokens for response | 4000 |
| `--verbose` | 🔍 Enable debug output | false |
| `--help` | ❓ Show help message | - |

## 🐳 Docker Usage

### 🚢 Using Pre-built Image

```bash
docker run --rm \
  -e OPENROUTER_API_KEY=your_key \
  -e DEFAULT_MODEL=your_model \
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
    volumes:
      - ./cache:/app/cache
      - ./output:/app/output
    command: ["--date", "2024-01-15", "--output", "/app/output/result.json", "--verbose"]
```

</details>

## 🧠 Model Selection

rubot works with **any OpenRouter-compatible model**. Choose based on your needs:

### 🏆 Recommended Free Models

| Model | Provider | Best For | Cost |
|-------|----------|----------|------|
| `moonshotai/kimi-k2:free` | Moonshot AI | 📝 Text analysis, reasoning | Free |
| `x-ai/grok-3-mini` | xAI | 🎯 Fast, reliable | Free |

> 💡 **Tip**: These free models provide excellent performance for Rathaus-Umschau analysis. Start with `moonshotai/kimi-k2:free` for comprehensive text analysis.

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
  "summary": "Rathaus-Umschau 134/2025: Sanierung Markt Wiener Platz, Neubau Thomas-Wimmer-Haus in Laim, neue Feuerwache 3 in Laim, Gedenkveranstaltung 9. Jahrestag OEZ-Attentat, Baustellen-Radverkehr, Vandalismus Zierbrunnen Harras, Ausstellungen Mode- und Designschulen.",
  "social_media_post": "# KI-Kommentar zur Rathaus-Umschau 134 vom 17.07.2025\n\n## Baustellen-Radverkehr: Endlich Priorität?\nGrüne fordern Fuß- \u0026 Radverkehr vor MIV bei Baustellen. MobRef antwortet: „Ist schon lange so.“ Wirklich? Dann zeigt’s mal, statt nur davon zu reden!\n\n## Feuerwache 3 Laim: 10-Meter-Fahrrad-Freistreifen\nImmerhin: Für den neuen Standort wird ein 10 m breiter Streifen für „künftigen Fußgänger- und Fahrradsteg“ freigehalten. Bleibt nur zu hoffen, dass daraus mehr wird als ein Schmierzettel im Plan.\n\nQuelle: https://ru.muenchen.de/2025/134",
  "announcements": [
    {
      "title": "Markt am Wiener Platz wird saniert",
      "description": "Großreparatur statt Neubau: 3 Mio € Eigenfinanzierung, Interimsmarkt ab Frühjahr 2026, Fertigung Ende 2027",
      "category": "construction",
      "date": "Ende 2027",
      "location": "Wiener Platz, Haidhausen"
    },
    {
      "title": "Neubau Thomas-Wimmer-Haus in der „Alten Heimat“",
      "description": "159 barrierefreie Wohnungen + Tagespflege, Baubeginn Herbst 2026, Fertigstellung Ende 2029",
      "category": "construction",
      "date": "Ende 2029",
      "location": "Laim"
    },
    {
      "title": "Neue Feuerwache 3 in Laim",
      "description": "Ersatz für Schwanthalerhöhe, Generalübernehmer-Verfahren, Baustart nach DB-Räumung Ende 2026",
      "category": "construction",
      "date": "Ende 2026",
      "location": "Landsberger Str. 332"
    },
    {
      "title": "Zierbrunnen am Harras wieder beschädigt",
      "description": "Vandalismus kostet 15 000 €, Wiederinbetriebnahme Ende Juli geplant",
      "category": "public services",
      "date": "Ende Juli 2025",
      "location": "Harras"
    }
  ],
  "events": [
    {
      "title": "Eröffnung naturnaher Pausenhof Guardinistraße 60",
      "date": "18. Juli 2025",
      "time": "14:00",
      "location": "Grund- und Mittelschule Guardinistraße 60",
      "description": "Erster naturnaher Pausenhof Münchens mit Bürgermeisterin Dietl"
    },
    {
      "title": "Enthüllung „Ort der Demokratie“ Prannerstraße 8",
      "date": "18. Juli 2025",
      "time": "15:00",
      "location": "Foyer MEAG, Prannerstraße 8",
      "description": "Ehrung durch Landtagspräsidentin Aigner und OB Reiter"
    },
    {
      "title": "Kunstprojekt „Menzinga“",
      "date": "18. Juli 2025",
      "time": "16:00",
      "location": "Fußgänger-Unterführung S-Bahnhof Untermenzing",
      "description": "800 m² Wandbild von Martin Blumöhr"
    },
    {
      "title": "Gedenken Reichsbahnlager Neuaubing",
      "date": "18. Juli 2025",
      "time": "16:00",
      "location": "Erinnerungsort Neuaubing, Ehrenbürgstraße 9",
      "description": "Gedenkzeichen für 11 Zwangsarbeiter*innen"
    },
    {
      "title": "Eröffnung Spielplatz Gollierplatz",
      "date": "21. Juli 2025",
      "time": "12:30",
      "location": "Gollierplatz",
      "description": "Neuer inklusiver Spielplatz mit Wasserspielbereich"
    },
    {
      "title": "JEF-EU-Planspiel im Landtag",
      "date": "21. Juli 2025",
      "time": "14:00",
      "location": "Bayerischer Landtag, Max-Planck-Straße 1",
      "description": "100 Schüler*innen simulieren EU-Parlament"
    },
    {
      "title": "Designpreis „Goldenes Pony“",
      "date": "22. Juli 2025",
      "time": "20:00",
      "location": "Roßmarkt 15",
      "description": "Verleihung mit Stadtschulrat Kraus"
    },
    {
      "title": "Modenschau Meisterschule für Mode",
      "date": "24. Juli 2025",
      "time": "20:00",
      "location": "Muffathalle, Zellstraße 4",
      "description": "Premiere der Kollektionen „Breaking Patterns“"
    }
  ],
  "important_dates": [
    {
      "description": "Akkreditierung für OEZ-Gedenkveranstaltung",
      "date": "19. Juli 2025",
      "details": "für Medienvertreter*innen"
    },
    {
      "description": "Akkreditierung Modenschau",
      "date": "23. Juli 2025, 16:00",
      "details": "bei presse.rbs@muenchen.de"
    },
    {
      "description": "Ausstellung Wettbewerbsergebnisse Ramersdorf",
      "date": "7. August 2025",
      "details": "täglich 8–20 Uhr, Blumenstraße 28b"
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

<details>
<summary>🧪 <strong>Running Tests</strong></summary>

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rubot --cov-report=html

# Run specific test file
pytest tests/test_simple.py -v
```

</details>

<details>
<summary>🔍 <strong>Code Quality</strong></summary>

```bash
# 🧹 Linting
flake8 rubot/

# 🔍 Type checking  
mypy rubot/

# ✨ Formatting
black rubot/
```

</details>

<details>
<summary>📁 <strong>Project Structure</strong></summary>

```
rubot/
├── 🤖 rubot/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py          # 🖥️ CLI interface
│   ├── config.py       # ⚙️ Configuration management
│   ├── downloader.py   # 📥 PDF downloading
│   ├── marker.py       # 🔄 PDF to Markdown conversion
│   ├── llm.py          # 🧠 OpenRouter API integration
│   ├── cache.py        # 💾 Caching functionality
│   ├── retry.py        # 🔄 Retry mechanisms
│   ├── models.py       # 📊 Data models
│   └── utils.py        # 🛠️ Utility functions
├── 🧪 tests/           # Test suite
├── 📚 examples/        # Usage examples
├── 💬 prompts/         # System prompt templates
└── 📖 docs/            # Documentation
```

</details>

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

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

### ✅ Licensing

This project uses `PyMuPDF` (AGPL-3.0) for PDF to Markdown conversion, which enables commercial usage. The AGPL license requires that all derivative works are also published under AGPL.

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