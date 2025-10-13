# Test Suite Usage Guide

Complete guide for using the generador.py test suite.

## Installation & Setup

No installation required! The test suite uses only Python standard library.

### Prerequisites

```bash
# Verify Python 3.6+
python3 --version

# Verify GCC (required for compilation tests)
gcc --version

# Navigate to project root
cd /home/mrtin/dev/p1/idkfa
```

## Running Tests

### Method 1: Using unittest (Recommended)

```bash
# Run all tests with verbose output
python3 -m unittest discover tests/ -v

# Run all tests (quiet mode)
python3 -m unittest discover tests/

# Run with test discovery from different location
python3 -m unittest discover -s tests/ -p 'test_*.py' -v
```

### Method 2: Using the Shell Script

```bash
# Make executable (first time only)
chmod +x tests/run_tests.sh

# Run tests
./tests/run_tests.sh
```

### Method 3: Direct Execution

```bash
# Run the test file directly
python3 tests/test_generador.py
```

## Running Specific Tests

### Run Single Test Class

```bash
# Test basic features only
python3 -m unittest tests.test_generador.TestGeneradorBasicFeatures -v

# Test optional features
python3 -m unittest tests.test_generador.TestGeneradorOptionalFeatures -v

# Test CLI options
python3 -m unittest tests.test_generador.TestGeneradorCommandLineOptions -v

# Test combined features
python3 -m unittest tests.test_generador.TestGeneradorCombinedFeatures -v

# Test error handling
python3 -m unittest tests.test_generador.TestGeneradorErrorHandling -v

# Test parsing functions
python3 -m unittest tests.test_generador.TestGeneradorParsingFunctions -v

# Test category structure
python3 -m unittest tests.test_generador.TestGeneradorCategoryStructure -v
```

### Run Single Test Method

```bash
# Test minimal template
python3 -m unittest tests.test_generador.TestGeneradorBasicFeatures.test_minimal_template -v

# Test STDIN functionality
python3 -m unittest tests.test_generador.TestGeneradorOptionalFeatures.test_template_with_stdin -v

# Test variable substitution
python3 -m unittest tests.test_generador.TestGeneradorBasicFeatures.test_template_with_variables -v

# Test all features combined
python3 -m unittest tests.test_generador.TestGeneradorCombinedFeatures.test_all_features_except_correcta -v
```

## Testing with Example Templates

### Generate Questions from Examples

```bash
# Test minimal example
python3 generador.py -t tests/examples/01_minimal.c -n 5 -o /tmp/test_minimal.xml

# Test variables example
python3 generador.py -t tests/examples/02_with_variables.c -n 10 -o /tmp/test_vars.xml

# Test STDIN example
python3 generador.py -t tests/examples/05_with_stdin.c -n 5 -o /tmp/test_stdin.xml

# Test all features example
python3 generador.py -t tests/examples/07_all_features.c -n 7 -o /tmp/test_all.xml
```

### Generate C Code Only (for verification)

```bash
# Generate code without XML
python3 generador.py -t tests/examples/02_with_variables.c -n 3 -g

# Check generated code
ls -la generated/
cat generated/02_with_variables/02_with_variables_v1.c

# Compile and test manually
cd generated && make
./02_with_variables/02_with_variables_v1
```

### Process All Examples at Once

```bash
# Generate XML from all examples
python3 generador.py -s tests/examples -n 3 -o /tmp/all_examples.xml

# Generate code from all examples
python3 generador.py -s tests/examples -n 2 -g
```

## Understanding Test Output

### Successful Test Run

```
test_minimal_template ... ok
test_template_with_variables ... ok
...
----------------------------------------------------------------------
Ran 25 tests in 3.194s

OK
```

### Failed Test

```
test_custom_num_variants ... FAIL
...
======================================================================
FAIL: test_custom_num_variants
----------------------------------------------------------------------
Traceback (most recent call last):
  ...
AssertionError: Expected 7 questions, got 3
```

### Test with Errors

```
test_compilation_error ... ERROR
...
======================================================================
ERROR: test_compilation_error
----------------------------------------------------------------------
Traceback (most recent call last):
  ...
RuntimeError: GCC not found
```

## Debugging Tests

### Verbose Output

```bash
# Maximum verbosity
python3 -m unittest tests.test_generador -v

# Show test discovery
python3 -m unittest discover tests/ -v
```

### Running with Debug

```python
# Edit test_generador.py and add debug output
def test_something(self):
    print(f"DEBUG: Testing with value {value}")
    result = something()
    print(f"DEBUG: Got result {result}")
    self.assertEqual(result, expected)
```

### Inspecting Temporary Files

```python
# Modify tearDown() to keep temp files
def tearDown(self):
    # Comment out cleanup for debugging
    # if os.path.exists(self.test_dir):
    #     shutil.rmtree(self.test_dir)
    print(f"Test dir: {self.test_dir}")
```

## Advanced Usage

### Running Tests in Parallel

```bash
# Using pytest (if installed)
pip install pytest pytest-xdist
pytest tests/ -n auto -v
```

### Coverage Analysis

```bash
# Install coverage tool
pip install coverage

# Run tests with coverage
coverage run -m unittest discover tests/
coverage report
coverage html
```

### Continuous Testing

```bash
# Watch for changes and rerun tests
# Install watchdog
pip install watchdog

# Create watch script
while true; do
    python3 -m unittest discover tests/ -v
    sleep 5
done
```

## Creating Custom Tests

### Template for New Test

```python
def test_my_new_feature(self):
    """Test description."""
    # Create test template
    template = """// Question
#include <stdio.h>
int main() {
    // Your test code
    return 0;
}
// Answer

/*name
Test Name
*/
"""
    # Write template
    with open(os.path.join(self.templates_dir, 'test.c'), 'w') as f:
        f.write(template)
    
    # Run generator
    result = subprocess.run([
        'python3', 'generador.py',
        '-s', self.templates_dir,
        '-o', self.output_xml,
        '-n', '1'
    ], cwd=os.path.dirname(os.path.dirname(__file__)), 
       capture_output=True, text=True)
    
    # Assertions
    self.assertEqual(result.returncode, 0)
    self.assertTrue(os.path.exists(self.output_xml))
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Problem: ModuleNotFoundError: No module named 'generador'
# Solution: Run from project root
cd /home/mrtin/dev/p1/idkfa
python3 -m unittest discover tests/ -v
```

#### GCC Not Found
```bash
# Problem: Tests fail with "gcc: command not found"
# Solution: Install GCC
sudo apt-get install gcc  # Debian/Ubuntu
sudo yum install gcc      # RHEL/CentOS
```

#### Temp Directory Issues
```bash
# Problem: Permission denied on temp directories
# Solution: Clean up manually
rm -rf /tmp/test_generador_*

# Or set custom temp location
export TMPDIR=/path/to/writable/temp
```

#### Generated Directory Conflicts
```bash
# Problem: 'generated' directory already exists
# Solution: Remove it
rm -rf generated/

# Or use generate-only mode with specific test
python3 generador.py -t tests/examples/01_minimal.c -g
```

### Debug Mode

```bash
# Run with Python debug output
python3 -u -m unittest discover tests/ -v

# Add print statements to tests
# See temporary file locations
# Examine generated XML
```

## Performance

### Benchmarking

```bash
# Time test execution
time python3 -m unittest discover tests/ -v

# Individual test timing
time python3 -m unittest tests.test_generador.TestGeneradorBasicFeatures -v
```

### Optimization Tips

1. Run specific test classes instead of all tests during development
2. Use `-k` pattern matching if using pytest
3. Skip slow tests temporarily by adding `@unittest.skip()`
4. Use test parallelization for large test suites

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install GCC
        run: sudo apt-get install -y gcc
      - name: Run tests
        run: python3 -m unittest discover tests/ -v
```

## Best Practices

1. **Always run from project root**: `cd /home/mrtin/dev/p1/idkfa`
2. **Use verbose mode during development**: `-v` flag
3. **Test incrementally**: Run specific tests while developing
4. **Keep tests independent**: Each test should work in isolation
5. **Clean up resources**: Tests clean temp files automatically
6. **Document new tests**: Add to TEST_MATRIX.md
7. **Use examples as reference**: Check `examples/` directory

## Quick Reference

```bash
# Most common commands
python3 -m unittest discover tests/ -v              # Run all tests
python3 -m unittest tests.test_generador.CLASS -v   # Run test class
./tests/run_tests.sh                                # Use shell script
python3 generador.py -t tests/examples/XX.c -n 5    # Test example
```

## Getting Help

1. Read documentation: README.md, SUMMARY.md, TEST_MATRIX.md
2. Check examples: `tests/examples/`
3. Review test code: `tests/test_generador.py`
4. Inspect temp files during test execution
5. Add debug print statements to tests

## Next Steps

- Modify existing tests to understand behavior
- Create custom tests for new features
- Use examples as templates for production code
- Integrate tests into your development workflow
- Add coverage analysis for comprehensive testing
