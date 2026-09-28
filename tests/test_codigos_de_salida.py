"""El ejecutable `idkfa` sale con el código que fija cada comando (N-IDKFA-03).

`idkfa.generacion.main` (el punto de entrada `idkfa`) invoca la app con
standalone_mode=False, y en ese modo Click no lanza el typer.Exit de los
comandos: devuelve su código. main lo ignoraba, así que `idkfa` salía con 0
aunque fallaran plantillas o spellcheck encontrara errores. Los tests con
CliRunner no lo veían porque usan el modo standalone.
"""

from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace

import pytest

from idkfa.generacion import main


def _plantilla_rota(tmp_path):
    rota = tmp_path / "rota.c"
    rota.write_text("int main( { esto no compila\n", encoding="utf-8")
    return rota


def test_una_plantilla_que_falla_sale_con_1(tmp_path):
    with pytest.raises(SystemExit) as salida:
        main(["-t", str(_plantilla_rota(tmp_path)), "-o", str(tmp_path / "q.xml"), "--json"])
    assert salida.value.code == 1


def test_el_proceso_termina_con_ese_codigo(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-c", "from idkfa.generacion import main; main()",
         "-t", str(_plantilla_rota(tmp_path)), "-o", str(tmp_path / "q.xml"), "--json"],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 1, proc.stderr


def test_spellcheck_con_observaciones_sale_con_1(tmp_path, monkeypatch):
    pytest.importorskip("myst_tools", reason="requiere el extra languagetool (myst-tools)")
    from idkfa import languagetool_checker

    plantilla = tmp_path / "plantilla.c"
    plantilla.write_text("/* un ejenplo */\nint main(void) { return 0; }\n", encoding="utf-8")
    observacion = SimpleNamespace(archivo=str(plantilla), line=1, column=7, original_word="ejenplo",
                                  context="un ejenplo", replacements=["ejemplo"], message="Posible error",
                                  rule_id="MORFOLOGIK_RULE_ES", to_dict=lambda: {"palabra": "ejenplo"})
    monkeypatch.setattr(languagetool_checker, "analizar_archivo_languagetool", lambda *a, **k: [observacion])
    with pytest.raises(SystemExit) as salida:
        main(["spellcheck", str(plantilla), "--json"])
    assert salida.value.code == 1


def test_un_comando_exitoso_no_sale_con_error(capsys):
    main(["--version"])  # no lanza SystemExit
    assert capsys.readouterr().out.startswith("idkfa ")
