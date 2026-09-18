import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock

from idkfa.variables import (
    find_unresolved_placeholders,
    contains_unresolved_placeholders,
    generate_incorrect_answers,
    DistractorOption,
)
from idkfa.moodle_xml import create_moodle_question_xml
from idkfa.gift_exporter import exportar_pregunta_gift
from generador import process_template_data


class TestPlaceholderValidation(unittest.TestCase):

    def test_find_and_contains_unresolved_placeholders(self):
        self.assertFalse(contains_unresolved_placeholders("int a = 10;"))
        self.assertEqual(find_unresolved_placeholders("int a = 10;"), [])

        text_with_ph = "int a = __val_a__; int b = __val_b__;"
        self.assertTrue(contains_unresolved_placeholders(text_with_ph))
        self.assertEqual(find_unresolved_placeholders(text_with_ph), ["__val_a__", "__val_b__"])

        # None handling
        self.assertFalse(contains_unresolved_placeholders(None))
        self.assertEqual(find_unresolved_placeholders(None), [])

    def test_generate_incorrect_answers_replaces_vars_in_predefined_options(self):
        predefined = ["__val__", "42"]
        variables = {"val": 99}
        incorrect = generate_incorrect_answers(
            correct_answer="10",
            distractor_expressions=[],
            predefined_options=predefined,
            variables=variables,
            count=3,
        )
        self.assertIn("99", incorrect)
        self.assertNotIn("__val__", incorrect)

    def test_create_moodle_question_xml_raises_on_placeholders(self):
        root = ET.Element("quiz")
        info = {
            "question_type": "multichoice",
            "name": "Pregunta Placeholder",
            "question_text_template": "Enunciado: {code}",
        }

        # 1. Placeholder in code
        with self.assertRaises(ValueError) as ctx:
            create_moodle_question_xml(
                parent=root,
                template_info=info,
                code_instance="int x = __unresolved__;",
                correct_answer="10",
                incorrect_answers=["1", "2"],
                question_number=1,
            )
        self.assertIn("__unresolved__", str(ctx.exception))

        # 2. Placeholder in correct answer
        with self.assertRaises(ValueError) as ctx:
            create_moodle_question_xml(
                parent=root,
                template_info=info,
                code_instance="int x = 10;",
                correct_answer="__ans__",
                incorrect_answers=["1", "2"],
                question_number=1,
            )
        self.assertIn("__ans__", str(ctx.exception))

        # 3. Placeholder in incorrect answers
        with self.assertRaises(ValueError) as ctx:
            create_moodle_question_xml(
                parent=root,
                template_info=info,
                code_instance="int x = 10;",
                correct_answer="10",
                incorrect_answers=["1", "__distractor_ph__"],
                question_number=1,
            )
        self.assertIn("__distractor_ph__", str(ctx.exception))

        # 4. Placeholder in distractor feedback
        with self.assertRaises(ValueError) as ctx:
            create_moodle_question_xml(
                parent=root,
                template_info=info,
                code_instance="int x = 10;",
                correct_answer="10",
                incorrect_answers=[DistractorOption("1", "Feedback con __fb_ph__")],
                question_number=1,
            )
        self.assertIn("__fb_ph__", str(ctx.exception))

        # 5. Placeholder in general feedback
        info_with_fb = dict(info)
        info_with_fb["feedback_template"] = "General feedback __missing_fb__"
        with self.assertRaises(ValueError) as ctx:
            create_moodle_question_xml(
                parent=root,
                template_info=info_with_fb,
                code_instance="int x = 10;",
                correct_answer="10",
                incorrect_answers=["1", "2"],
                question_number=1,
                variables={"other_var": 5},
            )
        self.assertIn("__missing_fb__", str(ctx.exception))

    def test_exportar_pregunta_gift_raises_on_placeholders(self):
        # Placeholder in code
        with self.assertRaises(ValueError) as ctx:
            exportar_pregunta_gift("T1", "int x = __val__;", "10", ["1", "2"])
        self.assertIn("__val__", str(ctx.exception))

        # Placeholder in correct answer
        with self.assertRaises(ValueError) as ctx:
            exportar_pregunta_gift("T1", "int x = 10;", "__correct__", ["1", "2"])
        self.assertIn("__correct__", str(ctx.exception))

        # Placeholder in distractors
        with self.assertRaises(ValueError) as ctx:
            exportar_pregunta_gift("T1", "int x = 10;", "10", ["1", "__d__"])
        self.assertIn("__d__", str(ctx.exception))

    def test_process_template_data_returns_error_on_placeholder(self):
        mock_info = {
            "name": "Test Template",
            "question_type": "multichoice",
            "question_text_template": "{code}",
            "code_template": "int main() { printf(\"%d\", __missing__); return 0; }",
            "var_defs": {},
            "distractor_expressions": [],
            "predefined_options": ["1", "2", "3"],
            "substitutions": {},
            "feedback_template": None,
            "stdin_template": None,
            "fixed_correct_answer": "10",
        }

        with patch("builtins.open", unittest.mock.mock_open(read_data="dummy")), \
             patch("generador.parse_c_template", return_value=mock_info):
            res = process_template_data("fake_path.c", {"num": 1}, {})
            self.assertEqual(res["status"], "error")
            self.assertIn("Placeholder no resuelto", res["reason"])
            self.assertIn("__missing__", res["reason"])


if __name__ == "__main__":
    unittest.main()
