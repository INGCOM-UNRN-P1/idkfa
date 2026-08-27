import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch
from idkfa.moodle_xml import CDATA, evaluate_feedback, create_moodle_question_xml, create_category_xml
from idkfa.variables import DistractorOption
from idkfa.parser import TemplateInfo

class TestMoodleXml(unittest.TestCase):
    def test_cdata_wrapping(self):
        self.assertEqual(CDATA("hello"), "<![CDATA[hello]]>")
        self.assertEqual(CDATA("<![CDATA[already wrapped]]>"), "<![CDATA[already wrapped]]>")

    def test_evaluate_feedback_empty_or_none(self):
        self.assertEqual(evaluate_feedback(None, {}), "")
        self.assertEqual(evaluate_feedback("", {}), "")

    def test_evaluate_feedback_variable_and_expression(self):
        fb = "Valor: __a__, Doble: {a * 2}"
        res = evaluate_feedback(fb, {"a": 10})
        self.assertEqual(res, "Valor: 10, Doble: 20")

    def test_evaluate_feedback_expression_syntax_error(self):
        fb = "Expr fallida: {invalid syntax %$#@}"
        res = evaluate_feedback(fb, {"a": 10})
        self.assertEqual(res, "Expr fallida: {invalid syntax %$#@}")

    def test_evaluate_feedback_top_level_exception(self):
        # Trigger an exception inside evaluate_feedback (e.g. mock adapt_grammar_and_pluralization)
        with patch("idkfa.moodle_xml.adapt_grammar_and_pluralization", side_effect=TypeError("mock error")):
            res = evaluate_feedback("Plantilla con error", {"a": 1})
            self.assertEqual(res, "Plantilla con error")

    def test_create_moodle_question_xml_multichoice(self):
        root = ET.Element("quiz")
        info = {
            "question_type": "multichoice",
            "name": "Pregunta Multichoice",
            "question_text_template": "Enunciado: {code}",
            "default_grade": "2.0",
            "penalty": "0.5",
            "feedback_template": "Feedback __x__"
        }
        incorrect = [
            DistractorOption("42", "Feedback distractor"),
            "-5",
            "Texto no numerico"
        ]
        create_moodle_question_xml(
            parent=root,
            template_info=info,
            code_instance="int x = 10;",
            correct_answer="10",
            incorrect_answers=incorrect,
            question_number=1,
            stdin_content="input_line",
            variables={"x": 10}
        )
        q = root.find("question")
        self.assertIsNotNone(q)
        self.assertEqual(q.get("type"), "multichoice")
        self.assertEqual(q.find("defaultgrade").text, "2.0")
        self.assertEqual(q.find("penalty").text, "0.5")
        
        answers = q.findall("answer")
        self.assertEqual(len(answers), 4)
        
        # Verify correct answer
        correct_ans = q.find("answer[@fraction='100']")
        self.assertEqual(correct_ans.find("text").text, "<![CDATA[`10`]]>")

    def test_create_moodle_question_xml_fallback_grades(self):
        class Args:
            defaultgrade = "1.5"
            penalty = "0.2"

        root = ET.Element("quiz")
        info = TemplateInfo(status="success", question_type="multichoice")
        create_moodle_question_xml(
            parent=root,
            template_info=info,
            code_instance="code",
            correct_answer="ans",
            incorrect_answers=[],
            question_number=1,
            args=Args()
        )
        q = root.find("question")
        self.assertEqual(q.find("defaultgrade").text, "1.5")
        self.assertEqual(q.find("penalty").text, "0.2")

    def test_create_moodle_question_xml_shortanswer(self):
        root = ET.Element("quiz")
        info = TemplateInfo(status="success", question_type="shortanswer")
        create_moodle_question_xml(
            parent=root,
            template_info=info,
            code_instance="code",
            correct_answer=" texto_correcto ",
            incorrect_answers=[],
            question_number=1
        )
        q = root.find("question")
        self.assertEqual(q.get("type"), "shortanswer")
        self.assertEqual(q.find("usecase").text, "0")
        self.assertEqual(q.find("answer/text").text, "<![CDATA[texto_correcto]]>")

    def test_create_moodle_question_xml_numerical(self):
        root = ET.Element("quiz")
        info = TemplateInfo(status="success", question_type="numerical")
        create_moodle_question_xml(
            parent=root,
            template_info=info,
            code_instance="code",
            correct_answer="42",
            incorrect_answers=[],
            question_number=1
        )
        q = root.find("question")
        self.assertEqual(q.get("type"), "numerical")
        self.assertEqual(q.find("answer/tolerance").text, "0")
        self.assertEqual(q.find("answer/text").text, "<![CDATA[42]]>")

    def test_create_category_xml(self):
        root = ET.Element("quiz")
        create_category_xml(root, "$course$/top/categoria_ejemplo")
        cat_q = root.find("question[@type='category']")
        self.assertIsNotNone(cat_q)
        self.assertEqual(cat_q.find("category/text").text, "$course$/top/categoria_ejemplo")
        self.assertEqual(cat_q.find("info").get("format"), "moodle_auto_format")
