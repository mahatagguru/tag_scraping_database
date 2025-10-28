#!/bin/bash

# Quality checks script for TAG Grading Scraper
# This script runs all the code quality checks

set -e

echo "🔍 Running Code Quality Checks..."
echo "================================="

# Change to project root
cd "$(dirname "$0")/.."

echo ""
echo "1. Running Black formatting check..."
echo "-----------------------------------"
if python3 -m black --check src/scraper/ run_async_pipeline.py test_performance.py; then
    echo "✅ Black check passed"
else
    echo "❌ Black check failed - run 'python3 -m black src/scraper/ run_async_pipeline.py test_performance.py' to fix"
fi

echo ""
echo "2. Running isort import sorting check..."
echo "---------------------------------------"
if python3 -m isort --check-only src/scraper/ run_async_pipeline.py test_performance.py --profile black; then
    echo "✅ isort check passed"
else
    echo "❌ isort check failed - run 'python3 -m isort src/scraper/ run_async_pipeline.py test_performance.py --profile black' to fix"
fi

echo ""
echo "3. Running flake8 linting check..."
echo "---------------------------------"
if python3 -m flake8 src/scraper/ run_async_pipeline.py test_performance.py; then
    echo "✅ flake8 check passed"
else
    echo "❌ flake8 check failed - see output above for details"
fi

echo ""
echo "4. Running mypy type checking..."
echo "-------------------------------"
if python3 -m mypy src/scraper/ run_async_pipeline.py test_performance.py --ignore-missing-imports; then
    echo "✅ mypy check passed"
else
    echo "⚠️  mypy check found issues - see output above for details"
fi

echo ""
echo "5. Running pylint code quality check..."
echo "--------------------------------------"
if python3 -m pylint src/scraper/ run_async_pipeline.py test_performance.py --max-line-length=88 --disable=C0114,C0103,R0913; then
    echo "✅ pylint check passed"
else
    echo "⚠️  pylint check found issues - see output above for details"
fi

echo ""
echo "================================="
echo "🎉 Quality checks completed!"
echo ""
echo "To fix formatting issues, run:"
echo "  python3 -m black src/scraper/ run_async_pipeline.py test_performance.py"
echo "  python3 -m isort src/scraper/ run_async_pipeline.py test_performance.py --profile black"
echo ""
echo "For pre-commit hooks, run:"
echo "  pre-commit run --all-files"
