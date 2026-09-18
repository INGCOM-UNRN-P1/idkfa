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


def _emitir_json_generacion(
    procesadas: int,
    exitosas: int,
    fallidas: int,
    preguntas: int,
    archivo_salida: Optional[str],
    dry_run: bool,
    errores: List[Dict[str, str]],
    segundos: float,
) -> None:
    import json

    print(json.dumps({
        "schema_version": "1.0.0",
        "ok": fallidas == 0,
        "dry_run": dry_run,
        "plantillas_procesadas": procesadas,
        "plantillas_exitosas": exitosas,
        "plantillas_fallidas": fallidas,
        "preguntas_generadas": preguntas,
        "archivo_salida": archivo_salida,
        "errores": errores,
        "tiempo_segundos": round(segundos, 3),
    }, indent=2, ensure_ascii=False))


def _generate_c_code_only(args: CliArgs) -> None:
    from generador import generate_c_code_only
    generate_c_code_only(args)


def _process_template_data(filepath: str, args_dict: Dict[str, Any], config_dict: Dict[str, Any]) -> Dict[str, Any]:
    from generador import process_template_data
    return process_template_data(filepath, args_dict, config_dict)


@app.callback(invoke_without_command=True)
def main_cmd(
    ctx: typer.Context,
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
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emitir el resultado de la generación como JSON en stdout (el progreso y los avisos van a stderr).",
    ),
) -> None:
    """Genera cuestionarios XML para Moodle a partir de plantillas C ejecutadas y verificadas."""
    if ctx.invoked_subcommand is not None:
        return

    if json_output and generate_only:
        err_console.print("[bold red]Error:[/bold red] --json no se puede combinar con --generate-only.")
        sys.exit(2)
    # Con --json la salida humana se desvía a stderr: stdout queda como JSON puro.
    salida = err_console if json_output else console

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
        salida.print("[yellow][!] No se encontraron archivos .c para procesar.[/yellow]")
        if json_output:
            _emitir_json_generacion(0, 0, 0, 0, None, dry_run, [], 0.0)
        return

    salida.print(f"🚀 Procesando {len(files_to_process)} plantilla(s) con {jobs} worker(s)...")
    if dry_run:
        salida.print("[cyan]🔍 MODO VALIDACIÓN / DRY-RUN ACTIVO (no se escribirá archivo XML).[/cyan]")

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
                if not json_output:
                    _print_progress_bar(i, len(files_to_process), prefix="Progreso:", suffix=f"({i}/{len(files_to_process)})")
    else:
        for i, (fpath, _) in enumerate(files_to_process, 1):
            res = _process_template_data(fpath, args_dict, CONFIG)
            results.append(res)
            if not json_output:
                _print_progress_bar(i, len(files_to_process), prefix="Progreso:", suffix=f"({i}/{len(files_to_process)})")

    successful_templates = 0
    failed_templates = 0
    total_questions_generated = 0
    errores: List[Dict[str, str]] = []

    root = Element("quiz")
    current_category: Optional[str] = None

    for res in results:
        if res["status"] == "error":
            failed_templates += 1
            errores.append({"plantilla": str(res["filepath"]), "razon": str(res["reason"])})
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

    escribio_xml = not dry_run and successful_templates > 0
    if json_output:
        _emitir_json_generacion(
            len(files_to_process), successful_templates, failed_templates, total_questions_generated,
            output_str if escribio_xml else None, dry_run, errores, elapsed_time,
        )
    else:
        console.print("\n" + "=" * 55)
        console.print(" 📊 REPORTE DE EJECUCIÓN")
        console.print("=" * 55)
        console.print(f" • Plantillas procesadas:   {len(files_to_process)}")
        console.print(f" • Plantillas exitosas:     {successful_templates}")
        console.print(f" • Plantillas fallidas:     {failed_templates}")
        console.print(f" • Preguntas generadas:     {total_questions_generated}")
        console.print(f" • Tiempo total:            {elapsed_time:.2f}s")
        if escribio_xml:
            console.print(f" • Archivo de salida:       {output_str}")
        console.print("=" * 55 + "\n")

    if failed_templates > 0:
        raise typer.Exit(1)


@app.command("spellcheck")
@app.command("grammar")
@app.command("languagetool")
def cmd_spellcheck(
    paths: Optional[List[Path]] = typer.Argument(
        None,
        help="Plantillas .c, archivos .xml o directorios a revisar con LanguageTool.",
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="URL del servidor LanguageTool (por defecto http://localhost:8081 y API pública).",
    ),
    username: Optional[str] = typer.Option(
        None,
        "--username",
        "-u",
        help="Usuario / correo de LanguageTool Premium.",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="API Key / Token de LanguageTool Premium.",
    ),
    premium: bool = typer.Option(
        False,
        "--premium",
        help="Fuerza el uso de la API LanguageTool Premium.",
    ),
    lang: str = typer.Option(
        "es-AR",
        "--lang",
        "-l",
        help="Código de idioma para LanguageTool (ej: 'es-AR', 'es', 'en-US').",
    ),
    ignore_rules: Optional[str] = typer.Option(
        None,
        "--ignore-rules",
        help="Reglas a ignorar separadas por comas.",
    ),
    ignore_words: Optional[str] = typer.Option(
        None,
        "--ignore-words",
        help="Palabras personalizadas a ignorar separadas por comas.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emite salida estructurada en formato JSON.",
    ),
    output_md: Optional[Path] = typer.Option(
        None,
        "--md",
        "--output-md",
        "-o",
        help="Genera reporte en formato Markdown.",
    ),
) -> None:
    """Verifica ortografía y gramática en plantillas de C y cuestionarios generados usando LanguageTool."""
    import json
    from rich.table import Table
    from rich.panel import Panel
    from idkfa.languagetool_checker import (
        analizar_archivo_languagetool,
        generar_reporte_markdown_languagetool,
    )

    archivos_a_revisar = []
    if paths:
        for p in paths:
            if p.is_file() and p.suffix.lower() in (".c", ".xml"):
                archivos_a_revisar.append(p)
            elif p.is_dir():
                archivos_a_revisar.extend(sorted(p.glob("**/*.c")))
                archivos_a_revisar.extend(sorted(p.glob("**/*.xml")))
    else:
        src = Path("templates")
        if src.is_dir():
            archivos_a_revisar.extend(sorted(src.glob("**/*.c")))

    if not archivos_a_revisar:
        console.print("[yellow]No se encontraron archivos (.c / .xml) para auditar con LanguageTool.[/yellow]")
        raise typer.Exit(code=0)

    reglas_ign = set(r.strip() for r in ignore_rules.split(",") if r.strip()) if ignore_rules else None
    palabras_ign = set(w.strip() for w in ignore_words.split(",") if w.strip()) if ignore_words else None

    todos_los_issues = []
    for arch in archivos_a_revisar:
        issues = analizar_archivo_languagetool(
            arch,
            lang=lang,
            server_url=server,
            username=username,
            api_key=api_key,
            premium=premium,
            ignore_words=palabras_ign,
            ignore_rules=reglas_ign,
        )
        todos_los_issues.extend(issues)

    if output_md:
        md_text = generar_reporte_markdown_languagetool(todos_los_issues)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(md_text, encoding="utf-8")
        console.print(f"[bold green]✓ Reporte Markdown generado en:[/bold green] [cyan]{output_md}[/cyan]")
        raise typer.Exit(code=0 if not todos_los_issues else 1)

    if json_output:
        res = {
            "total_archivos": len(archivos_a_revisar),
            "total_issues": len(todos_los_issues),
            "issues": [i.to_dict() for i in todos_los_issues],
        }
        print(json.dumps({"schema_version": "1.0.0", **res}, indent=2, ensure_ascii=False))
        raise typer.Exit(code=0 if not todos_los_issues else 1)

    if not todos_los_issues:
        console.print(Panel(
            f"[bold green]✓ Plantillas y Preguntas Impecables[/bold green]\n"
            f"Se analizaron {len(archivos_a_revisar)} archivos sin observaciones ortográficas.",
            title="[bold green]LanguageTool Passed[/bold green]",
            border_style="green",
        ))
        raise typer.Exit(code=0)

    tabla = Table(title=f"⚠️ Observaciones de LanguageTool ({len(todos_los_issues)} encontradas)", border_style="yellow")
    tabla.add_column("Archivo", style="bold cyan")
    tabla.add_column("L:C", justify="center")
    tabla.add_column("Error / Contexto", style="white")
    tabla.add_column("Sugerencia", style="bold green")

    for iss in todos_los_issues:
        sug = ", ".join(iss.replacements[:2]) if iss.replacements else "[dim]—[/dim]"
        tabla.add_row(
            iss.file_path.name,
            f"{iss.line}:{iss.column}",
            f"[red]{iss.original_word}[/red] ({iss.context})",
            sug,
        )

    console.print(tabla)
    raise typer.Exit(code=1)


@app.command("synth-bst")
def cmd_synth_bst(
    recorrido: str = typer.Option("inorden", "--recorrido", "-r", help="Tipo de recorrido: inorden, preorden, postorden."),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Semilla pseudoaleatoria."),
    json_output: bool = typer.Option(False, "--json", help="Emite salida estructurada en formato JSON."),
) -> None:
    """Sintetiza un árbol binario de búsqueda (BST) con recorrido C compilado y validado en GCC."""
    import json
    from idkfa.procedural_synth import generar_bst_y_recorrido
    res = generar_bst_y_recorrido(tipo_recorrido=recorrido, seed=seed)
    if json_output:
        print(json.dumps({"schema_version": "1.0.0", **res}, indent=2, ensure_ascii=False))
        return
    console.print(f"[bold green]✓ BST sintetizado ({recorrido}):[/bold green]")
    console.print(f"Salida esperada: [cyan]{res['salida_esperada']}[/cyan] (GCC: {res['verificado_gcc']})")
    print(res["codigo"])


@app.command("synth-matrix")
def cmd_synth_matrix(
    filas: int = typer.Option(3, "--filas", "-f", help="Cantidad de filas."),
    cols: int = typer.Option(3, "--cols", "-c", help="Cantidad de columnas."),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Semilla pseudoaleatoria."),
    json_output: bool = typer.Option(False, "--json", help="Emite salida estructurada en formato JSON."),
) -> None:
    """Sintetiza ejercicio de matrices bidimensionales y cálculo de índices con puntero plano."""
    import json
    from idkfa.procedural_synth import generar_matriz_2d_y_puntero_plano
    res = generar_matriz_2d_y_puntero_plano(filas=filas, cols=cols, seed=seed)
    if json_output:
        print(json.dumps({"schema_version": "1.0.0", **res}, indent=2, ensure_ascii=False))
        return
    console.print(f"[bold green]✓ Matriz 2D sintetizada ({filas}x{cols}):[/bold green]")
    console.print(f"Valor objetivo: [cyan]{res['valor']}[/cyan] en [{res['f_target']}][{res['c_target']}]")
    print(res["codigo"])


@app.command("synth-linked-list")
def cmd_synth_linked_list(
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Semilla pseudoaleatoria."),
    json_output: bool = typer.Option(False, "--json", help="Emite salida estructurada en formato JSON."),
) -> None:
    """Sintetiza operaciones sobre listas enlazadas dinámicas en C validadas con GCC."""
    import json
    from idkfa.procedural_synth import generar_lista_enlazada_simple
    res = generar_lista_enlazada_simple(seed=seed)
    if json_output:
        print(json.dumps({"schema_version": "1.0.0", **res}, indent=2, ensure_ascii=False))
        return
    console.print(f"[bold green]✓ Lista enlazada sintetizada:[/bold green]")
    console.print(f"Salida esperada: [cyan]{res['salida_esperada']}[/cyan]")
    print(res["codigo"])


@app.command("synth-tf")
def cmd_synth_tf(
    tema: str = typer.Option("arrays_decay", "--tema", "-t", help="arrays_decay, sizeof_pointer, free_null, string_null_terminator."),
    json_output: bool = typer.Option(False, "--json", help="Emite salida estructurada en formato JSON."),
) -> None:
    """Genera pregunta conceptual de Verdadero/Falso con justificación técnica."""
    import json
    from idkfa.procedural_synth import generar_pregunta_verdadero_falso_con_justificacion
    res = generar_pregunta_verdadero_falso_con_justificacion(tema)
    if json_output:
        print(json.dumps({"schema_version": "1.0.0", **res}, indent=2, ensure_ascii=False))
        return
    console.print(f"[bold cyan]Enunciado:[/bold cyan] {res['enunciado']}")
    console.print(f"[bold yellow]Respuesta:[/bold yellow] {'Verdadero' if res['es_verdadero'] else 'Falso'}")
    console.print(f"[bold green]Justificación:[/bold green] {res['justificacion']}")


@app.command("export-standalone")
def cmd_export_standalone(
    archivo_c: Path = typer.Argument(..., help="Archivo C a empaquetar con autoevaluación assert()."),
    salida: Path = typer.Option(Path("standalone_autoeval.c"), "--output", "-o", help="Ruta del archivo de salida."),
) -> None:
    """Exporta snippet a formato C ejecutable independiente con asserts de autoevaluación."""
    from idkfa.procedural_synth import exportar_snippet_con_asserts
    codigo = archivo_c.read_text(encoding="utf-8")
    standalone = exportar_snippet_con_asserts(codigo, "0")
    salida.write_text(standalone, encoding="utf-8")
    console.print(f"[bold green]✓ Snippet autónomo con assert() exportado en:[/bold green] [cyan]{salida}[/cyan]")


@app.command("doctor")
def doctor_cmd(
    json_output: bool = typer.Option(False, "--json", help="Emitir diagnóstico en formato JSON estructurado."),
) -> None:
    """Verifica el estado del entorno de IDKFA (Python, GCC, Valgrind)."""
    import shutil
    from rich.table import Table
    diagnostico = []

    py_ok = sys.version_info >= (3, 10)
    diagnostico.append({
        "componente": "Python Runtime",
        "estado": "OK" if py_ok else "ERROR",
        "requerido": True,
        "detalle": f"Python {sys.version.split()[0]}",
    })

    gcc_path = shutil.which("gcc")
    diagnostico.append({
        "componente": "Compilador GCC",
        "estado": "OK" if gcc_path else "ERROR",
        "requerido": True,
        "detalle": gcc_path or "No encontrado (requerido para compilar y ejecutar plantillas C)",
    })

    valgrind_path = shutil.which("valgrind")
    diagnostico.append({
        "componente": "Valgrind",
        "estado": "OK" if valgrind_path else "ADVERTENCIA",
        "requerido": False,
        "detalle": valgrind_path or "No encontrado (opcional, para chequeo estricto de fugas de memoria)",
    })

    todo_ok = py_ok and bool(gcc_path)

    if json_output:
        import json
        payload = {
            "schema_version": "1.0.0",
            "herramienta": "idkfa",
            "ok": todo_ok,
            "componentes": diagnostico,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        raise typer.Exit(code=0 if todo_ok else 1)

    tabla = Table(title="🏥 Diagnóstico del Entorno IDKFA (doctor)", border_style="cyan")
    tabla.add_column("Componente", style="bold white")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Detalle")

    for c in diagnostico:
        color = "bold green" if c["estado"] == "OK" else ("bold yellow" if c["estado"] == "ADVERTENCIA" else "bold red")
        simbolo = "✓" if c["estado"] == "OK" else ("⚠️" if c["estado"] == "ADVERTENCIA" else "✗")
        tabla.add_row(c["componente"], f"[{color}]{simbolo} {c['estado']}[/{color}]", c["detalle"])

    console.print(tabla)
    if not todo_ok:
        console.print("\n[bold red]Instalá gcc (`sudo apt install gcc` o equivalente).[/bold red]")
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

