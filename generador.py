#!/usr/bin/env python3
"""Punto de entrada CLI para generador idkfa."""

import os
import re
import argparse
import sys
import io
import datetime
from xml.etree.ElementTree import Element, ElementTree, indent
from typing import List, Tuple, Any

from idkfa.config import CONFIG, AppConfig
from idkfa.parser import parse_c_template, TemplateInfo
from idkfa.compiler import compile_and_run_c
from idkfa.variables import (
    generate_vars,
    generate_all_variants_deterministically,
    generate_incorrect_answers,
    generate_stdin,
    normalize_answer_repr,
)
from idkfa.moodle_xml import (
    CDATA,
    evaluate_feedback,
    create_moodle_question_xml,
    create_category_xml,
)

def process_single_template(root: Element, filepath: str, args: argparse.Namespace) -> None:
    """Procesa un archivo .c individual y genera las preguntas en el XML."""
    filename = os.path.basename(filepath)
    
    # Crear categoría para este archivo individual
    moodle_category_path = f"$course$/top/{args.category}"
    create_category_xml(root, moodle_category_path)
    print(f"\n📁 Creando categoría: {moodle_category_path}")
    print(f"  📄 Procesando plantilla: {filename}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Purgar comentarios de documentación interna
    content = re.sub(r'^\s*//\s*#.*$\n?', '', content, flags=re.MULTILINE)

    template_info = parse_c_template(content)
    if template_info.get("status") == "error":
        log_file = CONFIG.get("parsing_error_log")
        if log_file:
            with open(log_file, "a", encoding='utf-8') as log:
                log.write(f"--- PARSE ERROR [{datetime.datetime.now()}] ---\n")
                log.write(f"File: {filename}\n")
                log.write(f"Reason: {template_info.get('reason')}\n")
                log.write("-" * 40 + "\n\n")
        print(f"  [!] No se pudo procesar {filename}. Razón: {template_info.get('reason')}", file=sys.stderr)
        return
    
    # Obtener variantes deterministas
    variants = generate_all_variants_deterministically(template_info['var_defs'], args.num)
    generated_count = 0

    base_flags: List[str] = [f.strip() for f in args.cflags.split()] if getattr(args, "cflags", None) else CONFIG.get("compiler_flags", ["-Wall", "-Wextra"])
    custom_compiler: str = getattr(args, "compiler", None) or CONFIG.get("compiler", "gcc")

    for variables in variants:
        code_instance = template_info['code_template']
        for name, value in variables.items():
            code_instance = code_instance.replace(f"__{name}__", str(value))

        # Generar STDIN si existe en la plantilla
        stdin_input = None
        if template_info.get('stdin_template'):
            stdin_input = generate_stdin(template_info['stdin_template'], variables)

        # Determinar la respuesta correcta: evaluar expresión, usar fija, o compilar.
        if template_info.get("correct_answer_expression"):
            try:
                expr = template_info["correct_answer_expression"]
                for name, value in variables.items():
                    expr = expr.replace(f"__{name}__", str(value))
                correct_answer = str(eval(expr))
            except Exception as e:
                print(f"  [!] Error evaluando expresión de respuesta correcta: {e}", file=sys.stderr)
                continue
        elif template_info.get("fixed_correct_answer"):
            correct_answer = template_info["fixed_correct_answer"]
        else:
            result = compile_and_run_c(
                code_instance, 
                CONFIG["execution_timeout"], 
                template_name=filename, 
                stdin_input=stdin_input,
                extra_flags=template_info.get("custom_flags"),
                custom_compiler=custom_compiler,
                base_flags=base_flags
            )
            if not result:
                continue
            correct_answer = result['output']
        
        # Generar opciones incorrectas y crear el XML
        min_distractors = getattr(args, 'min_distractors', None) or CONFIG.get("min_distractors", 3)
        incorrect_answers = generate_incorrect_answers(
            correct_answer, 
            template_info['predefined_options'], 
            template_info['distractor_expressions'],
            variables,
            count=min_distractors
        )
        
        # Validar mínimo de distractores para multichoice
        if template_info.get("question_type", "multichoice") == "multichoice" and len(incorrect_answers) < min_distractors:
            print(f"    [!] Advertencia: Solo se obtuvieron {len(incorrect_answers)}/{min_distractors} distractores para '{filename}'.", file=sys.stderr)

        # Crear una copia del código para visualización con sustituciones
        display_code_instance = code_instance
        substitutions = CONFIG.get("substitutions", {})
        for old, new in substitutions.items():
            display_code_instance = display_code_instance.replace(old, new)

        create_moodle_question_xml(root, template_info, display_code_instance, correct_answer, incorrect_answers, generated_count + 1, stdin_content=stdin_input, variables=variables, args=args)
        generated_count += 1
        print(f"    -> Generada pregunta #{generated_count} (Respuesta: '{correct_answer}')")

    if generated_count < args.num:
        print(f"    [!] Advertencia: Solo se generaron {generated_count}/{args.num} preguntas únicas.", file=sys.stderr)

def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de Cuestionarios Moodle XML (validado por XSD) desde plantillas C.")
    parser.add_argument("-s", "--source", default=CONFIG["source_directory"], help="Directorio con las plantillas .c o archivo .c individual")
    parser.add_argument("-o", "--output", default=CONFIG["output_file"], help="Archivo XML de salida")
    parser.add_argument("-n", "--num", type=int, default=CONFIG["questions_per_template"], help="Número de preguntas a generar por plantilla")
    parser.add_argument("-c", "--category", default=CONFIG["moodle_base_category"], help="Categoría base en Moodle")
    parser.add_argument("-g", "--generate-only", action="store_true", help="Solo generar código C en el directorio 'generated' sin crear XML")
    parser.add_argument("-t", "--template", help="Procesar solo este archivo .c específico (ruta completa o relativa)")
    parser.add_argument("--penalty", default=None, help="Penalización por defecto para respuestas incorrectas (ej: 0.25)")
    parser.add_argument("--defaultgrade", default=None, help="Calificación por defecto de las preguntas (ej: 1.0)")
    parser.add_argument("--min-distractors", type=int, default=CONFIG["min_distractors"], help="Mínimo de distractores para preguntas de opción múltiple")
    parser.add_argument("--compiler", default=None, help="Compilador C a utilizar (por defecto: gcc)")
    parser.add_argument("--cflags", default=None, help="Flags de compilación C adicionales o globales (ej: '-Wall -Wextra -O2')")
    parser.add_argument("--config", default=None, help="Ruta a archivo de configuración JSON personalizada")
    args = parser.parse_args()

    # Cargar configuración si se pasa archivo
    if args.config:
        cfg = AppConfig.load_from_file(args.config)
        CONFIG.update(cfg.to_dict())

    # Si se especifica --generate-only, solo generamos código C
    if args.generate_only:
        generate_c_code_only(args)
        return

    root = Element("quiz")
    
    # Determinar si estamos procesando un archivo individual o un directorio
    if args.template:
        if not os.path.isfile(args.template):
            print(f"Error: El archivo '{args.template}' no existe.", file=sys.stderr)
            sys.exit(1)
        if not args.template.endswith('.c'):
            print(f"Error: El archivo '{args.template}' no es un archivo .c", file=sys.stderr)
            sys.exit(1)
        
        print(f"Procesando plantilla individual: '{args.template}'...")
        process_single_template(root, args.template, args)
        processed_files = 1
    else:
        if not os.path.isdir(args.source):
            print(f"Error: El directorio '{args.source}' no existe.", file=sys.stderr)
            sys.exit(1)
        
        print(f"Buscando plantillas en: '{args.source}'...")
        processed_files = 0

        base_flags = [f.strip() for f in args.cflags.split()] if getattr(args, "cflags", None) else CONFIG.get("compiler_flags", ["-Wall", "-Wextra"])
        custom_compiler = getattr(args, "compiler", None) or CONFIG.get("compiler", "gcc")

        for dirpath, _, filenames in os.walk(args.source):
            if not any(fname.endswith('.c') for fname in filenames):
                continue

            relative_path = os.path.relpath(dirpath, args.source)
            moodle_category_path = f"$course$/top/{args.category}"
            if relative_path != ".":
                moodle_category_path += f"/{relative_path.replace(os.sep, '/')}"
            
            create_category_xml(root, moodle_category_path)
            print(f"\n📁 Creando categoría: {moodle_category_path}")

            for filename in filenames:
                if filename.endswith(".c"):
                    processed_files += 1
                    filepath = os.path.join(dirpath, filename)
                    print(f"  📄 Procesando plantilla: {filename}")

                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    content = re.sub(r'^\s*//\s*#.*$\n?', '', content, flags=re.MULTILINE)

                    template_info = parse_c_template(content)
                    if template_info.get("status") == "error":
                        log_file = CONFIG.get("parsing_error_log")
                        if log_file:
                            with open(log_file, "a", encoding='utf-8') as log:
                                log.write(f"--- PARSE ERROR [{datetime.datetime.now()}] ---\n")
                                log.write(f"File: {filename}\n")
                                log.write(f"Reason: {template_info.get('reason')}\n")
                                log.write("-" * 40 + "\n\n")
                        print(f"  [!] No se pudo procesar {filename}. Saltando. Razón: {template_info.get('reason')}", file=sys.stderr)
                        continue
                    
                    variants = generate_all_variants_deterministically(template_info['var_defs'], args.num)
                    generated_count = 0

                    for variables in variants:
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
                                print(f"  [!] Error evaluando expresión de respuesta correcta: {e}", file=sys.stderr)
                                continue
                        elif template_info.get("fixed_correct_answer"):
                            correct_answer = template_info["fixed_correct_answer"]
                        else:
                            result = compile_and_run_c(
                                code_instance, 
                                CONFIG["execution_timeout"], 
                                template_name=filename, 
                                stdin_input=stdin_input,
                                extra_flags=template_info.get("custom_flags"),
                                custom_compiler=custom_compiler,
                                base_flags=base_flags
                            )
                            if not result:
                                continue
                            correct_answer = result['output']
                        
                        min_distractors = getattr(args, 'min_distractors', None) or CONFIG.get("min_distractors", 3)
                        incorrect_answers = generate_incorrect_answers(
                            correct_answer, 
                            template_info['predefined_options'], 
                            template_info['distractor_expressions'],
                            variables,
                            count=min_distractors
                        )
                        
                        if template_info.get("question_type", "multichoice") == "multichoice" and len(incorrect_answers) < min_distractors:
                            print(f"    [!] Advertencia: Solo se obtuvieron {len(incorrect_answers)}/{min_distractors} distractores para '{filename}'.", file=sys.stderr)

                        display_code_instance = code_instance
                        substitutions = CONFIG.get("substitutions", {})
                        for old, new in substitutions.items():
                            display_code_instance = display_code_instance.replace(old, new)

                        create_moodle_question_xml(root, template_info, display_code_instance, correct_answer, incorrect_answers, generated_count + 1, stdin_content=stdin_input, variables=variables, args=args)
                        generated_count += 1
                        print(f"    -> Generada pregunta #{generated_count} (Respuesta: '{correct_answer}')")

                    if generated_count < args.num:
                         print(f"    [!] Advertencia: Solo se generaron {generated_count}/{args.num} preguntas únicas.", file=sys.stderr)

    if processed_files > 0:
        indent(root)
        tree = ElementTree(root)
        
        string_buffer = io.StringIO()
        tree.write(string_buffer, encoding="unicode", xml_declaration=True)
        xml_string = string_buffer.getvalue()
        
        xml_string = xml_string.replace("&lt;![CDATA[", "<![CDATA[")
        xml_string = xml_string.replace("]]&gt;", "]]>")
        
        xml_string = xml_string.replace("&amp;", "&")
        xml_string = xml_string.replace("&lt;", "<")
        xml_string = xml_string.replace("&gt;", ">")

        xml_string = xml_string.replace("<text><![CDATA[]]></text>", "<text></text>")

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(xml_string)
            
        print(f"\n✅ Proceso completado. Se ha creado el archivo '{args.output}'.")
    else:
        print("\n[!] No se encontraron archivos .c en el directorio de origen.")

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

if __name__ == "__main__":
    main()
