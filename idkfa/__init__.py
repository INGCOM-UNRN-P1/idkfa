"""Paquete idkfa para generación de preguntas de código C en Moodle XML."""

from idkfa.config import AppConfig, CONFIG, DEFAULT_SUBSTITUTIONS
from idkfa.parser import TemplateInfo, parse_c_template
from idkfa.compiler import compile_and_run_c
from idkfa.variables import (
    generate_vars,
    generate_all_variants_deterministically,
    normalize_answer_repr,
    generate_incorrect_answers,
    generate_stdin
)
from idkfa.moodle_xml import (
    CDATA,
    evaluate_feedback,
    create_moodle_question_xml,
    create_category_xml
)

__all__ = [
    "AppConfig",
    "CONFIG",
    "DEFAULT_SUBSTITUTIONS",
    "TemplateInfo",
    "parse_c_template",
    "compile_and_run_c",
    "generate_vars",
    "generate_all_variants_deterministically",
    "normalize_answer_repr",
    "generate_incorrect_answers",
    "generate_stdin",
    "CDATA",
    "evaluate_feedback",
    "create_moodle_question_xml",
    "create_category_xml",
]
