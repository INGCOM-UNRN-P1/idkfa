# Test Coverage Matrix

This document shows all tested combinations of features for `generador.py`.

## Feature Legend

- ✅ = Feature included and tested
- ❌ = Feature not included
- `name` = Question name (required)
- `var` = Dynamic variables
- `opciones` = Fixed incorrect options
- `distractors` = Dynamic incorrect options
- `correcta` = Fixed correct answer
- `STDIN` = Standard input

## Basic Features Tests

| Test Name | name | var | opciones | distractors | correcta | STDIN | Description |
|-----------|------|-----|----------|-------------|----------|-------|-------------|
| test_minimal_template | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | Absolute minimum template |
| test_template_with_variables | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Template with dynamic vars |

## Optional Features Tests (Individual)

| Test Name | name | var | opciones | distractors | correcta | STDIN | Description |
|-----------|------|-----|----------|-------------|----------|-------|-------------|
| test_template_with_opciones | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Fixed options only |
| test_template_with_distractors | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | Dynamic distractors |
| test_template_with_correcta | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | Fixed answer (no compile) |
| test_template_with_stdin | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | STDIN input |

## Combined Features Tests

| Test Name | name | var | opciones | distractors | correcta | STDIN | Description |
|-----------|------|-----|----------|-------------|----------|-------|-------------|
| test_var_plus_opciones | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Variables + Fixed options |
| test_var_plus_distractors | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | Variables + Distractors |
| test_var_plus_stdin | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | Variables + STDIN |
| test_opciones_plus_distractors | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | Fixed + Dynamic options |
| test_all_features_except_correcta | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | All dynamic features |
| test_correcta_plus_opciones | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | Fixed answer + options |

## Command-Line Options Tests

| Test Name | Option(s) Tested | Description |
|-----------|-----------------|-------------|
| test_custom_output_file | `-o/--output` | Custom XML output filename |
| test_custom_num_variants | `-n/--num` | Number of question variants |
| test_custom_category | `-c/--category` | Custom Moodle category |
| test_single_template_mode | `-t/--template` | Process single template file |
| test_generate_only_mode | `-g/--generate-only` | Generate C code only |

## Category & Structure Tests

| Test Name | Feature Tested |
|-----------|---------------|
| test_category_hierarchy | Directory-based category structure |

## Error Handling Tests

| Test Name | Error Type Tested |
|-----------|------------------|
| test_missing_intro_comment | Missing `//` intro comment |
| test_missing_name_section | Missing `/*name*/` section |
| test_compilation_error | C code compilation error |

## Parsing Function Tests

| Test Name | Function Tested |
|-----------|----------------|
| test_parse_minimal_template | `parse_c_template()` with minimal input |
| test_parse_template_with_vars | Variable definition parsing |
| test_parse_stdin_section | STDIN section parsing |
| test_generate_vars | Variable value generation |

## Total Coverage

- **Total Tests**: 25
- **Feature Combinations**: 12
- **Command-Line Options**: 5
- **Error Cases**: 3
- **Direct Function Tests**: 4
- **Structure Tests**: 1

## Feature Compatibility Matrix

This matrix shows which features can be combined:

|            | var | opciones | distractors | correcta | STDIN |
|------------|-----|----------|-------------|----------|-------|
| **var**    | —   | ✅       | ✅          | ❌*      | ✅    |
| **opciones** | ✅ | —        | ✅          | ✅       | ✅    |
| **distractors** | ✅ | ✅    | —           | ❌*      | ✅    |
| **correcta** | ❌* | ✅      | ❌*         | —        | N/A** |
| **STDIN**  | ✅  | ✅       | ✅          | N/A**    | —     |

**Notes:**
- `*` When `correcta` is used, compilation is skipped, so `var` in code is not evaluated (though `var` can still be used in `opciones`/`distractors` expressions)
- `**` STDIN requires executable code, so it's incompatible with `correcta` which skips execution

## Test Execution Time

Average test execution time: ~3 seconds for all 25 tests

## Coverage Statistics

- ✅ All basic features tested
- ✅ All optional features tested individually
- ✅ All logical feature combinations tested
- ✅ All command-line options tested
- ✅ Error handling tested
- ✅ Direct function unit tests included
