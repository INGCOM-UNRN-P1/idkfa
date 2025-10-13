# Test Suite Index

Quick navigation for the generador.py test suite.

## 📚 Documentation Files

| File | Purpose | Contents |
|------|---------|----------|
| **README.md** | Main documentation | Detailed test coverage, running instructions, test structure |
| **SUMMARY.md** | Executive summary | Quick overview, test results, key statistics |
| **TEST_MATRIX.md** | Coverage matrix | Complete feature combination table, compatibility matrix |
| **INDEX.md** | This file | Quick navigation and overview |

## 🧪 Test Files

| File | Description | Tests |
|------|-------------|-------|
| **test_generador.py** | Main test suite | 25 comprehensive tests in 7 test classes |
| **run_tests.sh** | Shell runner | Executable script to run all tests |
| **__init__.py** | Package init | Makes tests/ a Python package |

## 📋 Test Classes

1. **TestGeneradorBasicFeatures** (2 tests)
   - Minimal templates
   - Variable substitution

2. **TestGeneradorOptionalFeatures** (4 tests)
   - Individual optional features
   - `opciones`, `distractors`, `correcta`, `STDIN`

3. **TestGeneradorCombinedFeatures** (6 tests)
   - Feature combinations
   - Complex template scenarios

4. **TestGeneradorCommandLineOptions** (5 tests)
   - CLI argument testing
   - All command-line flags

5. **TestGeneradorCategoryStructure** (1 test)
   - Directory-based categories

6. **TestGeneradorErrorHandling** (3 tests)
   - Error cases
   - Malformed templates

7. **TestGeneradorParsingFunctions** (4 tests)
   - Direct function tests
   - Unit testing of parse functions

## 📁 Example Templates

Located in `examples/` directory:

| File | Features | Purpose |
|------|----------|---------|
| 01_minimal.c | name only | Minimal working template |
| 02_with_variables.c | var | Dynamic variables |
| 03_with_opciones.c | opciones | Fixed options |
| 04_with_distractors.c | var + distractors | Dynamic incorrect answers |
| 05_with_stdin.c | var + STDIN + distractors | Input handling |
| 06_with_correcta.c | correcta + opciones | Fixed answer |
| 07_all_features.c | var + STDIN + opciones + distractors | Everything combined |

## 🚀 Quick Commands

```bash
# Run all tests
python3 -m unittest discover tests/ -v

# Run with script
./tests/run_tests.sh

# Test specific class
python3 -m unittest tests.test_generador.TestGeneradorBasicFeatures -v

# Test single feature
python3 -m unittest tests.test_generador.TestGeneradorOptionalFeatures.test_template_with_stdin -v

# Test an example
python3 generador.py -t tests/examples/05_with_stdin.c -n 3 -o test.xml
```

## 📊 Coverage Summary

- ✅ **Basic Features**: 100%
- ✅ **Optional Features**: 100%
- ✅ **Feature Combinations**: 12 combinations tested
- ✅ **CLI Options**: 5/5 tested
- ✅ **Error Handling**: 3 scenarios covered
- ✅ **Direct Functions**: 4 functions tested

## 🎯 Test Results

```
Ran 25 tests in ~3.2s
Status: OK (All Passing)
```

## 📖 Reading Order

**For first-time users:**
1. Start with `SUMMARY.md` - get the big picture
2. Read `README.md` - understand the details
3. Check `examples/` - see practical examples
4. Review `TEST_MATRIX.md` - understand coverage

**For developers:**
1. `test_generador.py` - read the actual tests
2. `examples/` - reference templates
3. `TEST_MATRIX.md` - feature compatibility

**For maintainers:**
1. `TEST_MATRIX.md` - identify gaps
2. `test_generador.py` - add new tests
3. Update documentation files

## 🔧 Test Development

When adding new tests:
1. Add test method to appropriate class
2. Update TEST_MATRIX.md with coverage info
3. Add example template if needed
4. Run full test suite to verify

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | Run from project root: `cd /home/mrtin/dev/p1/idkfa` |
| GCC not found | Install GCC: `sudo apt-get install gcc` |
| Temp dirs persist | Clean: `rm -rf /tmp/test_generador_*` |
| Generated dir exists | Remove: `rm -rf generated/` |

## 📈 Statistics

- Total test files: 1 (test_generador.py)
- Total test methods: 25
- Example templates: 7
- Documentation files: 4
- Execution time: ~3.2 seconds
- Test coverage: Comprehensive (all features)

## 🔗 Related Files

In project root:
- `generador.py` - The script being tested
- `templates/` - Production templates
- `GEMINI.md` - Project documentation

## 📝 Notes

- All tests use temporary directories (auto-cleanup)
- Tests are independent and order-agnostic
- No external dependencies beyond stdlib
- Examples are self-contained and runnable
