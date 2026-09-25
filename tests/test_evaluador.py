"""Evaluación restringida de expresiones de plantilla (N-IDKFA-02).

Antes las expresiones se evaluaban con `eval` y los builtins completos: una
plantilla compartida podía ejecutar código arbitrario.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from idkfa.evaluador import ExpresionNoPermitida, evaluar
from idkfa.variables import generate_vars

# Lambda recursiva real de templates/basicos/forpy.c
LAMBDA_RECURSIVA = (
    "(lambda limit, mult: (lambda f, x, n: f(f, x, n))"
    "(lambda f, x, n: x if n == 0 else (f(f, x, n-1) + (n-1)) * mult, 0, limit))(4, 2)"
)


@pytest.mark.parametrize(
    ("expresion", "variables", "esperado"),
    [
        ("range(4, 8)", None, range(4, 8)),
        ("sum(range(5))", None, 10),
        ("__a__ * __b__", {"__a__": 3, "__b__": 4}, 12),
        ("a - b", {"a": 9, "b": 4}, 5),
        ("[x * 2 for x in range(3)]", None, [0, 2, 4]),
        ("chr(ord('a') + 1)", None, "b"),
        ("'abc'.upper()", None, "ABC"),
        ("f'{n} elementos'", {"n": 3}, "3 elementos"),
        ("max([3, 7, 5]) if n > 0 else 0", {"n": 1}, 7),
        ("2 ** 10", None, 1024),
        (LAMBDA_RECURSIVA, None, 22),  # mismo resultado que el eval de Python
    ],
)
def test_expresiones_de_plantilla_permitidas(expresion, variables, esperado):
    assert evaluar(expresion, variables) == esperado


@pytest.mark.parametrize(
    "expresion",
    [
        "__import__('os').system('true')",
        "().__class__.__bases__[0].__subclasses__()",
        "open('/etc/passwd').read()",
        "getattr(1, 'real')",
        "eval('1 + 1')",
        "(lambda: 0).__globals__",
        "f'{n.__class__}'",
        "9 ** 9 ** 9",
        "10 ** 100000",
        "__builtins__",
    ],
)
def test_escapes_bloqueados(expresion):
    with pytest.raises((ExpresionNoPermitida, NameError)):
        evaluar(expresion, {"n": 1})


def test_una_plantilla_maliciosa_no_ejecuta_codigo(tmp_path: Path):
    marca = tmp_path / "ejecutado"
    definiciones = {"n": f"__import__('pathlib').Path({str(marca)!r}).touch() or range(1, 3)"}
    generate_vars(definiciones)
    assert not marca.exists()
