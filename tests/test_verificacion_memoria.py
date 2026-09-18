"""Regresión de IDKFA-D0301: la verificación de fugas debe estar en el flujo.

`verificar_memory_leaks` existía con gcc+valgrind reales, pero ningún módulo
del flujo de emisión lo invocaba pese a que el README promete "cero fugas de
memoria". La desconexión no era teórica: las plantillas de BST y de lista
enlazada emitían snippets que perdían 120 y 48 bytes, publicados como material
de examen en una materia donde liberar la memoria es la regla.
"""

import shutil

import pytest

from idkfa import procedural_synth as ps
from idkfa.leak_checker import verificar_memory_leaks

GENERADORES = [
    ("bst", ps.generar_bst_y_recorrido),
    ("matriz", ps.generar_matriz_2d_y_puntero_plano),
    ("lista", ps.generar_lista_enlazada_simple),
    ("efectos", ps.inyectar_efectos_secundarios_y_sequence_points),
]

necesita_valgrind = pytest.mark.skipif(
    not (shutil.which("gcc") and shutil.which("valgrind")),
    reason="requiere gcc y valgrind",
)


@pytest.mark.parametrize("nombre, generador", GENERADORES)
def test_el_resultado_reporta_el_estado_de_memoria(nombre, generador):
    """Todo generador debe exponer si el snippet quedó libre de fugas."""
    resultado = generador(seed=7)
    assert "sin_leaks" in resultado
    assert "valgrind_disponible" in resultado


@necesita_valgrind
@pytest.mark.parametrize("nombre, generador", GENERADORES)
def test_los_snippets_emitidos_no_pierden_memoria(nombre, generador):
    resultado = generador(seed=7)
    assert resultado["verificado_gcc"] is True
    assert resultado["sin_leaks"] is True, resultado["detalle_memoria"]


@pytest.mark.parametrize(
    "nombre, generador", [g for g in GENERADORES if g[0] in ("bst", "lista")]
)
def test_las_plantillas_con_malloc_respetan_las_reglas_de_catedra(nombre, generador):
    """Sin casteo de malloc (antipatrón que marca spunkmeyer) y con free."""
    codigo = generador(seed=7)["codigo"]
    assert "(Nodo*)malloc" not in codigo
    assert "free(" in codigo


@necesita_valgrind
def test_el_verificador_detecta_una_fuga_real():
    """Si el chequeo no distinguiera, conectarlo no serviría de nada."""
    con_fuga = (
        "#include <stdlib.h>\n"
        "int main(void) { int *p = malloc(64); if (!p) return 1; p[0] = 1; return 0; }\n"
    )
    assert verificar_memory_leaks(con_fuga)["sin_leaks"] is False
