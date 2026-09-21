"""Regresión de IDKFA-D0802: el README documenta todos los comandos synth-*/export-standalone."""

from pathlib import Path

from typer.main import get_command

from idkfa.cli import app

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")


def test_readme_documenta_los_comandos_de_sintesis():
    nombres = [n for n in get_command(app).commands if n.startswith("synth-") or n == "export-standalone"]
    assert len(nombres) == 5
    for n in nombres:
        assert f"idkfa {n}" in README, n
