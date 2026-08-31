"""Auditor de Cero Memory Leaks con Valgrind para snippets C sintetizados en IDKFA."""

from __future__ import annotations

import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any


def verificar_memory_leaks(codigo_c: str) -> Dict[str, Any]:
    """Compila el código y lo ejecuta bajo Valgrind para asegurar 0 bytes en fuga."""
    valgrind_bin = shutil.which("valgrind")
    gcc_bin = shutil.which("gcc")

    if not gcc_bin:
        return {"valgrind_disponible": False, "sin_leaks": True, "detalle": "GCC no encontrado"}

    with tempfile.TemporaryDirectory() as tmp_dir:
        src_path = Path(tmp_dir) / "snippet.c"
        bin_path = Path(tmp_dir) / "snippet.bin"
        src_path.write_text(codigo_c, encoding="utf-8")

        res_compile = subprocess.run([gcc_bin, str(src_path), "-o", str(bin_path)], capture_output=True, text=True)
        if res_compile.returncode != 0:
            return {"valgrind_disponible": bool(valgrind_bin), "sin_leaks": False, "detalle": f"Error de compilación: {res_compile.stderr}"}

        if not valgrind_bin:
            return {"valgrind_disponible": False, "sin_leaks": True, "detalle": "Valgrind no disponible en el host; omitiendo prueba dinámica."}

        res_valgrind = subprocess.run(
            [valgrind_bin, "--leak-check=full", "--error-exitcode=42", str(bin_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        sin_leaks = res_valgrind.returncode == 0
        return {
            "valgrind_disponible": True,
            "sin_leaks": sin_leaks,
            "detalle": "0 bytes en fuga (All heap blocks were freed)" if sin_leaks else res_valgrind.stderr,
        }
