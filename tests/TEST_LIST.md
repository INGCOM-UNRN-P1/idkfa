# Complete Test List

All 25 tests in the generador.py test suite with descriptions and commands.

## Basic Features Tests (2)

### TestGeneradorBasicFeatures

#### 1. test_minimal_template
**Description**: Test template with only required features: name and code.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorBasicFeatures.test_minimal_template -v`
**Features Tested**: Minimal template structure, name section

#### 2. test_template_with_variables
**Description**: Test template with dynamic variables.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorBasicFeatures.test_template_with_variables -v`
**Features Tested**: Variable definitions, range expressions, variable substitution

---

## Optional Features Tests (4)

### TestGeneradorOptionalFeatures

#### 3. test_template_with_opciones
**Description**: Test template with fixed incorrect options.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorOptionalFeatures.test_template_with_opciones -v`
**Features Tested**: `/*opciones*/` section, fixed distractors

#### 4. test_template_with_distractors
**Description**: Test template with dynamic distractors.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorOptionalFeatures.test_template_with_distractors -v`
**Features Tested**: `/*distractors*/` section, Python expressions

#### 5. test_template_with_correcta
**Description**: Test template with fixed correct answer (no compilation).
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorOptionalFeatures.test_template_with_correcta -v`
**Features Tested**: `/*correcta*/` section, compilation bypass

#### 6. test_template_with_stdin
**Description**: Test template with STDIN input.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorOptionalFeatures.test_template_with_stdin -v`
**Features Tested**: `/*STDIN*/` section, input handling

---

## Combined Features Tests (6)

### TestGeneradorCombinedFeatures

#### 7. test_var_plus_opciones
**Description**: Test variables + fixed options.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorCombinedFeatures.test_var_plus_opciones -v`
**Features Tested**: var + opciones combination

#### 8. test_var_plus_distractors
**Description**: Test variables + dynamic distractors.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorCombinedFeatures.test_var_plus_distractors -v`
**Features Tested**: var + distractors combination

#### 9. test_var_plus_stdin
**Description**: Test variables + STDIN.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorCombinedFeatures.test_var_plus_stdin -v`
**Features Tested**: var + STDIN combination

#### 10. test_opciones_plus_distractors
**Description**: Test fixed options + dynamic distractors.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorCombinedFeatures.test_opciones_plus_distractors -v`
**Features Tested**: opciones + distractors combination

#### 11. test_all_features_except_correcta
**Description**: Test var + opciones + distractors + STDIN.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorCombinedFeatures.test_all_features_except_correcta -v`
**Features Tested**: All dynamic features combined

#### 12. test_correcta_plus_opciones
**Description**: Test fixed answer + fixed options (no compilation).
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorCombinedFeatures.test_correcta_plus_opciones -v`
**Features Tested**: correcta + opciones combination

---

## Command-Line Options Tests (5)

### TestGeneradorCommandLineOptions

#### 13. test_custom_output_file
**Description**: Test -o/--output option.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorCommandLineOptions.test_custom_output_file -v`
**Features Tested**: Custom XML output filename

#### 14. test_custom_num_variants
**Description**: Test -n/--num option.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorCommandLineOptions.test_custom_num_variants -v`
**Features Tested**: Number of question variants

#### 15. test_custom_category
**Description**: Test -c/--category option.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorCommandLineOptions.test_custom_category -v`
**Features Tested**: Custom Moodle category name

#### 16. test_single_template_mode
**Description**: Test -t/--template option for single file.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorCommandLineOptions.test_single_template_mode -v`
**Features Tested**: Single template processing

#### 17. test_generate_only_mode
**Description**: Test -g/--generate-only option.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorCommandLineOptions.test_generate_only_mode -v`
**Features Tested**: C code generation without XML

---

## Category Structure Tests (1)

### TestGeneradorCategoryStructure

#### 18. test_category_hierarchy
**Description**: Test that categories are created based on directory structure.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorCategoryStructure.test_category_hierarchy -v`
**Features Tested**: Directory-based category creation

---

## Error Handling Tests (3)

### TestGeneradorErrorHandling

#### 19. test_missing_intro_comment
**Description**: Test template without intro comment.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorErrorHandling.test_missing_intro_comment -v`
**Features Tested**: Error handling for missing intro `//` comment

#### 20. test_missing_name_section
**Description**: Test template without name section.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorErrorHandling.test_missing_name_section -v`
**Features Tested**: Default name assignment when `/*name*/` missing

#### 21. test_compilation_error
**Description**: Test template with C compilation error.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorErrorHandling.test_compilation_error -v`
**Features Tested**: Compilation error handling and logging

---

## Parsing Functions Tests (4)

### TestGeneradorParsingFunctions

#### 22. test_parse_minimal_template
**Description**: Test parse_c_template with minimal template.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorParsingFunctions.test_parse_minimal_template -v`
**Features Tested**: parse_c_template() function, minimal input

#### 23. test_parse_template_with_vars
**Description**: Test parsing variable definitions.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorParsingFunctions.test_parse_template_with_vars -v`
**Features Tested**: Variable definition parsing, range and list expressions

#### 24. test_parse_stdin_section
**Description**: Test parsing STDIN section.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorParsingFunctions.test_parse_stdin_section -v`
**Features Tested**: STDIN section parsing

#### 25. test_generate_vars
**Description**: Test variable generation.
**Command**: `python3 -m unittest tests.test_generador.TestGeneradorParsingFunctions.test_generate_vars -v`
**Features Tested**: generate_vars() function, random value generation

---

## Running Multiple Tests

### Run All Tests
```bash
python3 -m unittest discover tests/ -v
```

### Run by Category
```bash
# Basic features
python3 -m unittest tests.test_generador.TestGeneradorBasicFeatures -v

# Optional features
python3 -m unittest tests.test_generador.TestGeneradorOptionalFeatures -v

# Combined features
python3 -m unittest tests.test_generador.TestGeneradorCombinedFeatures -v

# CLI options
python3 -m unittest tests.test_generador.TestGeneradorCommandLineOptions -v

# Error handling
python3 -m unittest tests.test_generador.TestGeneradorErrorHandling -v

# Parsing functions
python3 -m unittest tests.test_generador.TestGeneradorParsingFunctions -v

# Category structure
python3 -m unittest tests.test_generador.TestGeneradorCategoryStructure -v
```

### Run Multiple Specific Tests
```bash
# Run several related tests
python3 -m unittest \
  tests.test_generador.TestGeneradorBasicFeatures.test_minimal_template \
  tests.test_generador.TestGeneradorBasicFeatures.test_template_with_variables \
  -v
```

## Quick Reference

| Test # | Test Name | Primary Feature | Time |
|--------|-----------|----------------|------|
| 1 | test_minimal_template | Minimal template | ~0.1s |
| 2 | test_template_with_variables | Variables | ~0.2s |
| 3 | test_template_with_opciones | Fixed options | ~0.1s |
| 4 | test_template_with_distractors | Distractors | ~0.2s |
| 5 | test_template_with_correcta | Fixed answer | ~0.1s |
| 6 | test_template_with_stdin | STDIN | ~0.2s |
| 7 | test_var_plus_opciones | Combo | ~0.2s |
| 8 | test_var_plus_distractors | Combo | ~0.2s |
| 9 | test_var_plus_stdin | Combo | ~0.2s |
| 10 | test_opciones_plus_distractors | Combo | ~0.2s |
| 11 | test_all_features_except_correcta | Combo | ~0.2s |
| 12 | test_correcta_plus_opciones | Combo | ~0.1s |
| 13 | test_custom_output_file | CLI | ~0.1s |
| 14 | test_custom_num_variants | CLI | ~0.5s |
| 15 | test_custom_category | CLI | ~0.1s |
| 16 | test_single_template_mode | CLI | ~0.1s |
| 17 | test_generate_only_mode | CLI | ~0.1s |
| 18 | test_category_hierarchy | Structure | ~0.1s |
| 19 | test_missing_intro_comment | Error | ~0.1s |
| 20 | test_missing_name_section | Error | ~0.1s |
| 21 | test_compilation_error | Error | ~0.1s |
| 22 | test_parse_minimal_template | Parsing | <0.1s |
| 23 | test_parse_template_with_vars | Parsing | <0.1s |
| 24 | test_parse_stdin_section | Parsing | <0.1s |
| 25 | test_generate_vars | Parsing | <0.1s |

**Total**: ~3.2 seconds for all 25 tests
