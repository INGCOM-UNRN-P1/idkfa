# Example Templates

This directory contains example C templates demonstrating all features of `generador.py`.

## Files

1. **01_minimal.c** - Minimal template with only required features
   - Shows the absolute minimum needed: question comments and `/*name*/`

2. **02_with_variables.c** - Template with dynamic variables
   - Demonstrates `/*var*/` section with range expressions
   - Variables are substituted in code using `__variable_name__` format

3. **03_with_opciones.c** - Template with fixed incorrect options
   - Shows `/*opciones*/` section for static distractors
   - Good for questions with known wrong answers

4. **04_with_distractors.c** - Template with dynamic distractors
   - Demonstrates `/*distractors*/` section with Python expressions
   - Creates context-aware incorrect answers based on variables

5. **05_with_stdin.c** - Template with standard input
   - Shows `/*STDIN*/` section for programs using scanf/fgets
   - Input lines can use `__variable__` substitution

6. **06_with_correcta.c** - Template with fixed correct answer
   - Demonstrates `/*correcta*/` for conceptual questions
   - Skips compilation and execution

7. **07_all_features.c** - Template combining all dynamic features
   - Shows var + STDIN + opciones + distractors together
   - Demonstrates real-world complex template

## Testing Examples

You can test any example individually:

```bash
# Test single template
python3 generador.py -t tests/examples/01_minimal.c -n 5 -o test_output.xml

# Generate C code only for verification
python3 generador.py -t tests/examples/02_with_variables.c -n 3 -g

# Test all examples at once
python3 generador.py -s tests/examples -n 3 -o examples_output.xml
```

## Feature Reference

| File | name | var | opciones | distractors | correcta | STDIN |
|------|------|-----|----------|-------------|----------|-------|
| 01   | ✅   | ❌  | ❌       | ❌          | ❌       | ❌    |
| 02   | ✅   | ✅  | ❌       | ❌          | ❌       | ❌    |
| 03   | ✅   | ❌  | ✅       | ❌          | ❌       | ❌    |
| 04   | ✅   | ✅  | ❌       | ✅          | ❌       | ❌    |
| 05   | ✅   | ✅  | ❌       | ✅          | ❌       | ✅    |
| 06   | ✅   | ❌  | ✅       | ❌          | ✅       | ❌    |
| 07   | ✅   | ✅  | ✅       | ✅          | ❌       | ✅    |

## Notes

- These examples are simplified for clarity
- Real-world templates may have more complex logic
- All examples follow the documented template format
- Each example is a valid, working template that can generate questions
