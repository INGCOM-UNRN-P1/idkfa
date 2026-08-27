import os
import tempfile
import json
import unittest
from idkfa.config import AppConfig, DEFAULT_SUBSTITUTIONS, CONFIG

class TestAppConfig(unittest.TestCase):
    def test_default_values(self):
        cfg = AppConfig()
        self.assertEqual(cfg.source_directory, "templates")
        self.assertEqual(cfg.output_file, "cuestionario_moodle.xml")
        self.assertEqual(cfg.questions_per_template, 5)
        self.assertEqual(cfg.moodle_base_category, "programacion1_gen_codigo")
        self.assertEqual(cfg.compiler, "gcc")
        self.assertEqual(cfg.compiler_flags, ["-Wall", "-Wextra"])
        self.assertEqual(cfg.execution_timeout, 3)
        self.assertEqual(cfg.min_distractors, 3)
        self.assertEqual(cfg.default_grade, "1.0000000")
        self.assertEqual(cfg.default_penalty, "0.3333333")
        self.assertEqual(cfg.compilation_error_log, "compile_errors.log")
        self.assertEqual(cfg.parsing_error_log, "parsing_errors.log")
        self.assertEqual(cfg.substitutions, DEFAULT_SUBSTITUTIONS)

    def test_to_dict(self):
        cfg = AppConfig(compiler="clang", min_distractors=5)
        d = cfg.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["compiler"], "clang")
        self.assertEqual(d["min_distractors"], 5)
        self.assertIn("substitutions", d)

    def test_load_from_file_non_existent(self):
        cfg = AppConfig.load_from_file("path_does_not_exist_12345.json")
        self.assertIsInstance(cfg, AppConfig)
        self.assertEqual(cfg.compiler, "gcc")

    def test_load_from_file_valid(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json.dumps({
                "compiler": "clang",
                "min_distractors": 7,
                "unknown_key_ignored": 123
            }))
            temp_path = f.name

        try:
            cfg = AppConfig.load_from_file(temp_path)
            self.assertEqual(cfg.compiler, "clang")
            self.assertEqual(cfg.min_distractors, 7)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
