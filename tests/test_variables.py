import unittest
import sys
import io
from unittest.mock import patch
from idkfa.parser import DistractorDef
from idkfa.variables import (
    DistractorOption,
    generate_vars,
    generate_all_variants_deterministically,
    normalize_answer_repr,
    adapt_grammar_and_pluralization,
    is_mathematically_trivial,
    generate_incorrect_answers,
    generate_stdin
)

class TestVariables(unittest.TestCase):
    def test_distractor_option(self):
        opt = DistractorOption("42", "Feedback test")
        self.assertEqual(opt.text, "42")
        self.assertEqual(opt.feedback, "Feedback test")
        self.assertEqual(str(opt), "42")

    def test_generate_vars_all_cases(self):
        # 1. Iterable pool
        # 2. Empty iterable pool
        # 3. Scalar pool (non-iterable)
        # 4. Dependent variable
        # 5. Evaluation error
        defs = {
            "a": "range(1, 3)",
            "empty_list": "[]",
            "scalar_num": "42",
            "scalar_str": "'const_str'",
            "dependent": "__scalar_num__ + 8",
            "error_var": "1 / 0"
        }
        res = generate_vars(defs)
        self.assertIn(res["a"], [1, 2])
        self.assertEqual(res["empty_list"], "")
        self.assertEqual(res["scalar_num"], 42)
        self.assertEqual(res["scalar_str"], "const_str")
        self.assertEqual(res["dependent"], 50)
        self.assertEqual(res["error_var"], "")

    def test_generate_all_variants_empty(self):
        self.assertEqual(generate_all_variants_deterministically({}, 5), [{}])

    def test_generate_all_variants_static_and_sample(self):
        # Combinations <= max_count
        defs_small = {"x": "[1, 2]", "y": "[10]"}
        res = generate_all_variants_deterministically(defs_small, max_count=5)
        self.assertEqual(len(res), 2)

        # Combinations > max_count (random.sample)
        defs_large = {"x": "[1, 2, 3, 4]", "y": "[10, 20, 30, 40]"}
        res_sample = generate_all_variants_deterministically(defs_large, max_count=3)
        self.assertEqual(len(res_sample), 3)

    def test_generate_all_variants_dynamic_deps_and_large_domain(self):
        # 1. Dynamic dependency via __var__
        defs_dep = {
            "a": "range(1, 4)",
            "b": "range(__a__, __a__ + 2)"
        }
        res_dep = generate_all_variants_deterministically(defs_dep, max_count=3)
        self.assertEqual(len(res_dep), 3)

        # 2. Dynamic dependency via variable name identifier in string
        defs_dep_name = {
            "a": "range(1, 4)",
            "b": "range(a, a + 2)"
        }
        res_dep_name = generate_all_variants_deterministically(defs_dep_name, max_count=2)
        self.assertEqual(len(res_dep_name), 2)

        # 3. Large domain > 1000 items
        defs_large = {
            "x": "range(1, 2000)"
        }
        res_large = generate_all_variants_deterministically(defs_large, max_count=2)
        self.assertEqual(len(res_large), 2)

        # 4. Scalar domain
        defs_scalar = {
            "x": "100"
        }
        res_scalar = generate_all_variants_deterministically(defs_scalar, max_count=1)
        self.assertEqual(len(res_scalar), 1)
        self.assertEqual(res_scalar[0]["x"], 100)

        # 5. Eval exception during domain inspection
        defs_syntax_err = {
            "x": "syntax error ?!"
        }
        res_err = generate_all_variants_deterministically(defs_syntax_err, max_count=1)
        self.assertEqual(len(res_err), 1)

    def test_normalize_answer_repr(self):
        self.assertEqual(normalize_answer_repr(None), "")
        self.assertEqual(normalize_answer_repr(42.0), "42")
        self.assertEqual(normalize_answer_repr(" 42.0 "), "42")
        self.assertEqual(normalize_answer_repr("3.1400"), "3.14")
        self.assertEqual(normalize_answer_repr("texto"), "texto")

    def test_adapt_grammar_and_pluralization(self):
        tmpl_plural = "[plural: count | 1 elemento | {count} elementos]"
        self.assertEqual(adapt_grammar_and_pluralization(tmpl_plural, {"count": 1}), "1 elemento")
        self.assertEqual(adapt_grammar_and_pluralization(tmpl_plural, {"count": -1}), "1 elemento")
        self.assertEqual(adapt_grammar_and_pluralization(tmpl_plural, {"count": 0}), "{count} elementos")
        self.assertEqual(adapt_grammar_and_pluralization(tmpl_plural, {"count": 5}), "{count} elementos")
        self.assertEqual(adapt_grammar_and_pluralization(tmpl_plural, {"count": "invalido"}), "{count} elementos")

        tmpl_gender = "[gender: g | alumno | alumna]"
        for fem_val in ["f", "fem", "femenino", "mujer", "female", "a", " FEM "]:
            self.assertEqual(adapt_grammar_and_pluralization(tmpl_gender, {"g": fem_val}), "alumna")
        for masc_val in ["m", "masc", "masculino", "varon", "male", "o"]:
            self.assertEqual(adapt_grammar_and_pluralization(tmpl_gender, {"g": masc_val}), "alumno")

    def test_is_mathematically_trivial(self):
        for bad in ["nan", "inf", "-inf", "null", "none", " NAN ", " NULL "]:
            self.assertTrue(is_mathematically_trivial(bad, "10"))
        
        # Negative for positive/zero correct
        self.assertTrue(is_mathematically_trivial("-1", "10"))
        self.assertTrue(is_mathematically_trivial("-5", "0"))
        
        # Huge jump (> 1000x)
        self.assertTrue(is_mathematically_trivial("10001", "10"))
        
        # Non-trivial
        self.assertFalse(is_mathematically_trivial("9", "10"))
        self.assertFalse(is_mathematically_trivial("-10", "-5"))
        
        # Non-numeric exception handling
        self.assertFalse(is_mathematically_trivial("string_opt", "string_ans"))

    def test_generate_incorrect_answers_all_paths(self):
        # 1. Predefined options
        # 2. DistractorDef with dynamic feedback
        # 3. String distractor without feedback
        # 4. Helper functions in eval (chr, ord, bin, hex)
        # 5. Distractor expression error with and without template_name
        # 6. Fallback numeric offsets
        distractors = [
            DistractorDef(expression="__val__ + 1", feedback="Valor fue __val__"),
            "__val__ * 2",
            "chr(ord('A') + __val__)",
            "1 / 0",  # Triggers error without template_name
            DistractorDef(expression="1 / 0", feedback="")  # Triggers error with template_name
        ]
        
        # Without template_name
        res1 = generate_incorrect_answers(
            correct_answer="10",
            predefined_options=["Opcion Predefinida", "10"],
            distractor_expressions=distractors[:4],
            variables={"val": 5},
            count=5,
            template_name=None
        )
        texts1 = [opt.text for opt in res1]
        self.assertIn("Opcion Predefinida", texts1)
        self.assertIn("6", texts1)
        opt_with_fb = [opt for opt in res1 if opt.feedback == "Valor fue 5"]
        self.assertEqual(len(opt_with_fb), 1)
        self.assertEqual(opt_with_fb[0].text, "6")
        self.assertIn("F", texts1) # chr(ord('A') + 5) = 'F'
        self.assertNotIn("10", texts1) # correct answer excluded

        # With template_name (for error logging origin_info branch)
        res2 = generate_incorrect_answers(
            correct_answer="10",
            predefined_options=[],
            distractor_expressions=[DistractorDef("1 / 0", "fb")],
            variables={"val": 5},
            count=3,
            template_name="mi_plantilla.c"
        )
        self.assertGreaterEqual(len(res2), 3)

        # Non-numeric correct answer (catches ValueError in numeric offset loop)
        res3 = generate_incorrect_answers(
            correct_answer="TEXTO_CORRECTO",
            predefined_options=["INCORRECTO_1", "INCORRECTO_2"],
            distractor_expressions=[],
            variables={},
            count=5
        )
        texts3 = [opt.text for opt in res3]
        self.assertIn("INCORRECTO_1", texts3)
        self.assertIn("INCORRECTO_2", texts3)
        self.assertNotIn("TEXTO_CORRECTO", texts3)

    def test_generate_stdin_all_cases(self):
        # 1. None or empty template
        self.assertIsNone(generate_stdin(None, {}))
        self.assertIsNone(generate_stdin("", {}))

        # 2. __var__ and {expr} substitution
        tmpl = "__a__\n{a * 10}\n{b.upper()}"
        res = generate_stdin(tmpl, {"a": 3, "b": "hola"})
        lines = res.split("\n")
        self.assertEqual(lines[0], "3")
        self.assertEqual(lines[1], "30")
        self.assertEqual(lines[2], "HOLA")

        # 3. Invalid python syntax inside {expr} -> returns match.group(0)
        tmpl_syntax_err = "{invalid expr #$}"
        res_syntax = generate_stdin(tmpl_syntax_err, {})
        self.assertEqual(res_syntax, "{invalid expr #$}")

        # 4. Top-level exception -> returns stdin_template (lines 264-266)
        with patch("re.sub", side_effect=TypeError("mock re.sub error")):
            res_top_err = generate_stdin("raw stdin", {"a": 1})
            self.assertEqual(res_top_err, "raw stdin")
