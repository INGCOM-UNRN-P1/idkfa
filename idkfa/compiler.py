"""Módulo para la compilación y ejecución segura de código C."""

import os
import subprocess
import datetime
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from idkfa.config import CONFIG

# UBSan en modo trampa: ante un comportamiento indefinido el programa termina con SIGILL. No
# necesita libubsan, así que anda también con MinGW y en Linux sin el paquete del sanitizer.
FLAGS_UB = ["-fsanitize=undefined", "-fsanitize-undefined-trap-on-error"]
_SENALES_UB = (-4, 132)  # SIGILL (o 128 + 4 si pasa por un shell)


def _try_daedalus_compile(src_path: str, exe_path: str, flags: List[str], timeout: int):
    """Intenta compilar con DAEDALUS (extra `ecosistema`); sin él devuelve None y se usa gcc directo."""
    try:
        from daedalus.core.compiler import compilar_archivos
    except ImportError:
        return None
    return compilar_archivos([Path(src_path)], binario_salida=Path(exe_path), flags_adicionales=flags, timeout=timeout)


def compile_and_run_c(
    code: str, 
    timeout: int, 
    template_name: Optional[str] = None, 
    stdin_input: Optional[str] = None, 
    extra_flags: Optional[List[str]] = None, 
    custom_compiler: Optional[str] = None, 
    base_flags: Optional[List[str]] = None,
    log_file: Optional[str] = None,
    validar_ub: bool = False,
) -> Dict[str, Any]:
    """Compila y ejecuta un string de código C de forma segura usando tempfile y flags configurables.

    Con `validar_ub` se compila con UBSan en modo trampa y una variante con comportamiento
    indefinido devuelve el estado `undefined_behavior` (QoL #546). Si el compilador no admite esas
    banderas, se compila sin ellas y el resultado lo dice en `ub_verificado`.
    """
    if validar_ub:
        resultado = compile_and_run_c(code, timeout, template_name, stdin_input,
                                      list(extra_flags or []) + FLAGS_UB, custom_compiler, base_flags, log_file=os.devnull)
        if resultado["status"] != "compile_error":
            if resultado["status"] == "runtime_error" and resultado.get("returncode") in _SENALES_UB:
                return {"status": "undefined_behavior", "ub_verificado": True,
                        "output": "La variante tiene comportamiento indefinido (UBSan)."}
            return {**resultado, "ub_verificado": True}
        # Sin soporte para UBSan (o el código no compila): la compilación normal decide y registra.
        resultado = compile_and_run_c(code, timeout, template_name, stdin_input, extra_flags,
                                      custom_compiler, base_flags, log_file)
        return {**resultado, "ub_verificado": False}

    compiler = custom_compiler or CONFIG.get("compiler", "gcc")
    flags: List[str] = list(base_flags) if base_flags is not None else list(CONFIG.get("compiler_flags", ["-Wall", "-Wextra"]))
    if extra_flags:
        for f in extra_flags:
            if f not in flags:
                flags.append(f)

    with tempfile.TemporaryDirectory(prefix="idkfa_build_") as tmp_dir:
        src_path = os.path.join(tmp_dir, "source.c")
        exe_path = os.path.join(tmp_dir, "prog.out")

        with open(src_path, "w", encoding='utf-8') as src_file:
            src_file.write(code)

        try:
            daedalus_res = None
            if custom_compiler is None or custom_compiler == "gcc":
                daedalus_res = _try_daedalus_compile(src_path, exe_path, flags, timeout)

            if daedalus_res is not None:
                if not daedalus_res.exito:
                    target_log = log_file or CONFIG.get("compilation_error_log")
                    if target_log:
                        with open(target_log, "a", encoding='utf-8') as log:
                            log.write(f"--- COMPILE ERROR [{datetime.datetime.now()}] ---\n")
                            if template_name:
                                log.write(f"Template: {template_name}\n")
                            log.write(f"Command: daedalus {' '.join(flags)} {src_path} -o {exe_path}\n")
                            log.write(f"Stderr:\n{daedalus_res.stderr_crudo}\n")
                            log.write(f"Source Code:\n{code}\n")
                            log.write("-" * 40 + "\n\n")
                    return {"status": "compile_error", "output": "Se produce un error de compilación."}
            else:
                cmd = [compiler] + flags + [src_path, "-o", exe_path]
                compile_process = subprocess.run(
                    cmd,
                    capture_output=True, text=True, timeout=timeout, encoding='utf-8'
                )
                if compile_process.returncode != 0:
                    target_log = log_file or CONFIG.get("compilation_error_log")
                    if target_log:
                        with open(target_log, "a", encoding='utf-8') as log:
                            log.write(f"--- COMPILE ERROR [{datetime.datetime.now()}] ---\n")
                            if template_name:
                                log.write(f"Template: {template_name}\n")
                            log.write(f"Command: {' '.join(cmd)}\n")
                            log.write(f"Stderr:\n{compile_process.stderr}\n")
                            log.write(f"Source Code:\n{code}\n")
                            log.write("-" * 40 + "\n\n")
                    return {"status": "compile_error", "output": "Se produce un error de compilación."}

            try:
                run_process = subprocess.run(
                    [exe_path],
                    input=stdin_input,
                    capture_output=True, text=True, timeout=timeout, encoding='utf-8'
                )
                if run_process.returncode != 0:
                    return {"status": "runtime_error", "returncode": run_process.returncode,
                            "output": "Se produce un error en tiempo de ejecución."}
                
                return {"status": "success", "output": run_process.stdout.strip()}

            except subprocess.TimeoutExpired:
                return {"status": "timeout", "output": "El programa excede el tiempo límite de ejecución."}

        except Exception as e:
            return {"status": "error", "output": str(e)}
