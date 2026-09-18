"""Regresión de IDKFA-D0601: la generación principal no tenía `--json`.

Solo lo tenían `spellcheck` y `synth-*` (sin `schema_version`); el flujo central —plantillas
a XML Moodle— solo emitía texto para humanos, inservible para un script o un orquestador.
"""

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from idkfa.cli import app

runner = CliRunner()
RAIZ = Path(__file__).resolve().parents[1]
PLANTILLA = RAIZ / "templates" / "basicos" / "suma_stdin.c"
necesita_gcc = pytest.mark.skipif(not shutil.which("gcc"), reason="requiere gcc")


def _json(res):
    return json.loads(res.stdout)


@necesita_gcc
def test_la_generacion_emite_json_puro_por_stdout(tmp_path):
    salida = tmp_path / "q.xml"
    res = runner.invoke(app, ["-t", str(PLANTILLA), "-o", str(salida), "-n", "2", "--json"])
    assert res.exit_code == 0, res.output
    datos = _json(res)  # falla si el progreso o el reporte se colaron en stdout
    assert datos["schema_version"] == "1.0.0"
    assert datos["ok"] is True and datos["dry_run"] is False
    assert datos["plantillas_procesadas"] == 1 and datos["plantillas_exitosas"] == 1
    assert datos["preguntas_generadas"] == 2
    assert datos["archivo_salida"] == str(salida) and salida.is_file()
    assert datos["errores"] == []


@necesita_gcc
def test_dry_run_no_escribe_xml_y_lo_dice_en_el_json(tmp_path):
    salida = tmp_path / "q.xml"
    res = runner.invoke(app, ["-t", str(PLANTILLA), "-o", str(salida), "-n", "1", "--dry-run", "--json"])
    datos = _json(res)
    assert datos["dry_run"] is True and datos["archivo_salida"] is None
    assert not salida.exists()


def test_una_plantilla_que_falla_sale_con_1_y_lista_el_error(tmp_path):
    rota = tmp_path / "rota.c"
    rota.write_text("int main( { esto no compila\n", encoding="utf-8")
    res = runner.invoke(app, ["-t", str(rota), "-o", str(tmp_path / "q.xml"), "--json"])
    assert res.exit_code == 1
    datos = _json(res)
    assert datos["ok"] is False and datos["plantillas_fallidas"] == 1
    assert datos["errores"] and datos["errores"][0]["plantilla"].endswith("rota.c")
    assert datos["errores"][0]["razon"]


def test_un_directorio_sin_plantillas_da_json_vacio_y_ok(tmp_path):
    vacio = tmp_path / "vacio"
    vacio.mkdir()
    res = runner.invoke(app, ["-s", str(vacio), "-o", str(tmp_path / "q.xml"), "--json"])
    assert res.exit_code == 0
    datos = _json(res)
    assert datos["plantillas_procesadas"] == 0 and datos["ok"] is True


def test_json_y_generate_only_son_incompatibles(tmp_path):
    res = runner.invoke(app, ["-t", str(PLANTILLA), "--generate-only", "--json"])
    assert res.exit_code == 2


@necesita_gcc
def test_sin_json_la_salida_humana_no_cambia(tmp_path):
    res = runner.invoke(app, ["-t", str(PLANTILLA), "-o", str(tmp_path / "q.xml"), "-n", "1"])
    assert res.exit_code == 0
    assert "REPORTE DE EJECUCIÓN" in res.stdout
    with pytest.raises(json.JSONDecodeError):
        json.loads(res.stdout)


@necesita_gcc
def test_los_synth_versionan_su_json():
    for comando in ("synth-bst", "synth-matrix", "synth-linked-list", "synth-tf"):
        res = runner.invoke(app, [comando, "--json"])
        assert res.exit_code == 0, (comando, res.output)
        assert _json(res)["schema_version"] == "1.0.0", comando
