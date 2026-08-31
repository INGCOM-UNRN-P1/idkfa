"""Sintetizador de snippets procedurales con operadores a nivel de bits y máscaras."""

from __future__ import annotations

import random
from typing import Dict, Any


def generar_snippet_bitwise(seed: int | None = None) -> Dict[str, Any]:
    """Genera un snippet C determinista con operaciones AND, OR, XOR y desplazamientos."""
    rng = random.Random(seed)
    val_a = rng.randint(0x0F, 0xFF)
    shift = rng.randint(1, 3)
    mascara = rng.choice([0x0F, 0x55, 0xAA, 0xF0])
    
    codigo = f"""#include <stdio.h>
int main(void) {{
    unsigned char x = {hex(val_a)};
    unsigned char y = (x << {shift}) & {hex(mascara)};
    printf("%u\\n", y);
    return 0;
}}
"""
    # Calcular salida esperada
    res = ((val_a << shift) & mascara) & 0xFF
    return {
        "codigo": codigo,
        "salida_esperada": str(res),
        "variables": {"x": hex(val_a), "shift": shift, "mascara": hex(mascara)},
    }
