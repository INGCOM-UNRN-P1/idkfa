"""Módulo de verificación ortográfica con LanguageTool en idkfa — Delegado a myst-tools."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple, Dict, Any

try:
    from myst_tools.languagetool_checker import (
        DEFAULT_LANGUAGETOOL_URL,
        DEFAULT_LANGUAGETOOL_PREMIUM_URL,
        LOCAL_LANGUAGETOOL_URL,
        PALABRAS_IGNORADAS_DEFAULT,
        LanguageToolIssue,
        consultar_languagetool,
        analizar_texto_languagetool,
        generar_reporte_markdown as generar_reporte_markdown_languagetool,
    )
except ImportError:
    sibling = Path(__file__).resolve().parents[2] / "myst-tools" / "src"
    if sibling.is_dir() and str(sibling) not in sys.path:
        sys.path.insert(0, str(sibling))
    from myst_tools.languagetool_checker import (
        DEFAULT_LANGUAGETOOL_URL,
        DEFAULT_LANGUAGETOOL_PREMIUM_URL,
        LOCAL_LANGUAGETOOL_URL,
        PALABRAS_IGNORADAS_DEFAULT,
        LanguageToolIssue,
        consultar_languagetool,
        analizar_texto_languagetool,
        generar_reporte_markdown as generar_reporte_markdown_languagetool,
    )


def enmascarar_plantilla(contenido: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Enmascara comentarios técnicos de variables, directivas #pragma, código C y etiquetas XML."""
    enmascarado = list(contenido)
    mascaras = []

    def _mask_range(start: int, end: int, preserve_newlines: bool = True):
        for i in range(start, end):
            if preserve_newlines and enmascarado[i] == '\n':
                continue
            enmascarado[i] = ' '
        mascaras.append({"start": start, "end": end})

    # 1. Etiquetas XML / HTML <...>
    for m in re.finditer(r'<[^>\n]+>', contenido):
        _mask_range(m.start(), m.end())

    # 2. Directivas C (#include, #define, #pragma)
    for m in re.finditer(r'^\s*#.*$', contenido, re.MULTILINE):
        _mask_range(m.start(), m.end())

    # 3. Comentarios de definición de variables /// @var o // @...
    for m in re.finditer(r'//\s*@[^\n]+', contenido):
        _mask_range(m.start(), m.end())

    # 4. Código C entre funciones o bloques
    for m in re.finditer(r'(```|~~~)[^\n]*\n.*?\n\s*\1', contenido, re.DOTALL):
        _mask_range(m.start(), m.end())
    for m in re.finditer(r'`[^`\n]+`', contenido):
        _mask_range(m.start(), m.end())

    # 5. Formatos CDATA
    for m in re.finditer(r'<!\[CDATA\[', contenido):
        _mask_range(m.start(), m.end())
    for m in re.finditer(r'\]\]>', contenido):
        _mask_range(m.start(), m.end())

    return "".join(enmascarado), mascaras


def analizar_archivo_languagetool(
    file_path: Path,
    lang: str = "es-AR",
    server_url: Optional[str] = None,
    username: Optional[str] = None,
    api_key: Optional[str] = None,
    premium: bool = False,
    ignore_words: Optional[Set[str]] = None,
    ignore_rules: Optional[Set[str]] = None,
) -> List[LanguageToolIssue]:
    """Analiza ortografía en comentarios explicativos y enunciados de plantillas o cuestionarios."""
    if not file_path.is_file():
        return []

    contenido = file_path.read_text(encoding="utf-8", errors="replace")
    return analizar_texto_languagetool(
        contenido,
        file_path=file_path,
        lang=lang,
        server_url=server_url,
        username=username,
        api_key=api_key,
        premium=premium,
        ignore_words=ignore_words,
        ignore_rules=ignore_rules,
        custom_mask_fn=enmascarar_plantilla,
    )
