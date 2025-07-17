# Rubot Justfile - Development commands with venv management

# Default recipe when just is called without arguments
default:
    @just --list

# Set venv path
venv_path := "venv"

# Check if venv exists
venv_exists := if path_exists(venv_path) == "true" { "true" } else { "false" }

# Initialize virtual environment if it doesn't exist
init-venv:
    #!/usr/bin/env bash
    if [ ! -d "{{venv_path}}" ]; then
        echo "Creating virtual environment..."
        python3 -m venv {{venv_path}}
    else
        echo "Virtual environment already exists"
    fi

# Install dependencies
install: init-venv
    #!/usr/bin/env bash
    source {{venv_path}}/bin/activate
    pip install --upgrade pip
    pip install -e .
    pip install -r requirements.txt

# Install development dependencies
install-dev: init-venv
    #!/usr/bin/env bash
    source {{venv_path}}/bin/activate
    pip install --upgrade pip
    pip install -e .[dev]
    pip install -r requirements.txt

# Run all tests
test: init-venv
    #!/usr/bin/env bash
    source {{venv_path}}/bin/activate
    pytest tests/ -v

# Run tests with coverage
test-cov: init-venv
    #!/usr/bin/env bash
    source {{venv_path}}/bin/activate
    pytest tests/ --cov=rubot --cov-report=html --cov-report=term-missing

# Run specific test file
test-file TEST_FILE: init-venv
    #!/usr/bin/env bash
    source {{venv_path}}/bin/activate
    pytest "{{TEST_FILE}}" -v

# Run only fast tests
test-fast: init-venv
    #!/usr/bin/env bash
    source {{venv_path}}/bin/activate
    pytest tests/ -v -m "not slow"

# Lint code
lint: init-venv
    #!/usr/bin/env bash
    source {{venv_path}}/bin/activate
    flake8 rubot/ tests/

# Format code
format: init-venv
    #!/usr/bin/env bash
    source {{venv_path}}/bin/activate
    black rubot/ tests/

# Type checking
type-check: init-venv
    #!/usr/bin/env bash
    source {{venv_path}}/bin/activate
    mypy rubot/

# Run the application
run *ARGS:
    #!/usr/bin/env bash
    source {{venv_path}}/bin/activate
    rubot {{ARGS}}

# Run the application with debug info
run-debug *ARGS:
    #!/usr/bin/env bash
    source {{venv_path}}/bin/activate
    python -m rubot.cli {{ARGS}}

# Clean up build artifacts
clean:
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf .pytest_cache/
    rm -rf .mypy_cache/
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

# Full clean including venv
clean-all: clean
    rm -rf {{venv_path}}

# Build package
build: init-venv
    #!/usr/bin/env bash
    source {{venv_path}}/bin/activate
    python -m build

# Run all quality checks
quality: format lint type-check test

# Development setup - install everything and run tests
setup: install-dev test

# Development workflow - format, lint, test
dev: format lint test

# Help command
help:
    @echo "Rubot Development Commands:"
    @echo "  setup        - Install dev dependencies and run tests"
    @echo "  install      - Install dependencies"
    @echo "  install-dev  - Install dev dependencies"
    @echo "  test         - Run all tests"
    @echo "  test-cov     - Run tests with coverage"
    @echo "  test-file    - Run specific test file"
    @echo "  test-fast    - Run only fast tests"
    @echo "  lint         - Run flake8 linter"
    @echo "  format       - Format code with black"
    @echo "  type-check   - Run mypy type checking"
    @echo "  run          - Run the application"
    @echo "  run-debug    - Run with debug info"
    @echo "  dev          - Format, lint, and test"
    @echo "  quality      - Full quality check"
    @echo "  build        - Build package"
    @echo "  clean        - Clean build artifacts"
    @echo "  clean-all    - Clean everything including venv"