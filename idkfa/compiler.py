"""Módulo para la compilación y ejecución segura de código C."""

import os
import subprocess
import datetime
import tempfile
from typing import Dict, List, Optional, Any
from idkfa.config import CONFIG

def compile_and_run_c(
    code: str, 
    timeout: int, 
    template_name: Optional[str] = None, 
    stdin_input: Optional[str] = None, 
    extra_flags: Optional[List[str]] = None, 
    custom_compiler: Optional[str] = None, 
    base_flags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Compila y ejecuta un string de código C de forma segura usando tempfile y flags configurables."""
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
            cmd = [compiler] + flags + [src_path, "-o", exe_path]
            compile_process = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=timeout, encoding='utf-8'
            )
            if compile_process.returncode != 0:
                log_file = CONFIG.get("compilation_error_log")
                if log_file:
                    with open(log_file, "a", encoding='utf-8') as log:
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
                    return {"status": "runtime_error", "output": "Se produce un error en tiempo de ejecución."}
                
                return {"status": "success", "output": run_process.stdout.strip()}

            except subprocess.TimeoutExpired:
                return {"status": "timeout", "output": "El programa excede el tiempo límite de ejecución."}

        except Exception as e:
            return {"status": "error", "output": str(e)}
