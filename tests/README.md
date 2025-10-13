# Test Suite for generador.py

This directory contains comprehensive tests for the `generador.py` script.

## Test Coverage

The test suite covers all basic and optional features:

### Basic Features (Required)
- **Minimal template**: Only `/*name*/` section and code
- **Dynamic variables**: `/*var*/` section with ranges and lists
- **Question statements**: Intro and outro comments (`//`)

### Optional Features
- **`/*opciones*/`**: Fixed incorrect answer options
- **`/*distractors*/`**: Dynamic incorrect answers using Python expressions
- **`/*correcta*/`**: Fixed correct answer (skips compilation)
- **`/*STDIN*/`**: Standard input for programs using scanf/fgets

### Feature Combinations
All possible combinations of optional features are tested:
- Variables + Fixed options
- Variables + Distractors
- Variables + STDIN
- Fixed options + Distractors
- All features combined
- Fixed answer + Fixed options

### Command-Line Options
- `-s/--source`: Custom source directory
- `-o/--output`: Custom output file name
- `-n/--num`: Number of variants to generate
- `-c/--category`: Custom Moodle category name
- `-t/--template`: Single template processing
- `-g/--generate-only`: Generate C code without XML

### Additional Tests
- Category hierarchy based on directory structure
- Error handling for malformed templates
- Direct testing of parsing functions

## Running Tests

Run all tests:
```bash
cd /home/mrtin/dev/p1/idkfa
python3 -m pytest tests/ -v
```

Or using unittest:
```bash
python3 -m unittest discover tests/ -v
```

Run specific test class:
```bash
python3 -m unittest tests.test_generador.TestGeneradorBasicFeatures -v
```

Run specific test:
```bash
python3 -m unittest tests.test_generador.TestGeneradorBasicFeatures.test_minimal_template -v
```

## Test Structure

- `TestGeneradorBasicFeatures`: Tests for required features
- `TestGeneradorOptionalFeatures`: Tests for individual optional features
- `TestGeneradorCombinedFeatures`: Tests for feature combinations
- `TestGeneradorCommandLineOptions`: Tests for CLI arguments
- `TestGeneradorCategoryStructure`: Tests for Moodle category generation
- `TestGeneradorErrorHandling`: Tests for error cases
- `TestGeneradorParsingFunctions`: Direct unit tests for parsing functions

## Requirements

- Python 3.6+
- gcc (for compilation tests)
- Standard Python libraries (unittest, xml.etree.ElementTree, tempfile, subprocess)

## Notes

- Tests create temporary directories for templates and outputs
- All temporary files are cleaned up after tests
- Tests validate both XML generation and structure
- Error cases are tested to ensure graceful degradation
