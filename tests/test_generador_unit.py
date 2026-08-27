import os
import sys
import tempfile
import unittest
import argparse
import io
import runpy
from unittest.mock import patch, MagicMock

import generador
from idkfa.config import AppConfig

class TestGeneradorUnit(unittest.TestCase):
    def test_print_progress_bar(self):
        # 1. Total <= 0 (line 38)
        generador.print_progress_bar(0, 0)
        generador.print_progress_bar(1, -1)

        # 2. Intermediate progress
        capture = io.StringIO()
        with patch("sys.stdout", capture):
            generador.print_progress_bar(1, 2, prefix="Progreso:", suffix="(1/2)")
            generador.print_progress_bar(2, 2, prefix="Progreso:", suffix="(2/2)")
        out = capture.getvalue()
        self.assertIn("Progreso:", out)
        self.assertIn("100.0%", out)

    def test_process_template_data_parse_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_file = os.path.join(tmpdir, "bad.c")
            with open(bad_file, "w", encoding="utf-8") as f:
                f.write("No intro or closing comments\n")

            log_file = os.path.join(tmpdir, "test.log")
            args_dict = {"output": os.path.join(tmpdir, "out.xml"), "log_file": log_file, "num": 1}
            config_dict = {}

            res = generador.process_template_data(bad_file, args_dict, config_dict)
            self.assertEqual(res["status"], "error")
            self.assertTrue(os.path.exists(log_file))
            with open(log_file, "r", encoding="utf-8") as f:
                log_text = f.read()
            self.assertIn("PARSE ERROR", log_text)

    def test_process_template_data_correct_answer_expression(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Valid expression
            tmpl_valid = os.path.join(tmpdir, "valid_expr.c")
            with open(tmpl_valid, "w", encoding="utf-8") as f:
                f.write("// Q\nint main(){}\n// A\n/*name Expr*/\n/*var\nx: [5]\n*/\n/*correcta\n# __x__ * 3\n*/\n")

            args_dict = {"output": "out.xml", "num": 1}
            config_dict = {}
            res_valid = generador.process_template_data(tmpl_valid, args_dict, config_dict)
            self.assertEqual(res_valid["status"], "success")
            self.assertEqual(res_valid["questions"][0]["correct_answer"], "15")

            # 2. Expression that throws exception (lines 89-95)
            tmpl_err = os.path.join(tmpdir, "err_expr.c")
            with open(tmpl_err, "w", encoding="utf-8") as f:
                f.write("// Q\nint main(){}\n// A\n/*name Err*/\n/*var\nx: [0]\n*/\n/*correcta\n# 10 / __x__\n*/\n")

            res_err = generador.process_template_data(tmpl_err, args_dict, config_dict)
            self.assertEqual(res_err["status"], "success")
            self.assertEqual(len(res_err["questions"]), 0)

    def test_process_template_data_compile_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpl_compile_err = os.path.join(tmpdir, "compile_fail.c")
            with open(tmpl_compile_err, "w", encoding="utf-8") as f:
                f.write("// Q\nint main() { syntax_error; }\n// A\n/*name Fail*/\n")

            args_dict = {"output": os.path.join(tmpdir, "out.xml"), "num": 1}
            config_dict = {}
            res = generador.process_template_data(tmpl_compile_err, args_dict, config_dict)
            self.assertEqual(res["status"], "success")
            self.assertEqual(len(res["questions"]), 0)

    def test_generate_c_code_only_invalid_template(self):
        # 1. Template does not exist (lines 161-163)
        args1 = argparse.Namespace(template="non_existent_file.c", source="templates", num=1, cflags=None, compiler=None)
        generador.generate_c_code_only(args1)

        # 2. Template not ending in .c (lines 164-166)
        with tempfile.NamedTemporaryFile("w", suffix=".txt") as f:
            args2 = argparse.Namespace(template=f.name, source="templates", num=1, cflags=None, compiler=None)
            generador.generate_c_code_only(args2)

    def test_generate_c_code_only_template_parse_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_c = os.path.join(tmpdir, "bad.c")
            with open(bad_c, "w", encoding="utf-8") as f:
                f.write("No comment delimiters\n")

            args = argparse.Namespace(template=bad_c, source="templates", num=1, cflags=None, compiler=None)
            generador.generate_c_code_only(args)
            self.assertTrue(os.path.exists("generated"))

    def test_generate_c_code_only_valid_single_template(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            valid_c = os.path.join(tmpdir, "single.c")
            with open(valid_c, "w", encoding="utf-8") as f:
                f.write("// Q\n#define __a__ 1\nint main(){ return 0; }\n// A\n/*name Single*/\n/*var\na: [1, 2]\n*/\n")

            args = argparse.Namespace(template=valid_c, source=tmpdir, num=2, cflags=None, compiler=None)
            generador.generate_c_code_only(args)
            out_c = os.path.join("generated", "single", "single_v1.c")
            self.assertTrue(os.path.exists(out_c))

    def test_generate_c_code_only_source_subdirs_and_limited_variants(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create templates in nested subdirectories
            sub = os.path.join(tmpdir, "nested", "sub")
            os.makedirs(sub)
            t1 = os.path.join(sub, "t1.c")
            with open(t1, "w", encoding="utf-8") as f:
                # var has only 1 option, but num=3 -> triggers warning "Solo se generaron 1/3 variantes" (lines 225-226)
                f.write("// Q\n#define __x__ 1\nint main(){ printf(\"%d\", __x__); return 0; }\n// A\n/*name T1*/\n/*var\nx: [10]\n*/\n")

            t2 = os.path.join(tmpdir, "t2.c")
            with open(t2, "w", encoding="utf-8") as f:
                f.write("// Q\nint main(){ printf(\"t2\"); return 0; }\n// A\n/*name T2*/\n")

            args = argparse.Namespace(
                template=None,
                source=tmpdir,
                num=3,
                cflags="-Wall -O2",
                compiler="gcc"
            )
            generador.generate_c_code_only(args)
            makefile_path = os.path.join("generated", "Makefile")
            self.assertTrue(os.path.exists(makefile_path))
            with open(makefile_path, "r", encoding="utf-8") as mf:
                content = mf.read()
            self.assertIn("CFLAGS = -Wall -O2", content)

    def test_main_cli_branches(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            valid_c = os.path.join(tmpdir, "valid.c")
            with open(valid_c, "w", encoding="utf-8") as f:
                f.write("// Q\nint main(){ printf(\"ok\"); return 0; }\n// A\n/*name Q1*/\n")

            config_json = os.path.join(tmpdir, "custom_config.json")
            with open(config_json, "w", encoding="utf-8") as f:
                f.write('{"compiler": "gcc", "min_distractors": 3}')

            out_xml = os.path.join(tmpdir, "output.xml")

            # 1. --config branch (lines 282-283) with parallel jobs (lines 318-326)
            valid_c2 = os.path.join(tmpdir, "valid2.c")
            with open(valid_c2, "w", encoding="utf-8") as f:
                f.write("// Q\nint main(){ printf(\"ok2\"); return 0; }\n// A\n/*name Q2*/\n")

            test_args_parallel = [
                "generador.py",
                "-s", tmpdir,
                "-o", out_xml,
                "--config", config_json,
                "-j", "2",
                "-n", "1"
            ]
            with patch("sys.argv", test_args_parallel):
                generador.main()
            self.assertTrue(os.path.exists(out_xml))

            # 2. --generate-only branch (line 286)
            test_args_gen = [
                "generador.py",
                "-s", tmpdir,
                "-g",
                "-n", "1"
            ]
            with patch("sys.argv", test_args_gen):
                generador.main()
            self.assertTrue(os.path.exists("generated"))

            # 3. Invalid --template (lines 293-294)
            test_args_invalid_t = [
                "generador.py",
                "-t", os.path.join(tmpdir, "non_existent.c")
            ]
            with patch("sys.argv", test_args_invalid_t):
                with self.assertRaises(SystemExit) as cm:
                    generador.main()
                self.assertEqual(cm.exception.code, 1)

            # 4. Invalid --source directory (lines 298-299)
            test_args_invalid_s = [
                "generador.py",
                "-s", os.path.join(tmpdir, "non_existent_dir_123")
            ]
            with patch("sys.argv", test_args_invalid_s):
                with self.assertRaises(SystemExit) as cm:
                    generador.main()
                self.assertEqual(cm.exception.code, 1)

            # 5. Empty directory (lines 306-307)
            empty_dir = os.path.join(tmpdir, "empty_dir")
            os.makedirs(empty_dir)
            test_args_empty = [
                "generador.py",
                "-s", empty_dir
            ]
            with patch("sys.argv", test_args_empty):
                generador.main()

            # 6. Dry run / Check mode (lines 311, 350, 377)
            out_dry = os.path.join(tmpdir, "dry.xml")
            test_args_dry = [
                "generador.py",
                "-s", tmpdir,
                "-o", out_dry,
                "--dry-run"
            ]
            with patch("sys.argv", test_args_dry):
                generador.main()
            self.assertFalse(os.path.exists(out_dry))

            # 7. Failed template in main loop (lines 342-344)
            bad_c = os.path.join(tmpdir, "bad.c")
            with open(bad_c, "w", encoding="utf-8") as f:
                f.write("No markers\n")
            test_args_failed = [
                "generador.py",
                "-s", tmpdir,
                "-o", out_xml,
                "-n", "1"
            ]
            with patch("sys.argv", test_args_failed):
                generador.main()

    def test_generador_run_as_main(self):
        # Execute generador.py as __main__ using runpy
        test_args = ["generador.py", "-h"]
        with patch("sys.argv", test_args):
            with self.assertRaises(SystemExit):
                runpy.run_module("generador", run_name="__main__")
