#!/bin/bash
# Installation script for rubot v0.2.0

set -e

echo "> Installing rubot CLI tool v0.2.0..."

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.13"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "L Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo " Python version check passed: $python_version"

# Check for required system dependencies
if ! command -v git &> /dev/null; then
    echo "L Error: git is required but not installed"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "L Error: pip is required but not installed"
    exit 1
fi

echo " System dependencies check passed"

# Create virtual environment
echo "=� Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "  Upgrading pip..."
pip install --upgrade pip

# Install project dependencies
echo "=� Installing project dependencies..."
pip install -r requirements.txt

# Install project in development mode
echo "=' Installing rubot in development mode..."
pip install -e .

# Create .env template
if [ ! -f .env ]; then
    echo "=� Creating .env template..."
    cat > .env << EOF
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Default LLM Model (optional)
DEFAULT_MODEL=moonshotai/kimi-k2:free

# Cache Settings
CACHE_ENABLED=true
CACHE_MAX_AGE_HOURS=24

# Processing Settings
MAX_PDF_PAGES=100

# Docling Settings
DOCLING_DO_TABLE_STRUCTURE=false
DOCLING_DO_OCR=true
EOF
    echo "=� Please edit .env and add your OPENROUTER_API_KEY"
fi

echo ""
echo "<� Installation complete!"
echo ""
echo "To use rubot:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Edit .env and add your OpenRouter API key"
echo "  3. Run: rubot --help"
echo ""
echo "Example usage:"
echo "  rubot --date 2024-01-15 --output result.json"
echo "  rubot --pdf document.pdf --output summary.md"
echo ""
echo "To run tests:"
echo "  pytest"
echo "  mypy"
echo ""