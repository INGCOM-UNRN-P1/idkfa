"""Exportador a formato GIFT enriquecido con sintaxis C formateada para Moodle."""

from __future__ import annotations

import html
from typing import List, Dict, Any


def exportar_pregunta_gift(
    titulo: str,
    codigo_c: str,
    respuesta_correcta: str,
    distractores: List[str],
) -> str:
    """Genera una pregunta de opción múltiple en formato GIFT con bloque preformateado."""
    codigo_limpio = html.escape(codigo_c.strip())
    
    opciones = [f"={respuesta_correcta}"]
    for d in distractores:
        if str(d) != str(respuesta_correcta):
            opciones.append(f"~{d}")

    opciones_str = "\n  ".join(opciones)
    
    return f"""// {titulo}
::{titulo}::[html]<p>¿Cuál es la salida por pantalla generada al compilar y ejecutar el siguiente programa en C?</p>
<pre><code class="language-c">
{codigo_limpio}
</code></pre> {{
  {opciones_str}
}}
"""
