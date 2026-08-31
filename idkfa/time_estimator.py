"""Calculador de tiempo estimado de resolución cognitiva de trazas C."""

from __future__ import annotations

import re


def estimar_tiempo_resolucion(codigo_c: str) -> int:
    """Calcula el tiempo promedio estimado (en segundos) para resolver mentalmente el snippet."""
    lineas = [l for l in codigo_c.splitlines() if l.strip()]
    tiempo_base = 30  # 30 segundos lectura base
    
    # Cada bucle agrega ~20s
    bucles = len(re.findall(r"\b(for|while)\b", codigo_c))
    tiempo_base += bucles * 25
    
    # Cada función recursiva agrega ~40s
    if "return " in codigo_c and re.search(r"(\w+)\s*\([^)]*\)\s*\{.*\1\s*\(", codigo_c, re.DOTALL):
        tiempo_base += 45
        
    # Punteros y structs agregan ~15s
    punteros = len(re.findall(r"\*|->|&", codigo_c))
    tiempo_base += min(punteros * 5, 30)

    return tiempo_base
