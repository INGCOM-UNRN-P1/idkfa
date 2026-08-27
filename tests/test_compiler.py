import os
import tempfile
import unittest
from unittest.mock import patch
import subprocess
from idkfa.compiler import compile_and_run_c

class TestCompiler(unittest.TestCase):
    def test_compile_and_run_success(self):
        code = '#include <stdio.h>\nint main() { printf("success_output"); return 0; }'
        res = compile_and_run_c(code, timeout=5)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["output"], "success_output")

    def test_compile_and_run_stdin(self):
        code = '#include <stdio.h>\nint main() { int x; if (scanf("%d", &x) == 1) printf("val:%d", x*2); return 0; }'
        res = compile_and_run_c(code, timeout=5, stdin_input="21")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["output"], "val:42")

    def test_compile_and_run_extra_flags(self):
        code = '#include <stdio.h>\n#include <math.h>\nint main() { printf("%.1f", sqrt(9.0)); return 0; }'
        # Pass extra_flags with one already present and one new
        res = compile_and_run_c(code, timeout=5, extra_flags=["-Wall", "-lm"], base_flags=["-Wall"])
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["output"], "3.0")

    def test_compile_error_logging_with_template_name(self):
        code = 'int main() { syntax_error; }'
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
            log_path = f.name

        try:
            res = compile_and_run_c(
                code,
                timeout=5,
                template_name="test_template.c",
                log_file=log_path
            )
            self.assertEqual(res["status"], "compile_error")
            with open(log_path, "r", encoding="utf-8") as f:
                log_content = f.read()
            self.assertIn("Template: test_template.c", log_content)
            self.assertIn("COMPILE ERROR", log_content)
        finally:
            if os.path.exists(log_path):
                os.remove(log_path)

    def test_compile_error_logging_default_log(self):
        code = 'int main() { syntax_error; }'
        with tempfile.TemporaryDirectory() as tmpdir:
            default_log = os.path.join(tmpdir, "default_compile.log")
            with patch.dict("idkfa.compiler.CONFIG", {"compilation_error_log": default_log}):
                res = compile_and_run_c(code, timeout=5, log_file=None, template_name=None)
                self.assertEqual(res["status"], "compile_error")
                self.assertTrue(os.path.exists(default_log))

    def test_runtime_error(self):
        code = '#include <stdlib.h>\nint main() { exit(1); }'
        res = compile_and_run_c(code, timeout=5)
        self.assertEqual(res["status"], "runtime_error")
        self.assertIn("error en tiempo de ejecución", res["output"])

    def test_timeout_expired(self):
        code = 'int main() { while(1); return 0; }'
        res = compile_and_run_c(code, timeout=1)
        self.assertEqual(res["status"], "timeout")
        self.assertIn("tiempo límite", res["output"])

    def test_exception_invalid_compiler(self):
        # Lines 68-69: except Exception as e: return {"status": "error", "output": str(e)}
        code = 'int main() { return 0; }'
        res = compile_and_run_c(code, timeout=5, custom_compiler="/non/existent/compiler/binary_xyz_123")
        self.assertEqual(res["status"], "error")
        self.assertTrue(len(res["output"]) > 0)
