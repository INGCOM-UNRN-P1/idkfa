# Project Overview

This project contains a Python script (`generador.py`) designed to automate the creation of Moodle question banks in XML format. It processes C code templates (`.c` files) located in the `templates/` directory, generates multiple variants of each question, compiles and executes the C code to determine the correct answers, and then outputs a Moodle-compatible XML file. The directory structure within `templates/` is used to define the categorization of questions within Moodle.

# Building and Running

The core of this project is the `generador.py` Python script.

## Execution

To run the script, use the following command:

```bash
python3 generador.py [options]
```

## Command-Line Arguments

*   `-s` or `--source`: Specifies the directory containing the C code templates. Defaults to `templates`.
*   `-o` or `--output`: Specifies the name of the output XML file for Moodle. Defaults to `cuestionario_moodle.xml`.
*   `-n` or `--num`: The number of question variants to generate for each template. Defaults to `5`.
*   `-c` or `--category`: The root category name under which questions will be organized in Moodle. Defaults to `programacion1_gen_codigo`.
*   `-t` or `--template`: Process only a specific `.c` file instead of an entire directory. Useful for testing individual templates.
*   `-g` or `--generate-only`: Generate only C code in the `generated` directory without creating the XML file. Useful for verification.
*   `--penalty`: Default penalty fraction for wrong answers (e.g. `0.25`). Defaults to `0.3333333`.
*   `--defaultgrade`: Default question grade (e.g. `1.0`). Defaults to `1.0000000`.
*   `--min-distractors`: Minimum number of distractors for multichoice questions. Defaults to `3`.
*   `--compiler`: C compiler binary to use (e.g. `gcc`, `clang`). Defaults to `gcc`.
*   `--cflags`: Global C compilation flags (e.g. `"-Wall -Wextra -O2"`). Defaults to `"-Wall -Wextra"`.
*   `-j` or `--jobs`: Number of parallel worker processes for compilation and generation. Defaults to `1`.
*   `--check` or `--dry-run`: Fast syntax and compilation verification mode without writing XML.
*   `--config`: Path to custom JSON configuration file.

## Example

```bash
python3 generador.py -s templates -o my_moodle_questions.xml -n 10 -c my_course_category -j 4
python3 generador.py -t templates/arrays/example.c -n 5  # Process single template
python3 generador.py -s templates --check  # Quick dry-run validation
python3 generador.py -g -n 3  # Generate C code only for verification
```

# Development Conventions

## C Code Templates

*   C code templates are `.c` files located in subdirectories within the `templates/` folder. These subdirectories define the Moodle category hierarchy.
*   Each `.c` file combines valid C code with special metadata blocks embedded in comments.
*   Question statements are defined using single-line comments (`//`) at the beginning and end of the relevant code block.
*   Dynamic variables within the C code are denoted by `__variable_name__`.
*   Statements support grammar adaptation tags: `[plural: var_name | singular | plural]` and `[gender: var_name | masculino | femenino]`.
*   Macros (e.g., `#define __val_a__ 10`) can be included in the C files for independent testing; the script will remove them during processing.

## Metadata Blocks (within C templates)

Metadata is defined within `/* section ... */` comment blocks:

*   `/*name*/`: (Mandatory) Defines the base name of the question in Moodle.
*   `/*type*/`: (Optional) Question type: `multichoice` (default), `shortanswer`, or `numerical`.
*   `/*flags*/`: (Optional) Custom compiler flags for this template (e.g. `-lm -O2`). Note that `<math.h>` automatically appends `-lm`.
*   `/*penalty*/`: (Optional) Custom penalty fraction for incorrect attempts (e.g. `0.25`).
*   `/*defaultgrade*/`: (Optional) Custom default grade for the question (e.g. `2.0`).
*   `/*feedback*/`: (Optional) Dynamic pedagogical feedback displayed after question completion. Supports dynamic variables (`__var__` or `{var * 2}`).
*   `/*var*/`: (Optional) Defines dynamic variables using Python expressions (e.g., `variable_name: range(min, max)`). Supports dependent variables referencing previous variables (`b: range(__a__ + 1, 10)`).
*   `/*opciones*/`: (Optional) Provides a list of fixed incorrect answer options.
*   `/*distractors*/`: (Optional) Defines "smart distractors" using Python expressions. Supports specific distractor feedback using syntax `expr -> feedback` or `expr // feedback`. Lines starting with `//#` are comments. Trivial distractors (negative values for positive counts, NaN) are filtered automatically.
*   `/*correcta*/`: (Optional) If present, its content is used as the correct answer directly, bypassing code compilation and execution. Can be a fixed text value or an evaluable Python expression (if the first line starts with `# `). Useful for conceptual questions or conditional answers.
*   `/*STDIN*/`: (Optional) Defines standard input (stdin) to be provided to the program during execution. Supports static text, dynamic variables using `__variable_name__` format, and f-string-like expressions using `{variable}` syntax. Each line in the block becomes a line of stdin. The stdin content is automatically displayed in the question statement. Useful for programs using `scanf`, `fgets`, etc.

## Error Logging

By default, errors (parsing and C compilation failures) are recorded in a log file matching the output filename with the `.log` extension (e.g. `cuestionario_moodle.log` for `-o cuestionario_moodle.xml`). A custom log path can be specified using the `--log-file` argument.
