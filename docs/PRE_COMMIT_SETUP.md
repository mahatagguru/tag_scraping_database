# Pre-commit Setup Guide

This document explains how to set up and use pre-commit hooks for the TAG Grading Scraper project to ensure consistent code quality and formatting.

## Overview

Pre-commit hooks automatically run code quality checks before each commit, ensuring that all code meets the project's standards. This prevents poorly formatted or low-quality code from being committed to the repository.

## Setup

### 1. Install Pre-commit

```bash
pip install pre-commit
```

### 2. Install Hooks

```bash
pre-commit install
```

This will install the hooks defined in `.pre-commit-config.yaml` into your `.git/hooks/` directory.

### 3. Run Hooks Manually

To run all hooks on all files:

```bash
pre-commit run --all-files
```

To run hooks on specific files:

```bash
pre-commit run --files src/scraper/async_pipeline.py
```

## Configuration

### Pre-commit Configuration (`.pre-commit-config.yaml`)

The project uses a focused configuration that applies quality checks only to core files:

- **Black**: Python code formatting (88 character line length)
- **isort**: Import sorting (compatible with Black)
- **flake8**: Linting with relaxed rules
- **General hooks**: Trailing whitespace, end-of-file fixes, YAML/JSON validation, etc.

### Flake8 Configuration (`.flake8`)

The flake8 configuration includes:
- 88 character line length limit
- Ignores E203 (whitespace before ':') and W503 (line break before binary operator)
- Excludes common directories like `.git`, `__pycache__`, `.venv`, etc.

### PyProject Configuration (`pyproject.toml`)

Contains tool-specific configurations for:
- Black formatting settings
- isort import sorting (Black-compatible profile)
- mypy type checking settings
- pylint code quality settings

## Quality Checks

### 1. Black (Code Formatting)

Ensures consistent Python code formatting:

```bash
python3 -m black src/scraper/ run_async_pipeline.py test_performance.py
```

### 2. isort (Import Sorting)

Sorts and organizes imports:

```bash
python3 -m isort src/scraper/ run_async_pipeline.py test_performance.py --profile black
```

### 3. flake8 (Linting)

Checks for code style and potential issues:

```bash
python3 -m flake8 src/scraper/ run_async_pipeline.py test_performance.py
```

### 4. mypy (Type Checking)

Performs static type checking:

```bash
python3 -m mypy src/scraper/ run_async_pipeline.py test_performance.py --ignore-missing-imports
```

### 5. pylint (Code Quality)

Analyzes code quality and complexity:

```bash
python3 -m pylint src/scraper/ run_async_pipeline.py test_performance.py --max-line-length=88 --disable=C0114,C0103,R0913
```

## Quick Quality Check Script

Use the provided script to run all quality checks:

```bash
./scripts/run_quality_checks.sh
```

This script will:
1. Check Black formatting
2. Check isort import sorting
3. Run flake8 linting
4. Run mypy type checking
5. Run pylint code quality analysis

## Troubleshooting

### Black Python Version Issue

If you encounter the error:
```
Python 3.12.5 has a memory safety issue that can cause Black's AST safety checks to fail. Please upgrade to Python 3.12.6 or downgrade to Python 3.12.4
```

**Solutions:**
1. Upgrade to Python 3.12.6: `pyenv install 3.12.6`
2. Downgrade to Python 3.12.4: `pyenv install 3.12.4`
3. Use the manual quality check script instead

### Pre-commit Hooks Not Running

If hooks aren't running automatically:

1. Ensure hooks are installed: `pre-commit install`
2. Check if hooks are executable: `ls -la .git/hooks/`
3. Run manually to test: `pre-commit run --all-files`

### Flake8 Configuration Issues

If flake8 reports configuration errors:

1. Check `.flake8` file syntax
2. Ensure no spaces around commas in `extend-ignore`
3. Verify file paths in `exclude` section

## Best Practices

1. **Run checks before committing**: Always run `pre-commit run --all-files` before pushing
2. **Fix issues immediately**: Don't commit with failing hooks
3. **Keep configuration updated**: Regularly update hook versions in `.pre-commit-config.yaml`
4. **Use focused checks**: The configuration only checks core files to avoid overwhelming output

## Integration with CI/CD

The pre-commit configuration is designed to work with CI/CD pipelines:

- Hooks can be run in CI environments
- Configuration is version-controlled
- Consistent checks across all environments

## File Coverage

The current configuration focuses on these core files:
- `src/scraper/` - Main scraping logic
- `run_async_pipeline.py` - Main pipeline runner
- `test_performance.py` - Performance tests

Other files (like `backend/`, `src/mcp/`, etc.) are excluded to focus on the most critical code paths.

## Updating Hooks

To update all hooks to their latest versions:

```bash
pre-commit autoupdate
```

This will update the `rev` field in `.pre-commit-config.yaml` to the latest versions.

## Summary

Pre-commit hooks provide an automated way to maintain code quality. The current setup focuses on the core scraping functionality while being practical and not overwhelming developers with too many checks on legacy code.

For any issues or questions, refer to the individual tool documentation or run the quality check script for detailed output.
