"""CLI de idkfa con soporte de autocompletado nativo (Typer y Rich)."""

from __future__ import annotations

import os
import sys
import time
import io
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from xml.etree.ElementTree import Element, ElementTree, indent
from concurrent.futures import ProcessPoolExecutor, as_completed

import typer
from rich.console import Console

from idkfa.config import CONFIG, AppConfig
from idkfa.parser import parse_c_template
from idkfa.variables import generate_all_variants_deterministically
from idkfa.moodle_xml import create_moodle_question_xml, create_category_xml

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="idkfa",
    help="Generador de Cuestionarios Moodle XML desde plantillas C.",
    add_completion=True,
)


class CliArgs:
    """Namespace compatible con la lógica interna de generación."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _print_progress_bar(iteration: int, total: int, prefix: str = '', suffix: str = '', length: int = 40) -> None:
    if total <= 0:
        return
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n')


def _generate_c_code_only(args: CliArgs) -> None:
    from generador import generate_c_code_only
    generate_c_code_only(args)


def _process_template_data(filepath: str, args_dict: Dict[str, Any], config_dict: Dict[str, Any]) -> Dict[str, Any]:
    from generador import process_template_data
    return process_template_data(filepath, args_dict, config_dict)


@app.command()
def main_cmd(
    source: Path = typer.Option(
        Path("templates"),
        "-s",
        "--source",
        help="Directorio con las plantillas .c o archivo .c individual.",
    ),
    template: Optional[Path] = typer.Option(
        None,
        "-t",
        "--template",
        help="Procesar solo este archivo .c específico (ruta completa o relativa).",
    ),
    output: Path = typer.Option(
        Path("cuestionario_moodle.xml"),
        "-o",
        "--output",
        help="Archivo XML de salida.",
    ),
    num: int = typer.Option(
        5,
        "-n",
        "--num",
        "--num-variants",
        help="Número de preguntas/variantes a generar por plantilla.",
    ),
    category: str = typer.Option(
        "Cuestionario C",
        "-c",
        "--category",
        help="Categoría base en Moodle.",
    ),
    generate_only: bool = typer.Option(
        False,
        "-g",
        "--generate-only",
        help="Solo generar código C en el directorio 'generated' sin crear XML.",
    ),
    dry_run: bool = typer.Option(
        False,
        "-d",
        "--dry-run",
        "--check",
        help="Modo validación rápida: verifica sintaxis y compilación sin generar XML.",
    ),
    jobs: int = typer.Option(
        1,
        "-j",
        "--jobs",
        help="Número de procesos concurrentes para compilación y generación.",
    ),
    penalty: Optional[str] = typer.Option(
        None,
        "--penalty",
        help="Penalización por defecto para respuestas incorrectas (ej: 0.25).",
    ),
    defaultgrade: Optional[str] = typer.Option(
        None,
        "--defaultgrade",
        help="Calificación por defecto de las preguntas (ej: 1.0).",
    ),
    min_distractors: int = typer.Option(
        3,
        "--min-distractors",
        help="Mínimo de distractores para preguntas de opción múltiple.",
    ),
    compiler: Optional[str] = typer.Option(
        None,
        "--compiler",
        help="Compilador C a utilizar (por defecto: gcc).",
    ),
    cflags: Optional[str] = typer.Option(
        None,
        "--cflags",
        help="Flags de compilación C adicionales o globales.",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Ruta a archivo de configuración JSON personalizada.",
    ),
    log_file: Optional[Path] = typer.Option(
        None,
        "--log-file",
        help="Ruta al archivo de log.",
    ),
) -> None:
    """Genera cuestionarios XML para Moodle a partir de plantillas C ejecutadas y verificadas."""
    source_str = str(source)
    output_str = str(output)
    template_str = str(template) if template else None
    log_file_str = str(log_file) if log_file else f"{os.path.splitext(output_str)[0]}.log"

    CONFIG["compilation_error_log"] = log_file_str
    CONFIG["parsing_error_log"] = log_file_str

    if config:
        cfg = AppConfig.load_from_file(str(config))
        CONFIG.update(cfg.to_dict())

    args_obj = CliArgs(
        source=source_str,
        output=output_str,
        num=num,
        category=category,
        generate_only=generate_only,
        template=template_str,
        penalty=penalty,
        defaultgrade=defaultgrade,
        min_distractors=min_distractors,
        compiler=compiler,
        cflags=cflags,
        config=str(config) if config else None,
        jobs=jobs,
        dry_run=dry_run,
        log_file=log_file_str,
    )

    if generate_only:
        _generate_c_code_only(args_obj)
        return

    # Recolectar archivos a procesar
    files_to_process: List[Tuple[str, str]] = []
    if template_str:
        if not os.path.isfile(template_str) or not template_str.endswith(".c"):
            err_console.print(f"[bold red]Error:[/bold red] El archivo '{template_str}' no es un archivo .c válido.")
            sys.exit(1)
        files_to_process.append((template_str, os.path.dirname(template_str) or "."))
    else:
        if not os.path.isdir(source_str):
            err_console.print(f"[bold red]Error:[/bold red] El directorio '{source_str}' no existe.")
            sys.exit(1)
        for dirpath, _, filenames in os.walk(source_str):
            for filename in sorted(filenames):
                if filename.endswith(".c"):
                    files_to_process.append((os.path.join(dirpath, filename), dirpath))

    if not files_to_process:
        console.print("[yellow][!] No se encontraron archivos .c para procesar.[/yellow]")
        return

    console.print(f"🚀 Procesando {len(files_to_process)} plantilla(s) con {jobs} worker(s)...")
    if dry_run:
        console.print("[cyan]🔍 MODO VALIDACIÓN / DRY-RUN ACTIVO (no se escribirá archivo XML).[/cyan]")

    start_time = time.time()
    args_dict = vars(args_obj)
    results: List[Dict[str, Any]] = []

    if jobs > 1 and len(files_to_process) > 1:
        with ProcessPoolExecutor(max_workers=jobs) as executor:
            future_to_file = {
                executor.submit(_process_template_data, fpath, args_dict, CONFIG): fpath
                for fpath, _ in files_to_process
            }
            for i, future in enumerate(as_completed(future_to_file), 1):
                res = future.result()
                results.append(res)
                _print_progress_bar(i, len(files_to_process), prefix="Progreso:", suffix=f"({i}/{len(files_to_process)})")
    else:
        for i, (fpath, _) in enumerate(files_to_process, 1):
            res = _process_template_data(fpath, args_dict, CONFIG)
            results.append(res)
            _print_progress_bar(i, len(files_to_process), prefix="Progreso:", suffix=f"({i}/{len(files_to_process)})")

    successful_templates = 0
    failed_templates = 0
    total_questions_generated = 0

    root = Element("quiz")
    current_category: Optional[str] = None

    for res in results:
        if res["status"] == "error":
            failed_templates += 1
            err_console.print(f"[red][!] No se pudo procesar '{res['filepath']}'. Razón: {res['reason']}[/red]")
        else:
            successful_templates += 1
            questions = res["questions"]
            total_questions_generated += len(questions)

            if not dry_run and questions:
                fpath = res["filepath"]
                dirpath = os.path.dirname(fpath)
                relative_path = os.path.relpath(dirpath, source_str) if not template_str else "."
                moodle_category_path = f"$course$/top/{category}"
                if relative_path != ".":
                    moodle_category_path += f"/{relative_path.replace(os.sep, '/')}"

                if moodle_category_path != current_category:
                    create_category_xml(root, moodle_category_path)
                    current_category = moodle_category_path

                for q in questions:
                    create_moodle_question_xml(
                        root,
                        q["template_info"],
                        q["display_code_instance"],
                        q["correct_answer"],
                        q["incorrect_answers"],
                        q["question_number"],
                        stdin_content=q["stdin_content"],
                        variables=q["variables"],
                        args=args_obj,
                    )

    if not dry_run and successful_templates > 0:
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

        with open(output_str, "w", encoding="utf-8") as f:
            f.write(xml_string)

    elapsed_time = time.time() - start_time

    console.print("\n" + "=" * 55)
    console.print(" 📊 REPORTE DE EJECUCIÓN")
    console.print("=" * 55)
    console.print(f" • Plantillas procesadas:   {len(files_to_process)}")
    console.print(f" • Plantillas exitosas:     {successful_templates}")
    console.print(f" • Plantillas fallidas:     {failed_templates}")
    console.print(f" • Preguntas generadas:     {total_questions_generated}")
    console.print(f" • Tiempo total:            {elapsed_time:.2f}s")
    if not dry_run and successful_templates > 0:
        console.print(f" • Archivo de salida:       {output_str}")
    console.print("=" * 55 + "\n")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
