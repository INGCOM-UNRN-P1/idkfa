#!/usr/bin/env python3
"""Punto de entrada CLI con soporte de ejecución paralela, barra de progreso, dry-run y reporte estadístico."""

import os
import re
import argparse
import sys
import io
import time
import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from xml.etree.ElementTree import Element, ElementTree, indent
from typing import List, Tuple, Any, Dict, Optional

from idkfa.config import CONFIG, AppConfig
from idkfa.parser import parse_c_template, TemplateInfo
from idkfa.compiler import compile_and_run_c
from idkfa.variables import (
    generate_vars,
    generate_all_variants_deterministically,
    generate_incorrect_answers,
    generate_stdin,
    normalize_answer_repr,
    adapt_grammar_and_pluralization,
    is_mathematically_trivial,
    DistractorOption
)
from idkfa.moodle_xml import (
    CDATA,
    evaluate_feedback,
    create_moodle_question_xml,
    create_category_xml,
)

def print_progress_bar(iteration: int, total: int, prefix: str = '', suffix: str = '', length: int = 40) -> None:
    """Imprime una barra de progreso visual en la terminal."""
    if total <= 0:
        return
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n')

def process_template_data(filepath: str, args_dict: Dict[str, Any], config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Función de procesamiento aislada ejecutable en paralelo para una plantilla C."""
    filename = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(r'^\s*//\s*#.*$\n?', '', content, flags=re.MULTILINE)
    template_info = parse_c_template(content)
    
    log_file_path = args_dict.get("log_file") or f"{os.path.splitext(args_dict.get('output', 'cuestionario_moodle.xml'))[0]}.log"

    if template_info.get("status") == "error":
        if log_file_path:
            with open(log_file_path, "a", encoding='utf-8') as log:
                log.write(f"--- PARSE ERROR [{datetime.datetime.now()}] ---\n")
                log.write(f"File: {filename}\n")
                log.write(f"Reason: {template_info.get('reason')}\n")
                log.write("-" * 40 + "\n\n")
        return {
            "status": "error",
            "filepath": filepath,
            "filename": filename,
            "reason": template_info.get("reason"),
            "questions": []
        }

    variants = generate_all_variants_deterministically(template_info['var_defs'], args_dict.get("num", 5))
    generated_questions: List[Dict[str, Any]] = []

    base_flags: List[str] = [f.strip() for f in args_dict["cflags"].split()] if args_dict.get("cflags") else config_dict.get("compiler_flags", ["-Wall", "-Wextra"])
    custom_compiler: str = args_dict.get("compiler") or config_dict.get("compiler", "gcc")

    for idx, variables in enumerate(variants):
        code_instance = template_info['code_template']
        for name, value in variables.items():
            code_instance = code_instance.replace(f"__{name}__", str(value))

        stdin_input = None
        if template_info.get('stdin_template'):
            stdin_input = generate_stdin(template_info['stdin_template'], variables)

        if template_info.get("correct_answer_expression"):
            try:
                expr = template_info["correct_answer_expression"]
                for name, value in variables.items():
                    expr = expr.replace(f"__{name}__", str(value))
                correct_answer = str(eval(expr))
            except Exception as e:
                continue
        elif template_info.get("fixed_correct_answer"):
            correct_answer = template_info["fixed_correct_answer"]
        else:
            result = compile_and_run_c(
                code_instance, 
                config_dict.get("execution_timeout", 3), 
                template_name=filepath, 
                stdin_input=stdin_input,
                extra_flags=template_info.get("custom_flags"),
                custom_compiler=custom_compiler,
                base_flags=base_flags,
                log_file=log_file_path
            )
            if not result or result.get("status") != "success":
                continue
            correct_answer = result['output']

        min_distractors = args_dict.get("min_distractors") or config_dict.get("min_distractors", 3)
        dist_exprs = template_info.get("distractor_defs") or template_info.get("distractor_expressions", [])
        incorrect_answers = generate_incorrect_answers(
            correct_answer, 
            template_info['predefined_options'], 
            dist_exprs,
            variables,
            count=min_distractors,
            template_name=filepath
        )

        display_code_instance = code_instance
        substitutions = config_dict.get("substitutions", {})
        for old, new in substitutions.items():
            display_code_instance = display_code_instance.replace(old, new)

        generated_questions.append({
            "template_info": template_info,
            "display_code_instance": display_code_instance,
            "correct_answer": correct_answer,
            "incorrect_answers": incorrect_answers,
            "stdin_content": stdin_input,
            "variables": variables,
            "question_number": len(generated_questions) + 1
        })

    return {
        "status": "success",
        "filepath": filepath,
        "filename": filename,
        "template_info": template_info,
        "questions": generated_questions
    }

def generate_c_code_only(args: argparse.Namespace) -> None:
    """Genera solo el código C de las plantillas en el directorio 'generated'."""
    generated_dir = "generated"
    if os.path.exists(generated_dir):
        import shutil
        shutil.rmtree(generated_dir)
    os.makedirs(generated_dir)
    
    makefile_targets: List[Tuple[str, str]] = []
    all_executables: List[str] = []
    
    print(f"🚀 Generando código C en directorio '{generated_dir}'...")
    
    if args.template:
        if not os.path.isfile(args.template):
            print(f"Error: El archivo '{args.template}' no existe.", file=sys.stderr)
            return
        if not args.template.endswith('.c'):
            print(f"Error: El archivo '{args.template}' no es un archivo .c", file=sys.stderr)
            return
        
        files_to_process = [(args.template, os.path.dirname(args.template) or ".")]
    else:
        files_to_process = []
        for dirpath, dirnames, filenames in os.walk(args.source):
            for filename in filenames:
                if filename.endswith(".c"):
                    filepath = os.path.join(dirpath, filename)
                    files_to_process.append((filepath, dirpath))
    
    for filepath, dirpath in files_to_process:
        filename = os.path.basename(filepath)
        print(f"\n📄 Procesando plantilla: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(r'^\s*//\s*#.*$\n?', '', content, flags=re.MULTILINE)
        
        template_info = parse_c_template(content)
        if template_info.get("status") == "error":
            print(f"  [!] No se pudo procesar {filename}. Razón: {template_info.get('reason')}", file=sys.stderr)
            continue
        
        base_name = os.path.splitext(filename)[0]
        if args.template:
            output_subdir = os.path.join(generated_dir, base_name)
        else:
            relative_path = os.path.relpath(dirpath, args.source)
            if relative_path != ".":
                output_subdir = os.path.join(generated_dir, relative_path, base_name)
            else:
                output_subdir = os.path.join(generated_dir, base_name)
        
        os.makedirs(output_subdir, exist_ok=True)
        
        variants = generate_all_variants_deterministically(template_info['var_defs'], args.num)
        generated_count = 0
        
        for variables in variants:
            code_instance = template_info['code_template']
            for name, value in variables.items():
                code_instance = code_instance.replace(f"__{name}__", str(value))
            
            variant_filename = f"{base_name}_v{generated_count + 1}.c"
            variant_path = os.path.join(output_subdir, variant_filename)
            
            with open(variant_path, 'w', encoding='utf-8') as f:
                f.write(code_instance)
            
            relative_variant_path = os.path.relpath(variant_path, generated_dir)
            executable_name = os.path.splitext(relative_variant_path)[0]
            makefile_targets.append((relative_variant_path, executable_name))
            all_executables.append(executable_name)
            
            generated_count += 1
            print(f"    -> Generada variante {variant_filename}")
        
        if generated_count < args.num:
            print(f"    [!] Advertencia: Solo se generaron {generated_count}/{args.num} variantes únicas.", file=sys.stderr)
    
    makefile_path = os.path.join(generated_dir, "Makefile")
    base_flags = [f.strip() for f in args.cflags.split()] if getattr(args, "cflags", None) else CONFIG.get("compiler_flags", ["-Wall", "-Wextra"])
    cflags_str = " ".join(base_flags)
    compiler_cmd = getattr(args, "compiler", None) or CONFIG.get("compiler", "gcc")

    with open(makefile_path, 'w', encoding='utf-8') as f:
        f.write("# Makefile generado automáticamente\n")
        f.write(f"CC = {compiler_cmd}\n")
        f.write(f"CFLAGS = {cflags_str}\n\n")
        
        f.write(f"all: {' '.join(all_executables)}\n\n")
        
        for source, executable in makefile_targets:
            f.write(f"{executable}: {source}\n")
            f.write(f"\t$(CC) $(CFLAGS) -o $@ $<\n\n")
        
        f.write("clean:\n")
        f.write(f"\trm -f {' '.join(all_executables)}\n\n")
        
        f.write(".PHONY: all clean\n")
    
    print(f"\n✅ Generación completada.")
    print(f"   📁 Directorio: {generated_dir}")
    print(f"   📝 Makefile creado: {makefile_path}")
    print(f"   🔨 Para compilar: cd {generated_dir} && make")

def main(args: list[str] | None = None) -> None:
    import typer
    from idkfa.cli import app
    from typer._click.exceptions import Exit as ClickExit
    try:
        app(args=args, standalone_mode=False)
    except (SystemExit, ClickExit, typer.Exit) as e:
        code = getattr(e, "code", getattr(e, "exit_code", 0))
        if code != 0:
            sys.exit(code)





if __name__ == "__main__":
    from idkfa.cli import app
    app()


