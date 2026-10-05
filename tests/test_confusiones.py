"""Distractores basados en confusiones frecuentes (QoL #512)."""

from idkfa.variables import confusiones_frecuentes, generate_incorrect_answers


def _textos(respuesta):
    return [t for t, _ in confusiones_frecuentes(respuesta)]


def test_entero_una_vuelta_de_mas_y_de_menos():
    assert _textos("10") == ["11", "9"]
    assert _textos("65") == ["66", "64", "A"]  # 65 es imprimible: también su carácter


def test_real_division_entera():
    assert _textos("3.5") == ["3"]


def test_caracter_y_codigo():
    assert _textos("A") == ["65"]


def test_secuencias():
    assert _textos("1 2 3") == ["3 2 1", "1 2"]


def test_los_distractores_llevan_la_explicacion():
    opciones = generate_incorrect_answers("10", [], [], {}, count=2)
    textos = {o.text: o.feedback for o in opciones}
    assert set(textos) == {"11", "9"} and all(textos.values())
