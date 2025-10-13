#!/bin/bash
# Test runner script for generador.py test suite

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "========================================="
echo "Running generador.py Test Suite"
echo "========================================="
echo ""

# Check if gcc is available
if ! command -v gcc &> /dev/null; then
    echo "WARNING: gcc not found. Some tests may fail."
    echo ""
fi

# Run tests with unittest
echo "Running tests with unittest..."
python3 -m unittest discover tests/ -v

echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo "All tests completed!"
