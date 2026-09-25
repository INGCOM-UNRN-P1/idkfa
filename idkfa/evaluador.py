"""Evaluación restringida de las expresiones de las plantillas (N-IDKFA-02).

Las plantillas definen variables (`n: range(1, 10)`), respuestas correctas,
distractores, STDIN y retroalimentación con expresiones Python. Antes se
evaluaban con `eval` y los builtins completos: una plantilla compartida
podía ejecutar código arbitrario (`__import__('os').system(...)`).

`evaluar` valida el árbol sintáctico contra una lista blanca y lo ejecuta
con un conjunto acotado de funciones. Alcanza para lo que usan las
plantillas —aritmética, comparaciones, listas y comprensiones, `range`,
`sum`, `min`/`max`, `chr`/`ord`, f-strings e incluso lambdas recursivas—
pero no para acceder a atributos privados (`().__class__…`), importar
módulos, abrir archivos ni llamar a `eval`/`getattr`.
"""

from __future__ import annotations

import ast
from functools import lru_cache
from typing import Any, Mapping, Optional

# Funciones disponibles dentro de las expresiones.
FUNCIONES_PERMITIDAS: dict = {
    "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool, "chr": chr,
    "dict": dict, "divmod": divmod, "enumerate": enumerate, "filter": filter,
    "float": float, "hex": hex, "int": int, "len": len, "list": list, "map": map,
    "max": max, "min": min, "oct": oct, "ord": ord, "range": range,
    "reversed": reversed, "round": round, "set": set, "sorted": sorted,
    "str": str, "sum": sum, "tuple": tuple, "zip": zip,
    "True": True, "False": False, "None": None,
}

_NODOS_PERMITIDOS = (
    ast.Expression, ast.Constant, ast.Name, ast.Load, ast.Store,
    ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.IfExp,
    ast.Call, ast.keyword, ast.Lambda, ast.arguments, ast.arg,
    ast.List, ast.Tuple, ast.Set, ast.Dict, ast.Starred,
    ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.comprehension,
    ast.Subscript, ast.Slice, ast.Attribute,
    ast.JoinedStr, ast.FormattedValue,
    ast.operator, ast.unaryop, ast.boolop, ast.cmpop,
)

# Tope para el exponente de `**`: evita que una expresión como 9 ** 9 ** 9
# deje colgada la generación.
MAX_EXPONENTE = 10_000


class ExpresionNoPermitida(ValueError):
    """La expresión usa construcciones fuera de la lista blanca."""


def _validar(arbol: ast.AST, nombres_disponibles: frozenset) -> None:
    locales_lambda: set = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.arg):
            locales_lambda.add(nodo.arg)
        elif isinstance(nodo, ast.comprehension):
            for destino in ast.walk(nodo.target):
                if isinstance(destino, ast.Name):
                    locales_lambda.add(destino.id)
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, _NODOS_PERMITIDOS):
            raise ExpresionNoPermitida(f"construcción no permitida: {type(nodo).__name__}")
        if isinstance(nodo, ast.Attribute) and nodo.attr.startswith("_"):
            raise ExpresionNoPermitida(f"atributo no permitido: {nodo.attr}")
        if isinstance(nodo, ast.Name) and nodo.id.startswith("__") and nodo.id not in nombres_disponibles:
            raise ExpresionNoPermitida(f"nombre no permitido: {nodo.id}")
        if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Pow):
            exponente = nodo.right
            if isinstance(exponente, ast.Constant) and isinstance(exponente.value, (int, float)):
                if abs(exponente.value) > MAX_EXPONENTE:
                    raise ExpresionNoPermitida(f"exponente demasiado grande: {exponente.value}")
            elif isinstance(exponente, ast.BinOp) and isinstance(exponente.op, ast.Pow):
                raise ExpresionNoPermitida("potencias encadenadas no permitidas")


@lru_cache(maxsize=4096)
def _compilar(expresion: str, nombres_disponibles: frozenset):
    arbol = ast.parse(expresion.strip(), mode="eval")
    _validar(arbol, nombres_disponibles)
    return compile(arbol, "<plantilla>", "eval")


def evaluar(expresion: str, variables: Optional[Mapping[str, Any]] = None) -> Any:
    """Evalúa una expresión de plantilla con las variables dadas.

    Lanza ExpresionNoPermitida si la expresión sale de la lista blanca, y
    las excepciones normales de Python (NameError, ZeroDivisionError, …) si
    la expresión es válida pero falla al evaluarse.
    """
    variables = dict(variables or {})
    codigo = _compilar(expresion, frozenset(variables))
    return eval(codigo, {"__builtins__": FUNCIONES_PERMITIDAS}, variables)  # noqa: S307 - AST validado
