"""Los errores de uso de idkfa deben verse como mensajes, no como tracebacks (N-IDKFA-01).

`idkfa.generacion.main` invoca la app con standalone_mode=False y solo
capturaba Exit: una opción inexistente o un argumento sobrante (incluido
`--version`, que no existía) terminaban en un traceback de Click.
"""

from __future__ import annotations

import pytest

from idkfa.generacion import main


def test_version(capsys):
    main(["--version"])
    salida = capsys.readouterr().out
    assert salida.startswith("idkfa ")


@pytest.mark.parametrize("args", [["--no-existe"], ["doctor", "argumento-sobrante"]])
def test_error_de_uso_sale_con_2_y_sin_traceback(capsys, args):
    with pytest.raises(SystemExit) as salida:
        main(args)
    assert salida.value.code == 2
    err = capsys.readouterr().err
    assert "Error:" in err
    assert "Traceback" not in err
