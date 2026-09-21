"""Regresión de IDKFA-D0402: los alias de spellcheck no se repiten en --help."""

from typer.testing import CliRunner

from idkfa.cli import app

runner = CliRunner()


def test_help_lista_solo_spellcheck():
    res = runner.invoke(app, ["--help"], env={"NO_COLOR": "1", "COLUMNS": "200"})
    assert res.exit_code == 0
    palabras = [p for p in res.output.split() if p in ("spellcheck", "grammar", "languagetool")]
    assert palabras == ["spellcheck"]


def test_los_alias_siguen_funcionando():
    for alias in ("grammar", "languagetool"):
        assert runner.invoke(app, [alias, "--help"], env={"NO_COLOR": "1"}).exit_code == 0
