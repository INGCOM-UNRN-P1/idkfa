"""Variantes con comportamiento indefinido se descartan (QoL #546)."""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from idkfa.compiler import FLAGS_UB, compile_and_run_c


def _ubsan_trampa_disponible() -> bool:
    gcc = shutil.which("gcc")
    if not gcc:
        return False
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "a.c"
        src.write_text("int main(void) { return 0; }\n", encoding="utf-8")
        return subprocess.run([gcc, *FLAGS_UB, str(src), "-o", str(Path(d) / "a")],
                              capture_output=True, check=False).returncode == 0


necesita_ubsan = pytest.mark.skipif(not _ubsan_trampa_disponible(), reason="requiere gcc con UBSan en modo trampa")

DESBORDE = ('#include <stdio.h>\n#include <limits.h>\n'
            'int main(void) { int n = __N__; int x = INT_MAX - 1; x = x + n; printf("%d\\n", x); return 0; }\n')


@necesita_ubsan
def test_la_variante_con_ub_se_marca():
    res = compile_and_run_c(DESBORDE.replace("__N__", "2"), 3, validar_ub=True, base_flags=["-O0"], log_file="/dev/null")
    assert res["status"] == "undefined_behavior" and res["ub_verificado"]


@necesita_ubsan
def test_la_variante_sin_ub_pasa_con_su_salida():
    res = compile_and_run_c(DESBORDE.replace("__N__", "0"), 3, validar_ub=True, base_flags=["-O0"], log_file="/dev/null")
    assert res == {"status": "success", "output": "2147483646", "ub_verificado": True}


@necesita_ubsan
def test_indice_fuera_de_rango_es_ub():
    codigo = '#include <stdio.h>\nint main(void) { int a[3] = {1, 2, 3}; int i = 3; printf("%d\\n", a[i]); return 0; }\n'
    assert compile_and_run_c(codigo, 3, validar_ub=True, base_flags=["-O0"], log_file="/dev/null")["status"] == "undefined_behavior"


def test_sin_validar_no_cambia_el_comportamiento():
    codigo = '#include <stdio.h>\nint main(void) { printf("7\\n"); return 0; }\n'
    res = compile_and_run_c(codigo, 3, base_flags=["-O0"], log_file="/dev/null")
    assert res == {"status": "success", "output": "7"}


def test_si_el_compilador_no_admite_ubsan_se_compila_sin_el(monkeypatch):
    import idkfa.compiler as compiler

    monkeypatch.setattr(compiler, "FLAGS_UB", ["--bandera-que-no-existe"])
    codigo = '#include <stdio.h>\nint main(void) { printf("7\\n"); return 0; }\n'
    res = compiler.compile_and_run_c(codigo, 3, validar_ub=True, base_flags=["-O0"], log_file="/dev/null")
    assert res == {"status": "success", "output": "7", "ub_verificado": False}
