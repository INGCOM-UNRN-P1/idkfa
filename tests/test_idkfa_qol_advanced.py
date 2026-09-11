import pytest
from idkfa.procedural_synth import (
    renombrar_identificadores_tematico,
    generar_bst_y_recorrido,
    generar_matriz_2d_y_puntero_plano,
    generar_lista_enlazada_simple,
    generar_pregunta_verdadero_falso_con_justificacion,
    inyectar_efectos_secundarios_y_sequence_points,
    exportar_snippet_con_asserts,
)


def test_renombrar_identificadores_tematico():
    codigo = "int nodo = 1; int valor = 10; int arr[5];"
    gaming = renombrar_identificadores_tematico(codigo, "videojuegos")
    assert "item" in gaming
    assert "xp" in gaming
    assert "inventario" in gaming

    cine = renombrar_identificadores_tematico(codigo, "cine")
    assert "escena" in cine
    assert "minuto" in cine
    assert "guion" in cine


def test_generar_bst_y_recorrido():
    res = generar_bst_y_recorrido(valores=[20, 10, 30], tipo_recorrido="inorden")
    assert res["salida_esperada"] == "10 20 30"
    assert res["verificado_gcc"] is True
    assert res["salida_gcc"] == "10 20 30"

    res_pre = generar_bst_y_recorrido(valores=[20, 10, 30], tipo_recorrido="preorden")
    assert res_pre["salida_esperada"] == "20 10 30"
    assert res_pre["verificado_gcc"] is True


def test_generar_matriz_2d_y_puntero_plano():
    res = generar_matriz_2d_y_puntero_plano(filas=3, cols=3, seed=42)
    assert res["verificado_gcc"] is True
    assert res["salida_esperada"] == f"{res['valor']} {res['valor']}"


def test_generar_lista_enlazada_simple():
    res = generar_lista_enlazada_simple(seed=123)
    assert res["verificado_gcc"] is True
    assert len(res["salida_esperada"]) > 0


def test_generar_pregunta_verdadero_falso():
    q = generar_pregunta_verdadero_falso_con_justificacion("arrays_decay")
    assert q["es_verdadero"] is False
    assert "decaen" in q["justificacion"]

    q2 = generar_pregunta_verdadero_falso_con_justificacion("string_null_terminator")
    assert q2["es_verdadero"] is True


def test_inyectar_efectos_secundarios_y_sequence_points():
    res = inyectar_efectos_secundarios_y_sequence_points(seed=10)
    assert res["verificado_gcc"] is True
    assert len(res["salida_esperada"].split()) == 3


def test_exportar_snippet_con_asserts():
    code = "#include <stdio.h>\nint main(void) { int x = 5; printf(\"%d\", x); return 0; }"
    out = exportar_snippet_con_asserts(code, "5")
    assert "<assert.h>" in out
    assert "AUTOEVALUACIÓN" in out
    assert "int main(void)" in out
