"""Generador de explicaciones pedagógicas para opciones distractoras en IDKFA."""

from __future__ import annotations

from typing import Dict, List, Any


def explicar_distractor(valor_correcto: str, valor_distractor: str, tipo_pregunta: str = "general") -> str:
    """Genera una explicación didáctica del error conceptual que conduce a la opción incorrecta."""
    try:
        vc = int(valor_correcto)
        vd = int(valor_distractor)
        if vd == vc + 1:
            return "Error Off-By-One: el bucle iteró una vez más de lo debido (condición <= en lugar de <)."
        elif vd == vc - 1:
            return "Error Off-By-One: el bucle finalizó una iteración antes (condición < estricta)."
        elif vd == 0:
            return "El estudiante asumió erróneamente que la condición del if evaluó a falso o no modificó el acumulador."
        elif vd == vc * 2:
            return "Confusión de doble incremento: la variable se actualizó tanto en el cuerpo como en el incremento del for."
    except ValueError:
        pass

    return f"Resultado incorrecto derivado de asumir un orden de evaluación alternativo ({valor_distractor} vs {valor_correcto})."
