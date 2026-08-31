"""Tests para el verificador de LanguageTool en idkfa."""

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from idkfa.cli import app
from idkfa.languagetool_checker import (
    enmascarar_plantilla,
    consultar_languagetool,
    analizar_archivo_languagetool,
    generar_reporte_markdown_languagetool,
    LanguageToolIssue,
)

runner = CliRunner()


def test_enmascarar_plantilla_idkfa():
    texto = (
        "// Plantilla de C para ordenamiento\n"
        "#include <stdio.h>\n"
        "/// @var A = [1, 2, 3]\n"
        "<p>Pregunta HTML con `int a = 5;`</p>\n"
        "Explicación del ejercicio.\n"
    )
    enmascarado, _ = enmascarar_plantilla(texto)
    assert "Explicación del ejercicio." in enmascarado
    assert "#include <stdio.h>" not in enmascarado
    assert "<p>" not in enmascarado
    assert "@var A" not in enmascarado
    assert len(enmascarado) == len(texto)


def test_consultar_languagetool_idkfa_premium(monkeypatch):
    captured = []

    class MockResponse:
        status = 200
        def read(self):
            return json.dumps({"matches": []}).encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10.0: (captured.append(req), MockResponse())[1])

    # 1. Local
    consultar_languagetool("Texto de prueba")
    assert len(captured) == 1

    # 2. Premium
    consultar_languagetool("Texto", username="docente@uba.ar", api_key="idkfa-key-789", premium=True)
    assert len(captured) == 2
    assert "api.languagetoolplus.com" in captured[1].full_url
    body = captured[1].data.decode("utf-8")
    assert "username=docente%40uba.ar" in body
    assert "apiKey=idkfa-key-789" in body


def test_analizar_archivo_plantilla_c(tmp_path: Path, monkeypatch):
    plantilla = tmp_path / "template.c"
    plantilla.write_text("// Comentario con prueva de texto\n#include <stdio.h>\nint main() { return 0; }\n", encoding="utf-8")

    sample_response = {
        "matches": [
            {
                "message": "Falta de ortografía",
                "shortMessage": "Error",
                "offset": 18,
                "length": 6,
                "rule": {"id": "MORFOLOGIK_RULE_ES", "category": {"name": "Ortografía"}},
                "context": {"text": "Comentario con prueva de texto", "offset": 18, "length": 6},
                "replacements": [{"value": "prueba"}],
            }
        ]
    }

    class MockResponse:
        status = 200
        def read(self):
            return json.dumps(sample_response).encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10.0: MockResponse())

    issues = analizar_archivo_languagetool(plantilla)
    assert len(issues) >= 1
    assert issues[0].original_word == "prueva"


def test_cli_spellcheck_idkfa(tmp_path: Path, monkeypatch):
    plantilla = tmp_path / "test.c"
    plantilla.write_text("// Texto con errror\n", encoding="utf-8")

    sample_response = {
        "matches": [
            {
                "message": "Error",
                "shortMessage": "Error",
                "offset": 13,
                "length": 6,
                "rule": {"id": "TEST", "category": {"name": "Ortografía"}},
                "context": {"text": "Texto con errror", "offset": 13, "length": 6},
                "replacements": [{"value": "error"}],
            }
        ]
    }

    class MockResponse:
        status = 200
        def read(self):
            return json.dumps(sample_response).encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10.0: MockResponse())

    res = runner.invoke(app, ["spellcheck", str(plantilla)])
    assert res.exit_code == 1
    assert "Observaciones de LanguageTool" in res.output

    # JSON
    res_json = runner.invoke(app, ["spellcheck", str(plantilla), "--json"])
    assert res_json.exit_code == 1
    assert "total_issues" in res_json.output

    # Markdown
    md_out = tmp_path / "rep.md"
    res_md = runner.invoke(app, ["spellcheck", str(plantilla), "--md", str(md_out)])
    assert res_md.exit_code == 1
    assert md_out.is_file()
