# Quick Start Guide

Get started with the test suite in 60 seconds.

## Run All Tests

```bash
cd /home/mrtin/dev/p1/idkfa
python3 -m unittest discover tests/ -v
```

Expected output:
```
Ran 25 tests in ~3.2s
OK
```

## Test a Single Example

```bash
# Generate questions from an example template
python3 generador.py -t tests/examples/02_with_variables.c -n 5 -o /tmp/test.xml

# View the generated XML
cat /tmp/test.xml | head -50
```

## Run Specific Test Category

```bash
# Test basic features only
python3 -m unittest tests.test_generador.TestGeneradorBasicFeatures -v

# Test optional features
python3 -m unittest tests.test_generador.TestGeneradorOptionalFeatures -v

# Test CLI options
python3 -m unittest tests.test_generador.TestGeneradorCommandLineOptions -v
```

## Run Single Test

```bash
# Test the minimal template
python3 -m unittest tests.test_generador.TestGeneradorBasicFeatures.test_minimal_template -v
```

## Explore Examples

```bash
# List all example templates
ls tests/examples/*.c

# Generate code from an example (no XML)
python3 generador.py -t tests/examples/05_with_stdin.c -n 3 -g

# View generated code
cat generated/05_with_stdin/05_with_stdin_v1.c
```

## Documentation Files

Read in this order:

1. **QUICKSTART.md** (this file) - Start here
2. **SUMMARY.md** - Overview and statistics  
3. **README.md** - Detailed documentation
4. **USAGE_GUIDE.md** - Comprehensive usage
5. **TEST_MATRIX.md** - Coverage details
6. **TEST_LIST.md** - All test descriptions
7. **INDEX.md** - Navigation reference

## Common Commands

```bash
# Run all tests
python3 -m unittest discover tests/ -v

# Run all tests (quiet)
python3 -m unittest discover tests/

# Use shell script
./tests/run_tests.sh

# Test single template
python3 generador.py -t tests/examples/01_minimal.c -n 5

# Test all examples
python3 generador.py -s tests/examples -n 3 -o /tmp/examples.xml

# Generate C code only
python3 generador.py -t tests/examples/04_with_distractors.c -g
```

## What Gets Tested

✅ **Basic Features** (required)
- Minimal templates with name only
- Dynamic variables with substitution

✅ **Optional Features** (individual)
- Fixed incorrect options (opciones)
- Dynamic distractors
- Fixed correct answers (correcta)
- Standard input (STDIN)

✅ **Combined Features** (6 combinations)
- All logical feature combinations

✅ **CLI Options** (all 5)
- Output file, variants, category, template, generate-only

✅ **Error Handling**
- Missing sections, compilation errors

✅ **Direct Functions**
- Parsing and generation functions

## Need Help?

- Issues with imports? Run from project root: `cd /home/mrtin/dev/p1/idkfa`
- GCC not found? Install: `sudo apt-get install gcc`
- Want details? Read `tests/README.md`
- Want examples? Check `tests/examples/`

## Next Steps

1. Run the tests: `python3 -m unittest discover tests/ -v`
2. Explore examples: `ls tests/examples/`
3. Read documentation: `tests/SUMMARY.md`
4. Create your own templates using examples as reference
