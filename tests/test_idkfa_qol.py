"""Tests para las mejoras QoL de IDKFA."""

from idkfa.leak_checker import verificar_memory_leaks
from idkfa.bitwise_synth import generar_snippet_bitwise
from idkfa.distractor_explainer import explicar_distractor
from idkfa.time_estimator import estimar_tiempo_resolucion
from idkfa.gift_exporter import exportar_pregunta_gift


def test_leak_checker():
    codigo_ok = "#include <stdlib.h>\nint main(void) { int *p = malloc(sizeof(int)); free(p); return 0; }\n"
    res = verificar_memory_leaks(codigo_ok)
    assert res["sin_leaks"] is True


def test_bitwise_synth():
    snip = generar_snippet_bitwise(seed=123)
    assert "unsigned char" in snip["codigo"]
    assert snip["salida_esperada"].isdigit()


def test_distractor_explainer():
    exp1 = explicar_distractor("10", "11")
    exp2 = explicar_distractor("10", "9")
    assert "Off-By-One" in exp1
    assert "Off-By-One" in exp2


def test_time_estimator():
    c_simple = "int main(void) { return 0; }"
    c_complejo = """
int fact(int n) { if (n <= 1) return 1; return n * fact(n-1); }
int main(void) {
    for(int i=0; i<10; i++) { int *p = NULL; }
    return 0;
}
"""
    t1 = estimar_tiempo_resolucion(c_simple)
    t2 = estimar_tiempo_resolucion(c_complejo)
    assert t2 > t1


def test_gift_exporter():
    res = exportar_pregunta_gift("Trazas P1", "int main(void){ return 0; }", "0", ["1", "2", "42"])
    assert "::Trazas P1::" in res
    assert "=0" in res
    assert "~1" in res
