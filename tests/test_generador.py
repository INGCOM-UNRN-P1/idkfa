#!/usr/bin/env python3
"""
Test suite for generador.py
Tests all feature combinations: basic and optional metadata blocks.
"""

import unittest
import os
import sys
import subprocess
import tempfile
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

# Add parent directory to path to import generador
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import generador


class TestGeneradorBasicFeatures(unittest.TestCase):
    """Test basic features that all templates must have."""
    
    def setUp(self):
        """Create temporary directory for test templates."""
        self.test_dir = tempfile.mkdtemp(prefix='test_generador_')
        self.templates_dir = os.path.join(self.test_dir, 'templates')
        os.makedirs(self.templates_dir)
        self.output_xml = os.path.join(self.test_dir, 'test_output.xml')
    
    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_minimal_template(self):
        """Test template with only required features: name and code."""
        template = """// What is the output?
#include <stdio.h>
int main() {
    printf("42");
    return 0;
}
// Answer:

/*name
Minimal Test Question
*/
"""
        template_path = os.path.join(self.templates_dir, 'minimal.c')
        with open(template_path, 'w') as f:
            f.write(template)
        
        # Run generator
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', self.output_xml,
            '-n', '1'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0, f"Generator failed: {result.stderr}")
        self.assertTrue(os.path.exists(self.output_xml), "Output XML not created")
        
        # Parse and validate XML
        tree = ET.parse(self.output_xml)
        root = tree.getroot()
        questions = root.findall('.//question[@type="multichoice"]')
        self.assertGreater(len(questions), 0, "No questions generated")
    
    def test_template_with_variables(self):
        """Test template with dynamic variables."""
        template = """// What is the result?
#define __val_a__ 5
#define __val_b__ 3

#include <stdio.h>
int main() {
    printf("%d", __val_a__ + __val_b__);
    return 0;
}
// Answer:

/*name
Variable Test Question
*/

/*var
val_a: range(1, 10)
val_b: range(1, 10)
*/
"""
        template_path = os.path.join(self.templates_dir, 'variables.c')
        with open(template_path, 'w') as f:
            f.write(template)
        
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', self.output_xml,
            '-n', '3'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0, f"Generator failed: {result.stderr}")
        tree = ET.parse(self.output_xml)
        questions = tree.findall('.//question[@type="multichoice"]')
        self.assertEqual(len(questions), 3, "Should generate 3 variants")


class TestGeneradorOptionalFeatures(unittest.TestCase):
    """Test optional features: opciones, distractors, correcta, STDIN."""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix='test_generador_')
        self.templates_dir = os.path.join(self.test_dir, 'templates')
        os.makedirs(self.templates_dir)
        self.output_xml = os.path.join(self.test_dir, 'test_output.xml')
    
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_template_with_opciones(self):
        """Test template with fixed incorrect options."""
        template = """// What is the output?
#include <stdio.h>
int main() {
    printf("Hello");
    return 0;
}
// Answer:

/*name
Fixed Options Test
*/

/*opciones
Goodbye
Error
Nothing
*/
"""
        template_path = os.path.join(self.templates_dir, 'opciones.c')
        with open(template_path, 'w') as f:
            f.write(template)
        
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', self.output_xml,
            '-n', '1'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        tree = ET.parse(self.output_xml)
        # Check that answers include the fixed options
        answers = tree.findall('.//answer')
        self.assertGreater(len(answers), 1, "Should have multiple answer options")
    
    def test_template_with_distractors(self):
        """Test template with dynamic distractors."""
        template = """// What is the result?
#define __val__ 5

#include <stdio.h>
int main() {
    printf("%d", __val__ * 2);
    return 0;
}
// Answer:

/*name
Distractors Test
*/

/*var
val: range(2, 10)
*/

/*distractors
__val__
__val__ + 2
__val__ * 3
*/
"""
        template_path = os.path.join(self.templates_dir, 'distractors.c')
        with open(template_path, 'w') as f:
            f.write(template)
        
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', self.output_xml,
            '-n', '2'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(self.output_xml))
    
    def test_template_with_correcta(self):
        """Test template with fixed correct answer (no compilation)."""
        template = """// What does fgets do?
#include <stdio.h>
int main() {
    char buf[10];
    fgets(buf, sizeof(buf), stdin);
    printf("OK");
    return 0;
}
// Answer:

/*name
Fixed Answer Test
*/

/*correcta
OK
*/

/*opciones
Error
Undefined
Crash
*/
"""
        template_path = os.path.join(self.templates_dir, 'correcta.c')
        with open(template_path, 'w') as f:
            f.write(template)
        
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', self.output_xml,
            '-n', '1'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        tree = ET.parse(self.output_xml)
        # Find the correct answer
        correct_answers = tree.findall('.//answer[@fraction="100"]')
        self.assertEqual(len(correct_answers), 1, "Should have one correct answer")
    
    def test_template_with_stdin(self):
        """Test template with STDIN input."""
        template = """// What does the program output?
#define __num_a__ 5
#define __num_b__ 3

#include <stdio.h>
int main() {
    int a, b;
    scanf("%d", &a);
    scanf("%d", &b);
    printf("%d", a + b);
    return 0;
}
// Answer:

/*name
STDIN Test
*/

/*var
num_a: range(1, 10)
num_b: range(1, 10)
*/

/*STDIN
__num_a__
__num_b__
*/

/*distractors
__num_a__ * __num_b__
__num_a__
__num_b__
*/
"""
        template_path = os.path.join(self.templates_dir, 'stdin.c')
        with open(template_path, 'w') as f:
            f.write(template)
        
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', self.output_xml,
            '-n', '2'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(self.output_xml))


class TestGeneradorCombinedFeatures(unittest.TestCase):
    """Test combinations of optional features."""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix='test_generador_')
        self.templates_dir = os.path.join(self.test_dir, 'templates')
        os.makedirs(self.templates_dir)
        self.output_xml = os.path.join(self.test_dir, 'test_output.xml')
    
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_var_plus_opciones(self):
        """Test variables + fixed options."""
        template = """// Result?
#define __x__ 5

#include <stdio.h>
int main() {
    printf("%d", __x__ * 2);
    return 0;
}
// Answer:

/*name
Var + Opciones
*/

/*var
x: range(1, 5)
*/

/*opciones
Error
Undefined
*/
"""
        self._test_template('var_opciones.c', template, 2)
    
    def test_var_plus_distractors(self):
        """Test variables + dynamic distractors."""
        template = """// Result?
#define __x__ 5

#include <stdio.h>
int main() {
    printf("%d", __x__ + __x__);
    return 0;
}
// Answer:

/*name
Var + Distractors
*/

/*var
x: range(1, 5)
*/

/*distractors
__x__
__x__ * 2
__x__ + 1
*/
"""
        self._test_template('var_distractors.c', template, 2)
    
    def test_var_plus_stdin(self):
        """Test variables + STDIN."""
        template = """// Output?
#define __n__ 5

#include <stdio.h>
int main() {
    int x;
    scanf("%d", &x);
    printf("%d", x * 2);
    return 0;
}
// Answer:

/*name
Var + STDIN
*/

/*var
n: range(1, 10)
*/

/*STDIN
__n__
*/
"""
        self._test_template('var_stdin.c', template, 2)
    
    def test_opciones_plus_distractors(self):
        """Test fixed options + dynamic distractors."""
        template = """// Result?
#define __x__ 5

#include <stdio.h>
int main() {
    printf("%d", __x__);
    return 0;
}
// Answer:

/*name
Opciones + Distractors
*/

/*var
x: range(1, 5)
*/

/*opciones
Error
Undefined
*/

/*distractors
__x__ + 1
__x__ * 2
*/
"""
        self._test_template('opciones_distractors.c', template, 2)
    
    def test_all_features_except_correcta(self):
        """Test var + opciones + distractors + STDIN."""
        template = """// Output?
#define __a__ 3
#define __b__ 4

#include <stdio.h>
int main() {
    int x, y;
    scanf("%d %d", &x, &y);
    printf("%d", x + y);
    return 0;
}
// Answer:

/*name
All Features
*/

/*var
a: range(1, 5)
b: range(1, 5)
*/

/*STDIN
__a__ __b__
*/

/*opciones
Error
Undefined
*/

/*distractors
__a__ * __b__
__a__
__b__
*/
"""
        self._test_template('all_features.c', template, 2)
    
    def test_correcta_plus_opciones(self):
        """Test fixed answer + fixed options (no compilation)."""
        template = """// What happens?
#include <stdio.h>
int main() {
    printf("Test");
    return 0;
}
// Answer:

/*name
Correcta + Opciones
*/

/*correcta
Test
*/

/*opciones
Error
Nothing
Crash
*/
"""
        self._test_template('correcta_opciones.c', template, 1)
    
    def _test_template(self, filename, template, num_variants):
        """Helper to test a template."""
        template_path = os.path.join(self.templates_dir, filename)
        with open(template_path, 'w') as f:
            f.write(template)
        
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', self.output_xml,
            '-n', str(num_variants)
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0, f"Failed for {filename}: {result.stderr}")
        self.assertTrue(os.path.exists(self.output_xml))


class TestGeneradorCommandLineOptions(unittest.TestCase):
    """Test command-line arguments."""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix='test_generador_')
        self.templates_dir = os.path.join(self.test_dir, 'templates')
        os.makedirs(self.templates_dir)
        
        # Create a simple test template
        self.template = """// Test
#include <stdio.h>
int main() {
    printf("42");
    return 0;
}
// Answer

/*name
CLI Test
*/
"""
        with open(os.path.join(self.templates_dir, 'test.c'), 'w') as f:
            f.write(self.template)
    
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_custom_output_file(self):
        """Test -o/--output option."""
        custom_output = os.path.join(self.test_dir, 'custom.xml')
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', custom_output,
            '-n', '1'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(custom_output))
    
    def test_custom_num_variants(self):
        """Test -n/--num option."""
        # Create a template with variables to generate unique variants
        template = """// Result?
#define __x__ 5

#include <stdio.h>
int main() {
    printf("%d", __x__);
    return 0;
}
// Answer:

/*name
Num Variants Test
*/

/*var
x: range(1, 20)
*/
"""
        with open(os.path.join(self.templates_dir, 'test.c'), 'w') as f:
            f.write(template)
        
        output = os.path.join(self.test_dir, 'output.xml')
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', output,
            '-n', '7'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        tree = ET.parse(output)
        questions = tree.findall('.//question[@type="multichoice"]')
        self.assertEqual(len(questions), 7)
    
    def test_custom_category(self):
        """Test -c/--category option."""
        output = os.path.join(self.test_dir, 'output.xml')
        custom_category = 'test_category_name'
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', output,
            '-n', '1',
            '-c', custom_category
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        tree = ET.parse(output)
        # Check if category appears in XML
        category_text = ET.tostring(tree.getroot(), encoding='unicode')
        self.assertIn(custom_category, category_text)
    
    def test_single_template_mode(self):
        """Test -t/--template option for single file."""
        output = os.path.join(self.test_dir, 'output.xml')
        template_file = os.path.join(self.templates_dir, 'test.c')
        
        result = subprocess.run([
            'python3', 'generador.py',
            '-t', template_file,
            '-o', output,
            '-n', '2'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(output))
    
    def test_generate_only_mode(self):
        """Test -g/--generate-only option."""
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-n', '2',
            '-g'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        # Check that generated directory exists
        generated_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated')
        self.assertTrue(os.path.exists(generated_dir))
        # Clean up
        if os.path.exists(generated_dir):
            shutil.rmtree(generated_dir)


class TestGeneradorCategoryStructure(unittest.TestCase):
    """Test category hierarchy based on directory structure."""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix='test_generador_')
        self.templates_dir = os.path.join(self.test_dir, 'templates')
        self.output_xml = os.path.join(self.test_dir, 'output.xml')
        
        # Create nested directory structure
        os.makedirs(os.path.join(self.templates_dir, 'category1'))
        os.makedirs(os.path.join(self.templates_dir, 'category2', 'subcategory'))
        
        template = """// Test
#include <stdio.h>
int main() {
    printf("test");
    return 0;
}
// Answer

/*name
Category Test
*/
"""
        # Create templates in different categories
        with open(os.path.join(self.templates_dir, 'category1', 'test1.c'), 'w') as f:
            f.write(template)
        with open(os.path.join(self.templates_dir, 'category2', 'subcategory', 'test2.c'), 'w') as f:
            f.write(template)
    
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_category_hierarchy(self):
        """Test that categories are created based on directory structure."""
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', self.output_xml,
            '-n', '1'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        tree = ET.parse(self.output_xml)
        # Check for category elements
        categories = tree.findall('.//question[@type="category"]')
        self.assertGreater(len(categories), 0, "Should have category questions")


class TestGeneradorErrorHandling(unittest.TestCase):
    """Test error handling for malformed templates."""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix='test_generador_')
        self.templates_dir = os.path.join(self.test_dir, 'templates')
        os.makedirs(self.templates_dir)
        self.output_xml = os.path.join(self.test_dir, 'output.xml')
    
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_missing_intro_comment(self):
        """Test template without intro comment."""
        template = """#include <stdio.h>
int main() {
    printf("test");
    return 0;
}
// Answer

/*name
No Intro Test
*/
"""
        with open(os.path.join(self.templates_dir, 'bad.c'), 'w') as f:
            f.write(template)
        
        # Should still run but skip this template
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', self.output_xml,
            '-n', '1'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        # Check that parsing error is logged
        self.assertIn('No se pudo procesar', result.stdout + result.stderr)
    
    def test_missing_name_section(self):
        """Test template without name section."""
        template = """// Test
#include <stdio.h>
int main() {
    printf("test");
    return 0;
}
// Answer
"""
        with open(os.path.join(self.templates_dir, 'no_name.c'), 'w') as f:
            f.write(template)
        
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', self.output_xml,
            '-n', '1'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        # Should use default name
        self.assertEqual(result.returncode, 0)
    
    def test_compilation_error(self):
        """Test template with C compilation error."""
        template = """// Test
#include <stdio.h>
int main() {
    printf("test"  // Missing semicolon and closing paren
    return 0;
}
// Answer

/*name
Compilation Error Test
*/
"""
        with open(os.path.join(self.templates_dir, 'compile_error.c'), 'w') as f:
            f.write(template)
        
        result = subprocess.run([
            'python3', 'generador.py',
            '-s', self.templates_dir,
            '-o', self.output_xml,
            '-n', '1'
        ], cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True, text=True)
        
        # Check that compile error is handled (generates error answer or logs error)
        output_text = result.stdout + result.stderr
        self.assertTrue(
            'error de compilación' in output_text.lower() or 
            os.path.exists(self.output_xml),
            "Should handle compilation error gracefully"
        )


class TestGeneradorParsingFunctions(unittest.TestCase):
    """Test parsing functions directly."""
    
    def test_parse_minimal_template(self):
        """Test parse_c_template with minimal template."""
        content = """// Question
#include <stdio.h>
int main() { printf("42"); return 0; }
// Answer

/*name
Test
*/
"""
        result = generador.parse_c_template(content)
        self.assertNotEqual(result.get('status'), 'error')
        self.assertIn('code_template', result)
        self.assertIn('question_text_template', result)
    
    def test_parse_template_with_vars(self):
        """Test parsing variable definitions."""
        content = """// Question
#define __x__ 5
int main() { printf("%d", __x__); return 0; }
// Answer

/*name
Test
*/

/*var
x: range(1, 10)
y: [1, 2, 3]
*/
"""
        result = generador.parse_c_template(content)
        self.assertIn('var_defs', result)
        self.assertIn('x', result['var_defs'])
        self.assertIn('y', result['var_defs'])
    
    def test_parse_stdin_section(self):
        """Test parsing STDIN section."""
        content = """// Question
int main() { return 0; }
// Answer

/*name
Test
*/

/*STDIN
line1
line2
*/
"""
        result = generador.parse_c_template(content)
        self.assertIn('stdin_template', result)
        self.assertIsNotNone(result['stdin_template'])
    
    def test_generate_vars(self):
        """Test variable generation."""
        var_defs = {
            'x': 'range(1, 5)',
            'y': '[10, 20, 30]'
        }
        result = generador.generate_vars(var_defs)
        self.assertIn('x', result)
        self.assertIn('y', result)
        self.assertIn(result['x'], [1, 2, 3, 4])
    def test_distractor_normalization_and_deduplication(self):
        """Test normalization and deduplication of distractors."""
        correct = "0"
        predefined = ["0.0", " 1 ", "1", "2"]
        distractors = ["0 + 0", "2 - 1"]
        vars = {}
        results = generador.generate_incorrect_answers(correct, predefined, distractors, vars, count=0)
        norm_results = [generador.normalize_answer_repr(r) for r in results]
        self.assertNotIn("0", norm_results)
        self.assertNotIn("0.0", results)
        # Should not have duplicate '1'
        self.assertEqual(norm_results.count("1"), 1)

    def test_min_distractors_count(self):
        """Test that generate_incorrect_answers meets minimum distractor count."""
        correct = "10"
        results = generador.generate_incorrect_answers(correct, [], [], {}, count=5)
        self.assertGreaterEqual(len(results), 5)
        self.assertNotIn("10", results)

    def test_parse_and_xml_penalty_and_defaultgrade(self):
        """Test parsing and XML creation for custom penalty and defaultgrade."""
        template = """// Question
int main() { printf("5"); return 0; }
// Answer

/*name
Penalty Test
*/

/*penalty 0.25*/
/*defaultgrade 2.5*/
"""
        parsed = generador.parse_c_template(template)
        self.assertEqual(parsed["penalty"], "0.25")
        self.assertEqual(parsed["default_grade"], "2.5")

        root = ET.Element("quiz")
        generador.create_moodle_question_xml(root, parsed, "code", "5", ["1", "2", "3"], 1)
        q_node = root.find("question")
        self.assertEqual(q_node.find("penalty").text, "0.25")
        self.assertEqual(q_node.find("defaultgrade").text, "2.5")

    def test_question_types_xml(self):
        """Test XML generation for shortanswer and numerical question types."""
        # Shortanswer
        template_sa = """// Question
int main() { printf("hello"); return 0; }
// Answer

/*name
Shortanswer Test
*/

/*type shortanswer*/
"""
        parsed_sa = generador.parse_c_template(template_sa)
        self.assertEqual(parsed_sa["question_type"], "shortanswer")

        root_sa = ET.Element("quiz")
        generador.create_moodle_question_xml(root_sa, parsed_sa, "code", "hello", [], 1)
        q_sa = root_sa.find("question")
        self.assertEqual(q_sa.get("type"), "shortanswer")
        self.assertIsNotNone(q_sa.find("usecase"))
        self.assertEqual(q_sa.find("answer/text").text, "<![CDATA[hello]]>")

        # Numerical
        template_num = """// Question
int main() { printf("42"); return 0; }
// Answer

/*name
Numerical Test
*/

/*type numerical*/
"""
        parsed_num = generador.parse_c_template(template_num)
        self.assertEqual(parsed_num["question_type"], "numerical")

        root_num = ET.Element("quiz")
        generador.create_moodle_question_xml(root_num, parsed_num, "code", "42", [], 1)
        q_num = root_num.find("question")
        self.assertEqual(q_num.get("type"), "numerical")
        self.assertIsNotNone(q_num.find("answer/tolerance"))
        self.assertEqual(q_num.find("answer/tolerance").text, "0")

    def test_dynamic_feedback_evaluation(self):
        """Test evaluation and insertion of dynamic feedback."""
        template_fb = """// Question
int main() { printf("10"); return 0; }
// Answer

/*name
Feedback Test
*/

/*var
a: [5]
b: [10]
*/

/*feedback
El valor de a es __a__ y el doble es {a * 2}.
*/
"""
        parsed = generador.parse_c_template(template_fb)
        self.assertIsNotNone(parsed["feedback_template"])
        variables = {"a": 5, "b": 10}
        evaluated = generador.evaluate_feedback(parsed["feedback_template"], variables)
        self.assertIn("El valor de a es 5 y el doble es 10.", evaluated)

        root = ET.Element("quiz")
        generador.create_moodle_question_xml(root, parsed, "code", "10", ["1", "2"], 1, variables=variables)
        q_node = root.find("question")
        self.assertEqual(q_node.find("generalfeedback/text").text, "<![CDATA[El valor de a es 5 y el doble es 10.]]>")

    def test_safe_temp_files_compile_and_run(self):
        """Test compile_and_run_c executes safely and leaves no temporary files in cwd."""
        code = '#include <stdio.h>\nint main() { printf("ok"); return 0; }'
        before_files = set(os.listdir('.'))
        result = generador.compile_and_run_c(code, timeout=3)
        after_files = set(os.listdir('.'))
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output"], "ok")
        # No extra .c or .out files left in cwd
        new_files = [f for f in (after_files - before_files) if f.endswith('.c') or f.endswith('.out')]
        self.assertEqual(new_files, [])

    def test_semantic_validation_early_check(self):
        """Test semantic validation fails when scanf is present without STDIN or fixed answer."""
        template_bad = """// Question
#include <stdio.h>
int main() { int x; scanf("%d", &x); printf("%d", x); return 0; }
// Answer

/*name
Scanf Without Stdin
*/
"""
        parsed = generador.parse_c_template(template_bad)
        self.assertEqual(parsed["status"], "error")
        self.assertIn("Validación semántica", parsed["reason"])

        # Should succeed if STDIN is provided
        template_good = template_bad + "\n/*STDIN\n42\n*/\n"
        parsed_good = generador.parse_c_template(template_good)
        self.assertEqual(parsed_good["status"], "success")

    def test_dependent_variables_generation(self):
        """Test dependent variables generation where var_b depends on var_a."""
        var_defs = {
            "a": "range(5, 6)",       # a is 5
            "b": "range(__a__ + 1, __a__ + 3)" # b in [6, 7]
        }
        res = generador.generate_vars(var_defs)
        self.assertEqual(res["a"], 5)
        self.assertIn(res["b"], [6, 7])

    def test_deterministic_variants_generation(self):
        """Test deterministic Cartesian product generation."""
        var_defs = {
            "x": "[1, 2]",
            "y": "[10, 20]"
        }
        # Cartesian product has 4 elements
        variants = generador.generate_all_variants_deterministically(var_defs, max_count=4)
        self.assertEqual(len(variants), 4)
        unique_keys = set(tuple(sorted(v.items())) for v in variants)
        self.assertEqual(len(unique_keys), 4)

    def test_configurable_compiler_flags_and_math_lib(self):
        """Test custom flags and auto math library detection."""
        template_math = """// Question
#include <stdio.h>
#include <math.h>
int main() { printf("%.0f", sqrt(16.0)); return 0; }
// Answer

/*name
Math Sqrt Test
*/
"""
        parsed = generador.parse_c_template(template_math)
        self.assertIn("-lm", parsed["custom_flags"])
        result = generador.compile_and_run_c(
            parsed["code_template"], 
            timeout=3, 
            extra_flags=parsed["custom_flags"]
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output"], "4")

    def test_centralized_app_config(self):
        """Test centralized AppConfig loading and serialization."""
        from idkfa.config import AppConfig
        cfg = AppConfig(compiler="clang", min_distractors=4)
        self.assertEqual(cfg.compiler, "clang")
        self.assertEqual(cfg.min_distractors, 4)
        d = cfg.to_dict()
        self.assertEqual(d["compiler"], "clang")

        # Test loading from temporary JSON config file
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write('{"compiler": "clang", "min_distractors": 6}')
            temp_cfg_path = f.name

        try:
            loaded_cfg = AppConfig.load_from_file(temp_cfg_path)
            self.assertEqual(loaded_cfg.compiler, "clang")
            self.assertEqual(loaded_cfg.min_distractors, 6)
        finally:
            if os.path.exists(temp_cfg_path):
                os.remove(temp_cfg_path)


if __name__ == '__main__':
    unittest.main()




