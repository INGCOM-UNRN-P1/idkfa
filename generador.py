#!/usr/bin/env python3

import os
import re
import subprocess
import random
import argparse
import uuid
import sys
import io
import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

# --- CONFIGURACIÓN ---
CONFIG = {
    "source_directory": "templates",
    "output_file": "cuestionario_moodle.xml",
    "questions_per_template": 5,
    "moodle_base_category": "programacion1_gen_codigo",
    "compiler": "gcc",
    "execution_timeout": 3,
    "min_distractors": 3,
    "default_grade": "1.0000000",
    "default_penalty": "0.3333333",
    "compilation_error_log": "compile_errors.log",
    "parsing_error_log": "parsing_errors.log",
    "substitutions": {
    "=="   : "⩵",
    "="    : "＝",
    ";"    : ";",
    "#"    : "＃",
    "{"    : "｛",
    "}"    : "｝",
    "    " : "    ", # Espacio de 4 caracteres
    "\n"   : "↵\n",
    ">"    : "＞" ,
    "<"    : "＜",
   "["     : "［",
   "]"     : "］",
    }
}

def CDATA(text):
    """Envuelve el texto para la conversión a CDATA."""
    if str(text).strip().startswith("<![CDATA["):
        return text
    return f"<![CDATA[{text}]]>"

def parse_c_template(content):
    """
    Analiza el contenido de un archivo .c, incluyendo la sección de distractores.
    """
    try:
        lines = content.split('\n')
        
        intro_line_index = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('//'):
                intro_line_index = i
                break
        
        if intro_line_index == -1:
            return {"status": "error", "reason": "No se encontró el comentario de introducción (primera línea que empieza con //)."}

        outro_line_index = -1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('//'):
                outro_line_index = i
                break

        if outro_line_index <= intro_line_index:
            return {"status": "error", "reason": "No se encontró el comentario de cierre (segunda línea que empieza con //)."}

        intro_text = lines[intro_line_index].strip().lstrip('//').strip()
        outro_text = lines[outro_line_index].strip().lstrip('//').strip()
        code_block = '\n'.join(lines[intro_line_index+1:outro_line_index])

        cleaned_code_block = re.sub(r'#define\s+__\w+__\s+.*\n?', '', code_block)
        
        # --- Lectura robusta de secciones opcionales ---
        var_match = re.search(r"/\*var\s*(.*?)\*/", content, re.DOTALL)
        var_defs = {}
        if var_match:
            lines = var_match.group(1).strip().split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    var_defs[key.strip()] = value.strip()

        opciones_match = re.search(r"/\*opciones\s*(.*?)\*/", content, re.DOTALL)
        predefined_options = []
        if opciones_match:
            lines = opciones_match.group(1).strip().split('\n')
            predefined_options = [line.strip() for line in lines if line.strip()]

        name_match = re.search(r"/\*name\s*(.*?)\*/", content, re.DOTALL)
        question_name = name_match.group(1).strip() if name_match else "Pregunta de Código C (sin nombre)"

        distractors_match = re.search(r"/\*distractors\s*(.*?)\*/", content, re.DOTALL)
        distractor_expressions = []
        if distractors_match:
            distractor_content = distractors_match.group(1).strip()
            if distractor_content:
                lines = distractor_content.split('\n')
                for line in lines:
                    line = line.strip()
                    # Ignorar líneas vacías y comentarios de documentación (//#)
                    if line and not line.startswith('//#'):
                        # Si empieza con #, remover el # para convertirlo en expresión evaluable
                        if line.startswith('#'):
                            distractor_expressions.append(line[1:].strip())
                        elif line:
                            distractor_expressions.append(line)

        correcta_match = re.search(r"/\*correcta\s*(.*?)\*/", content, re.DOTALL)
        fixed_correct_answer = None
        correct_answer_expression = None
        if correcta_match:
            correcta_content = correcta_match.group(1).strip()
            # Eliminar comentarios de documentación interna
            lines = correcta_content.split('\n')
            clean_lines = [line for line in lines if line.strip() and not line.strip().startswith('//#')]
            
            if clean_lines:
                # Si la primera línea empieza con #, es una expresión evaluable
                if clean_lines[0].strip().startswith('#'):
                    # Remover el # y usar como expresión
                    correct_answer_expression = clean_lines[0].strip()[1:].strip()
                else:
                    # Es un valor fijo
                    fixed_correct_answer = '\n'.join(clean_lines)

        # --- Lectura de sección STDIN (opcional) ---
        stdin_match = re.search(r"/\*STDIN\s*(.*?)\*/", content, re.DOTALL)
        stdin_template = None
        if stdin_match:
            stdin_content = stdin_match.group(1).strip()
            if stdin_content:
                # Eliminar comentarios de documentación interna
                lines = stdin_content.split('\n')
                stdin_lines = [line for line in lines if line.strip() and not line.strip().startswith('//#')]
                stdin_template = '\n'.join(stdin_lines)

        # --- Lectura de sección penalty (opcional) ---
        penalty_match = re.search(r"/\*penalty\s*(.*?)\*/", content, re.DOTALL)
        penalty = penalty_match.group(1).strip() if penalty_match else None

        # --- Lectura de sección defaultgrade (opcional) ---
        grade_match = re.search(r"/\*defaultgrade\s*(.*?)\*/", content, re.DOTALL)
        default_grade = grade_match.group(1).strip() if grade_match else None

        # --- Lectura de tipo de pregunta (opcional: multichoice, shortanswer, numerical) ---
        type_match = re.search(r"/\*type\s*(.*?)\*/", content, re.DOTALL)
        question_type = type_match.group(1).strip().lower() if type_match else "multichoice"
        if question_type not in ["multichoice", "shortanswer", "numerical"]:
            question_type = "multichoice"

        # --- Lectura de sección feedback (opcional) ---
        feedback_match = re.search(r"/\*feedback\s*(.*?)\*/", content, re.DOTALL)
        feedback_template = None
        if feedback_match:
            fb_lines = [l for l in feedback_match.group(1).strip().split('\n') if not l.strip().startswith('//#')]
            feedback_template = '\n'.join(fb_lines).strip()

        return {
            "status": "success",
            "question_text_template": f"{intro_text}\n```c\n{{code}}\n```\n{outro_text}",
            "code_template": cleaned_code_block,
            "var_defs": var_defs,
            "predefined_options": predefined_options,
            "distractor_expressions": distractor_expressions,
            "name": question_name,
            "fixed_correct_answer": fixed_correct_answer,
            "correct_answer_expression": correct_answer_expression,
            "stdin_template": stdin_template,
            "penalty": penalty,
            "default_grade": default_grade,
            "question_type": question_type,
            "feedback_template": feedback_template
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def generate_vars(var_defs):
    """Genera un conjunto de valores concretos a partir de las definiciones de variables."""
    generated = {}
    for name, definition in var_defs.items():
        try:
            value_pool = eval(definition)
            generated[name] = random.choice(list(value_pool))
        except Exception as e:
            print(f"  [!] Error evaluando la definición de variable '{name}': {e}", file=sys.stderr)
            generated[name] = ""
    return generated

def generate_stdin(stdin_template, variables):
    """
    Genera el contenido de STDIN dinámicamente a partir de una plantilla y variables.
    Soporta referencias a variables usando el formato __variable__ y expresiones Python con f-string.
    """
    if not stdin_template:
        return None
    
    try:
        # Primero, reemplazar las variables en el template
        stdin_content = stdin_template
        for name, value in variables.items():
            stdin_content = stdin_content.replace(f"__{name}__", str(value))
        
        # Procesar cada línea para evaluar expresiones Python si están entre {}
        # Esto permite usar f-string-like syntax
        result_lines = []
        for line in stdin_content.split('\n'):
            # Si la línea contiene expresiones Python entre {}, evaluarlas
            if '{' in line and '}' in line:
                try:
                    # Crear un contexto con las variables disponibles
                    eval_context = variables.copy()
                    # Evaluar la línea como f-string usando eval con el contexto
                    processed_line = line.format(**eval_context)
                    result_lines.append(processed_line)
                except Exception as e:
                    # Si falla, usar la línea tal cual
                    result_lines.append(line)
            else:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    except Exception as e:
        print(f"  [!] Error generando STDIN: {e}", file=sys.stderr)
        return stdin_template

def compile_and_run_c(code, timeout, template_name=None, stdin_input=None):
    """Compila y ejecuta un string de código C, opcionalmente con entrada stdin."""
    temp_id = str(uuid.uuid4())
    source_file = f"{temp_id}.c"
    executable_file = f"{temp_id}.out"

    with open(source_file, "w", encoding='utf-8') as f:
        f.write(code)

    try:
        compile_process = subprocess.run(
            [CONFIG["compiler"], source_file, "-o", executable_file],
            capture_output=True, text=True, timeout=timeout, encoding='utf-8'
        )
        if compile_process.returncode != 0:
            log_file = CONFIG.get("compilation_error_log")
            if log_file:
                with open(log_file, "a", encoding='utf-8') as log:
                    log.write(f"--- COMPILE ERROR [{datetime.datetime.now()}] ---\n")
                    if template_name:
                        log.write(f"Template: {template_name}\n")
                    log.write(f"Stderr:\n{compile_process.stderr}\n")
                    log.write(f"Source Code:\n{code}\n")
                    log.write("-" * 40 + "\n\n")
            return {"status": "compile_error", "output": "Se produce un error de compilación."}

        try:
            run_process = subprocess.run(
                [f"./{executable_file}"],
                input=stdin_input,
                capture_output=True, text=True, timeout=timeout, encoding='utf-8'
            )
            if run_process.returncode != 0:
                return {"status": "runtime_error", "output": "Se produce un error en tiempo de ejecución."}
            
            return {"status": "success", "output": run_process.stdout.strip()}

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "output": "El programa excede el tiempo límite de ejecución."}

    finally:
        if os.path.exists(source_file):
            os.remove(source_file)
        if os.path.exists(executable_file):
            os.remove(executable_file)

def normalize_answer_repr(ans):
    """Normaliza la representación de una respuesta para comparación."""
    if ans is None:
        return ""
    ans_str = str(ans).strip()
    # Intentar normalización numérica (ej: 0.0 == 0 o "0" == 0)
    try:
        f_val = float(ans_str)
        if f_val.is_integer():
            return str(int(f_val))
        return f"{f_val:g}"
    except (ValueError, TypeError):
        return ans_str

def generate_incorrect_answers(correct_answer, predefined_options, distractor_expressions, variables, count=3):
    """Genera una lista de respuestas incorrectas, normalizando opciones y evitando duplicados."""
    norm_correct = normalize_answer_repr(correct_answer)
    seen_normalized = {norm_correct}
    
    unique_incorrect = []

    # 1. Opciones predefinidas
    for opt in predefined_options:
        opt_str = str(opt).strip()
        norm_opt = normalize_answer_repr(opt_str)
        if norm_opt and norm_opt not in seen_normalized:
            seen_normalized.add(norm_opt)
            unique_incorrect.append(opt_str)

    # 2. Expresiones de distractores
    for expr in distractor_expressions:
        temp_expr = expr
        try:
            for var_name, var_value in variables.items():
                temp_expr = temp_expr.replace(f"__{var_name}__", str(var_value))
            
            calculated_value = eval(temp_expr)
            calc_str = str(calculated_value).strip()
            norm_calc = normalize_answer_repr(calc_str)
            if norm_calc and norm_calc not in seen_normalized:
                seen_normalized.add(norm_calc)
                unique_incorrect.append(calc_str)
        except Exception as e:
            print(f"    [!] Advertencia: No se pudo calcular el distractor '{expr}': {e}", file=sys.stderr)

    # 3. Generación aleatoria de offsets numéricos si es posible
    try:
        num_correct = int(float(str(correct_answer).strip()))
        attempts = 0
        target_count = max(len(predefined_options) + len(distractor_expressions) + count, count)
        while len(unique_incorrect) < target_count and attempts < 100:
            offset = random.randint(1, 10) * random.choice([-1, 1])
            new_incorrect = str(num_correct + offset)
            norm_new = normalize_answer_repr(new_incorrect)
            if norm_new not in seen_normalized:
                seen_normalized.add(norm_new)
                unique_incorrect.append(new_incorrect)
            attempts += 1
    except (ValueError, TypeError):
        pass

    random.shuffle(unique_incorrect)
    return unique_incorrect

def evaluate_feedback(feedback_template, variables):
    """Genera el texto de retroalimentación reemplazando variables y expresiones."""
    if not feedback_template:
        return ""
    try:
        fb_content = feedback_template
        for name, value in variables.items():
            fb_content = fb_content.replace(f"__{name}__", str(value))
        
        def replace_expr(match):
            expr_str = match.group(1)
            try:
                val = eval(expr_str, {}, variables)
                return str(val)
            except Exception:
                return match.group(0)

        # Evaluar cualquier expresión entre {expr}
        fb_content = re.sub(r'\{([^}]+)\}', replace_expr, fb_content)
        return fb_content
    except Exception as e:
        print(f"  [!] Error evaluando feedback: {e}", file=sys.stderr)
        return feedback_template

def create_moodle_question_xml(parent, template_info, code_instance, correct_answer, incorrect_answers, question_number, stdin_content=None, variables=None, args=None):
    """Construye el árbol XML para una pregunta, respetando el orden del XSD."""
    question_type = template_info.get("question_type", "multichoice")
    q_node = SubElement(parent, "question", type=question_type)
    
    # El orden de los siguientes elementos es estricto para cumplir con bank.xsd
    base_name = template_info['name']
    numbered_name = f"{base_name} - {question_number}"
    SubElement(SubElement(q_node, "name"), "text").text = CDATA(numbered_name)
    
    questiontext_node = SubElement(SubElement(q_node, "questiontext", format="markdown"), "text")
    question_text_with_code = template_info['question_text_template'].replace("{code}", code_instance)
    
    # Agregar STDIN si está presente
    if stdin_content:
        stdin_section = f"\n\n#### Entrada (stdin):\n```\n{stdin_content}\n```"
        question_text_with_code += stdin_section
    
    questiontext_node.text = CDATA(question_text_with_code)

    # Feedback general dinámico
    fb_text = ""
    if template_info.get("feedback_template") and variables:
        fb_text = evaluate_feedback(template_info["feedback_template"], variables)
    SubElement(SubElement(q_node, "generalfeedback", format="markdown"), "text").text = CDATA(fb_text)

    # Configuración de defaultgrade y penalty
    default_grade = template_info.get("default_grade")
    if not default_grade:
        default_grade = getattr(args, "defaultgrade", None) or CONFIG.get("default_grade", "1.0000000")
    SubElement(q_node, "defaultgrade").text = str(default_grade)

    penalty = template_info.get("penalty")
    if not penalty:
        penalty = getattr(args, "penalty", None) or CONFIG.get("default_penalty", "0.3333333")
    SubElement(q_node, "penalty").text = str(penalty)

    SubElement(q_node, "hidden").text = "0"

    if question_type == "multichoice":
        SubElement(q_node, "single").text = "true"
        SubElement(q_node, "shuffleanswers").text = "true"
        SubElement(q_node, "answernumbering").text = "abc"
        SubElement(q_node, "showstandardinstruction").text = "0"
        SubElement(SubElement(q_node, "correctfeedback", format="markdown"), "text").text = CDATA("")
        SubElement(SubElement(q_node, "partiallycorrectfeedback", format="markdown"), "text").text = CDATA("")
        SubElement(SubElement(q_node, "incorrectfeedback", format="markdown"), "text").text = CDATA("")

        # Bloque de respuestas para multichoice
        ans_correct = SubElement(q_node, "answer", fraction="100", format="markdown")
        SubElement(ans_correct, "text").text = CDATA(f"`{correct_answer}`")
        SubElement(SubElement(ans_correct, "feedback", format="markdown"), "text").text = CDATA("")

        for ans_text in incorrect_answers:
            ans_incorrect = SubElement(q_node, "answer", fraction="0", format="markdown")
            formatted_ans_text = f"`{ans_text}`" if str(ans_text).isnumeric() or (str(ans_text).startswith('-') and str(ans_text)[1:].isnumeric()) else str(ans_text)
            SubElement(ans_incorrect, "text").text = CDATA(formatted_ans_text)
            SubElement(SubElement(ans_incorrect, "feedback", format="markdown"), "text").text = CDATA("")

    elif question_type == "shortanswer":
        SubElement(q_node, "usecase").text = "0"
        ans_correct = SubElement(q_node, "answer", fraction="100", format="markdown")
        SubElement(ans_correct, "text").text = CDATA(str(correct_answer).strip())
        SubElement(SubElement(ans_correct, "feedback", format="markdown"), "text").text = CDATA("")

    elif question_type == "numerical":
        ans_correct = SubElement(q_node, "answer", fraction="100", format="markdown")
        SubElement(ans_correct, "text").text = CDATA(str(correct_answer).strip())
        SubElement(SubElement(ans_correct, "feedback", format="markdown"), "text").text = CDATA("")
        SubElement(ans_correct, "tolerance").text = "0"

    # El elemento idnumber va al final de la secuencia según el XSD
    SubElement(q_node, "idnumber").text = ""

def create_category_xml(parent, category_path):
    """Crea el XML para una categoría, respetando el orden del XSD."""
    cat_question = SubElement(parent, "question", type="category")
    # Orden según XSD para type="category"
    category = SubElement(cat_question, "category")
    SubElement(category, "text").text = category_path
    SubElement(SubElement(cat_question, "info", format="moodle_auto_format"), "text").text = ""
    SubElement(cat_question, "idnumber").text = ""

def process_single_template(root, filepath, args):
    """
    Procesa un archivo .c individual y genera las preguntas en el XML.
    """
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
    
    generated_count = 0
    attempts = 0
    generated_variants = set()

    while generated_count < args.num and attempts < args.num * 5:
        attempts += 1
        variables = generate_vars(template_info['var_defs'])
        variant_id = tuple(sorted(variables.items()))
        if variant_id in generated_variants:
            continue

        code_instance = template_info['code_template']
        for name, value in variables.items():
            code_instance = code_instance.replace(f"__{name}__", str(value))

        # Generar STDIN si existe en la plantilla
        stdin_input = None
        if template_info.get('stdin_template'):
            stdin_input = generate_stdin(template_info['stdin_template'], variables)

        # Determinar la respuesta correcta: evaluar expresión, usar fija, o compilar.
        if template_info.get("correct_answer_expression"):
            # Evaluar la expresión con las variables actuales
            try:
                expr = template_info["correct_answer_expression"]
                # Reemplazar variables en la expresión
                for name, value in variables.items():
                    expr = expr.replace(f"__{name}__", str(value))
                correct_answer = str(eval(expr))
            except Exception as e:
                print(f"  [!] Error evaluando expresión de respuesta correcta: {e}", file=sys.stderr)
                continue
        elif template_info.get("fixed_correct_answer"):
            correct_answer = template_info["fixed_correct_answer"]
        else:
            result = compile_and_run_c(code_instance, CONFIG["execution_timeout"], template_name=filename, stdin_input=stdin_input)
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
        generated_variants.add(variant_id)
        generated_count += 1
        print(f"    -> Generada pregunta #{generated_count} (Respuesta: '{correct_answer}')")

    if generated_count < args.num:
        print(f"    [!] Advertencia: Solo se generaron {generated_count}/{args.num} preguntas únicas.", file=sys.stderr)

def main():
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
    args = parser.parse_args()

    # Si se especifica --generate-only, solo generamos código C
    if args.generate_only:
        generate_c_code_only(args)
        return

    root = Element("quiz")
    
    # Determinar si estamos procesando un archivo individual o un directorio
    if args.template:
        # Modo archivo individual
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
        # Modo directorio (comportamiento original)
        if not os.path.isdir(args.source):
            print(f"Error: El directorio '{args.source}' no existe.", file=sys.stderr)
            sys.exit(1)
        
        print(f"Buscando plantillas en: '{args.source}'...")
        processed_files = 0

        for dirpath, _, filenames in os.walk(args.source):
            # --- LÓGICA DE CATEGORIZACIÓN ---
            # 1. Se crea la categoría para el directorio actual ANTES de procesar sus archivos.
            # Ignorar directorios sin archivos .c para no crear categorías vacías
            if not any(fname.endswith('.c') for fname in filenames):
                continue

            relative_path = os.path.relpath(dirpath, args.source)
            moodle_category_path = f"$course$/top/{args.category}"
            if relative_path != ".":
                moodle_category_path += f"/{relative_path.replace(os.sep, '/')}"
            
            create_category_xml(root, moodle_category_path)
            print(f"\n📁 Creando categoría: {moodle_category_path}")

            # 2. Ahora, se procesan todos los archivos .c de este directorio.
            #    Sus preguntas se añadirán al XML justo después de la declaración de categoría.
            for filename in filenames:
                if filename.endswith(".c"):
                    processed_files += 1
                    filepath = os.path.join(dirpath, filename)
                    print(f"  📄 Procesando plantilla: {filename}")

                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # --- CAMBIO PRINCIPAL AQUÍ ---
                    # Se purgan todos los comentarios de documentación interna (//#) al inicio.
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
                    
                    generated_count = 0
                    attempts = 0
                    generated_variants = set()

                    while generated_count < args.num and attempts < args.num * 5:
                        attempts += 1
                        variables = generate_vars(template_info['var_defs'])
                        variant_id = tuple(sorted(variables.items()))
                        if variant_id in generated_variants:
                            continue
                        
                        code_instance = template_info['code_template']
                        for name, value in variables.items():
                            code_instance = code_instance.replace(f"__{name}__", str(value))
                        
                        # Generar STDIN si existe en la plantilla
                        stdin_input = None
                        if template_info.get('stdin_template'):
                            stdin_input = generate_stdin(template_info['stdin_template'], variables)
                        
                        # Determinar la respuesta correcta: evaluar expresión, usar fija, o compilar.
                        if template_info.get("correct_answer_expression"):
                            # Evaluar la expresión con las variables actuales
                            try:
                                expr = template_info["correct_answer_expression"]
                                # Reemplazar variables en la expresión
                                for name, value in variables.items():
                                    expr = expr.replace(f"__{name}__", str(value))
                                correct_answer = str(eval(expr))
                            except Exception as e:
                                print(f"  [!] Error evaluando expresión de respuesta correcta: {e}", file=sys.stderr)
                                continue
                        elif template_info.get("fixed_correct_answer"):
                            correct_answer = template_info["fixed_correct_answer"]
                        else:
                            result = compile_and_run_c(code_instance, CONFIG["execution_timeout"], template_name=filename, stdin_input=stdin_input)
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
                        generated_variants.add(variant_id)
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

def generate_c_code_only(args):
    """
    Genera solo el código C de las plantillas en el directorio 'generated'.
    Cada archivo .c genera múltiples variantes en su propio subdirectorio.
    También crea un Makefile para compilar todos los archivos.
    Soporta tanto directorios como archivos individuales.
    """
    generated_dir = "generated"
    if os.path.exists(generated_dir):
        import shutil
        shutil.rmtree(generated_dir)
    os.makedirs(generated_dir)
    
    makefile_targets = []
    all_executables = []
    
    print(f"🚀 Generando código C en directorio '{generated_dir}'...")
    
    # Determinar si estamos procesando un archivo individual o un directorio
    if args.template:
        # Modo archivo individual
        if not os.path.isfile(args.template):
            print(f"Error: El archivo '{args.template}' no existe.", file=sys.stderr)
            return
        if not args.template.endswith('.c'):
            print(f"Error: El archivo '{args.template}' no es un archivo .c", file=sys.stderr)
            return
        
        files_to_process = [(args.template, os.path.dirname(args.template) or ".")]
    else:
        # Modo directorio: recolectar todos los archivos .c
        files_to_process = []
        for dirpath, dirnames, filenames in os.walk(args.source):
            for filename in filenames:
                if filename.endswith(".c"):
                    filepath = os.path.join(dirpath, filename)
                    files_to_process.append((filepath, dirpath))
    
    # Procesar todos los archivos
    for filepath, dirpath in files_to_process:
        filename = os.path.basename(filepath)
        print(f"\n📄 Procesando plantilla: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Purgar comentarios de documentación interna
        content = re.sub(r'^\s*//\s*#.*$\n?', '', content, flags=re.MULTILINE)
        
        template_info = parse_c_template(content)
        if template_info.get("status") == "error":
            print(f"  [!] No se pudo procesar {filename}. Razón: {template_info.get('reason')}", file=sys.stderr)
            continue
        
        # Crear subdirectorio para este archivo
        base_name = os.path.splitext(filename)[0]
        if args.template:
            # Para archivo individual, usar solo el nombre base
            output_subdir = os.path.join(generated_dir, base_name)
        else:
            # Para directorio, mantener la estructura
            relative_path = os.path.relpath(dirpath, args.source)
            if relative_path != ".":
                output_subdir = os.path.join(generated_dir, relative_path, base_name)
            else:
                output_subdir = os.path.join(generated_dir, base_name)
        
        os.makedirs(output_subdir, exist_ok=True)
        
        # Generar variantes
        generated_count = 0
        attempts = 0
        generated_variants = set()
        
        while generated_count < args.num and attempts < args.num * 5:
            attempts += 1
            variables = generate_vars(template_info['var_defs'])
            variant_id = tuple(sorted(variables.items()))
            if variant_id in generated_variants:
                continue
            
            code_instance = template_info['code_template']
            for name, value in variables.items():
                code_instance = code_instance.replace(f"__{name}__", str(value))
            
            # Guardar variante
            variant_filename = f"{base_name}_v{generated_count + 1}.c"
            variant_path = os.path.join(output_subdir, variant_filename)
            
            with open(variant_path, 'w', encoding='utf-8') as f:
                f.write(code_instance)
            
            # Agregar al makefile
            relative_variant_path = os.path.relpath(variant_path, generated_dir)
            executable_name = os.path.splitext(relative_variant_path)[0]
            makefile_targets.append((relative_variant_path, executable_name))
            all_executables.append(executable_name)
            
            generated_variants.add(variant_id)
            generated_count += 1
            print(f"    -> Generada variante {variant_filename}")
        
        if generated_count < args.num:
            print(f"    [!] Advertencia: Solo se generaron {generated_count}/{args.num} variantes únicas.", file=sys.stderr)
    
    # Crear Makefile
    makefile_path = os.path.join(generated_dir, "Makefile")
    with open(makefile_path, 'w', encoding='utf-8') as f:
        f.write("# Makefile generado automáticamente\n")
        f.write("CC = gcc\n")
        f.write("CFLAGS = -Wall -Wextra\n\n")
        
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
