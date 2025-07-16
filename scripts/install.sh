#!/bin/bash
# Installation script for rubot

set -e

echo "🤖 Installing rubot CLI tool..."

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.13"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv rubot-env
source rubot-env/bin/activate

# Install rubot
echo "⬇️  Installing rubot..."
pip install --upgrade pip
pip install git+https://github.com/rmoriz/rubot.git

# Install marker-pdf
echo "📄 Installing marker-pdf..."
pip install git+https://github.com/datalab-to/marker.git

# Create .env template
if [ ! -f .env ]; then
    echo "📝 Creating .env template..."
    cat > .env << EOF
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Default LLM Model (optional)
DEFAULT_MODEL=anthropic/claude-3-haiku

# Cache Settings
CACHE_ENABLED=true
CACHE_MAX_AGE_HOURS=24

# Processing Settings
MAX_PDF_PAGES=100
EOF
    echo "📋 Please edit .env and add your OPENROUTER_API_KEY"
fi

echo "🎉 Installation complete!"
echo ""
echo "To use rubot:"
echo "  1. Activate the virtual environment: source rubot-env/bin/activate"
echo "  2. Edit .env and add your OpenRouter API key"
echo "  3. Run: rubot --help"
echo ""
echo "Example usage:"
echo "  rubot --date 2024-01-15 --output result.json"