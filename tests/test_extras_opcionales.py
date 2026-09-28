"""idkfa funciona sin myst-tools ni daedalus instalados (N-ECO-01).

Antes, sin esas herramientas en el entorno, idkfa las buscaba con
sys.path.insert en las carpetas hermanas del monorepo: instalado desde git la
integración se perdía sin aviso y `idkfa spellcheck` terminaba en un
traceback. Ahora llegan con los extras `languagetool` y `ecosistema`; sin
ellos el CLI arranca, compila con gcc directo y spellcheck explica cómo
instalar el extra.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import idkfa

BLOQUEAR = (
    "import sys\n"
    "for m in ('myst_tools', 'myst_tools.languagetool_checker', 'daedalus', 'daedalus.core', "
    "'daedalus.core.compiler'):\n"
    "    sys.modules[m] = None\n"
)


def _correr(codigo: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", BLOQUEAR + codigo], capture_output=True, text=True, timeout=120)


def test_ningun_modulo_busca_carpetas_hermanas():
    paquete = Path(idkfa.__file__).parent
    ocultos = [str(p.relative_to(paquete)) for p in paquete.rglob("*.py")
               if "sys.path.insert" in p.read_text(encoding="utf-8")]
    assert ocultos == []


def test_la_ayuda_funciona_sin_myst_tools_ni_daedalus():
    resultado = _correr("from idkfa.generacion import main\nmain(['--help'])\n")
    assert resultado.returncode == 0, resultado.stderr
    assert "spellcheck" in resultado.stdout


def test_spellcheck_sin_myst_tools_explica_el_extra(tmp_path):
    plantilla = tmp_path / "plantilla.c"
    plantilla.write_text("int main(void) { return 0; }\n", encoding="utf-8")
    resultado = _correr(f"from idkfa.generacion import main\nmain(['spellcheck', {str(plantilla)!r}])\n")
    salida = resultado.stdout + resultado.stderr
    assert resultado.returncode == 1
    assert "extra languagetool" in salida
    assert '"idkfa[languagetool] @ git+https://github.com/INGCOM-UNRN-P1/idkfa"' in salida
    assert "Traceback" not in salida


@pytest.mark.skipif(shutil.which("gcc") is None, reason="requiere gcc en el PATH")
def test_compila_con_gcc_sin_daedalus():
    resultado = _correr(
        "from idkfa.compiler import compile_and_run_c\n"
        "r = compile_and_run_c('#include <stdio.h>\\nint main(void) { printf(\"%d\", 6 * 7); return 0; }\\n', 10)\n"
        "print(r['status'], r['output'])\n"
    )
    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == "success 42"
