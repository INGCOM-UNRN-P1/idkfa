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
                    if line and not line.startswith('#'):
                        distractor_expressions.append(line)

        correcta_match = re.search(r"/\*correcta\s*(.*?)\*/", content, re.DOTALL)
        fixed_correct_answer = None
        if correcta_match:
            fixed_correct_answer = correcta_match.group(1).strip()

        return {
            "status": "success",
            "question_text_template": f"{intro_text}\n```c\n{{code}}\n```\n{outro_text}",
            "code_template": cleaned_code_block,
            "var_defs": var_defs,
            "predefined_options": predefined_options,
            "distractor_expressions": distractor_expressions,
            "name": question_name,
            "fixed_correct_answer": fixed_correct_answer
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

def compile_and_run_c(code, timeout, template_name=None):
    """Compila y ejecuta un string de código C."""
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

def generate_incorrect_answers(correct_answer, predefined_options, distractor_expressions, variables, count=3):
    """Genera una lista de respuestas incorrectas, incluyendo distractores calculados."""
    incorrect = set(predefined_options)

    for expr in distractor_expressions:
        temp_expr = expr
        try:
            for var_name, var_value in variables.items():
                temp_expr = temp_expr.replace(f"__{var_name}__", str(var_value))
            
            calculated_value = eval(temp_expr)
            incorrect.add(str(calculated_value))
        except Exception as e:
            print(f"    [!] Advertencia: No se pudo calcular el distractor '{expr}': {e}", file=sys.stderr)

    try:
        num_correct = int(correct_answer)
        attempts = 0
        while len(incorrect) < len(predefined_options) + len(distractor_expressions) + count and attempts < 50:
            offset = random.randint(1, 10) * random.choice([-1, 1])
            new_incorrect = num_correct + offset
            if new_incorrect != num_correct:
                incorrect.add(str(new_incorrect))
            attempts += 1
    except (ValueError, TypeError):
        pass

    if str(correct_answer) in incorrect:
        incorrect.remove(str(correct_answer))
        
    final_incorrect = list(incorrect)
    random.shuffle(final_incorrect)
    
    return final_incorrect

def create_moodle_question_xml(parent, template_info, code_instance, correct_answer, incorrect_answers, question_number):
    """Construye el árbol XML para una pregunta, respetando el orden del XSD."""
    q_node = SubElement(parent, "question", type="multichoice")
    
    # El orden de los siguientes elementos es estricto para cumplir con bank.xsd
    base_name = template_info['name']
    numbered_name = f"{base_name} - {question_number}"
    SubElement(SubElement(q_node, "name"), "text").text = CDATA(numbered_name)
    
    questiontext_node = SubElement(SubElement(q_node, "questiontext", format="markdown"), "text")
    question_text_with_code = template_info['question_text_template'].replace("{code}", code_instance)
    questiontext_node.text = CDATA(question_text_with_code)

    SubElement(SubElement(q_node, "generalfeedback", format="markdown"), "text").text = CDATA("")
    SubElement(q_node, "defaultgrade").text = "1.0000000"
    SubElement(q_node, "penalty").text = "0.3333333"
    SubElement(q_node, "hidden").text = "0"
    SubElement(q_node, "single").text = "true"
    SubElement(q_node, "shuffleanswers").text = "true"
    SubElement(q_node, "answernumbering").text = "abc"
    SubElement(q_node, "showstandardinstruction").text = "0"
    SubElement(SubElement(q_node, "correctfeedback", format="markdown"), "text").text = CDATA("")
    SubElement(SubElement(q_node, "partiallycorrectfeedback", format="markdown"), "text").text = CDATA("")
    SubElement(SubElement(q_node, "incorrectfeedback", format="markdown"), "text").text = CDATA("")

    # Bloque de respuestas
    ans_correct = SubElement(q_node, "answer", fraction="100", format="markdown")
    SubElement(ans_correct, "text").text = CDATA(f"`{correct_answer}`")
    SubElement(SubElement(ans_correct, "feedback", format="markdown"), "text").text = CDATA("")

    for ans_text in incorrect_answers:
        ans_incorrect = SubElement(q_node, "answer", fraction="0", format="markdown")
        formatted_ans_text = f"`{ans_text}`" if str(ans_text).isnumeric() or (str(ans_text).startswith('-') and str(ans_text)[1:].isnumeric()) else str(ans_text)
        SubElement(ans_incorrect, "text").text = CDATA(formatted_ans_text)
        SubElement(SubElement(ans_incorrect, "feedback", format="markdown"), "text").text = CDATA("")

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

def main():
    parser = argparse.ArgumentParser(description="Generador de Cuestionarios Moodle XML (validado por XSD) desde plantillas C.")
    parser.add_argument("-s", "--source", default=CONFIG["source_directory"], help="Directorio con las plantillas .c")
    parser.add_argument("-o", "--output", default=CONFIG["output_file"], help="Archivo XML de salida")
    parser.add_argument("-n", "--num", type=int, default=CONFIG["questions_per_template"], help="Número de preguntas a generar por plantilla")
    parser.add_argument("-c", "--category", default=CONFIG["moodle_base_category"], help="Categoría base en Moodle")
    args = parser.parse_args()

    root = Element("quiz")
    
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
                    
                    # Determinar la respuesta correcta: usar la fija o compilar.
                    if template_info.get("fixed_correct_answer"):
                        correct_answer = template_info["fixed_correct_answer"]
                    else:
                        result = compile_and_run_c(code_instance, CONFIG["execution_timeout"], template_name=filename)
                        if not result:
                            continue
                        correct_answer = result['output']
                    
                    # Generar opciones incorrectas y crear el XML
                    incorrect_answers = generate_incorrect_answers(
                        correct_answer, 
                        template_info['predefined_options'], 
                        template_info['distractor_expressions'],
                        variables
                    )
                    
                    # Crear una copia del código para visualización con sustituciones
                    display_code_instance = code_instance
                    substitutions = CONFIG.get("substitutions", {})
                    for old, new in substitutions.items():
                        display_code_instance = display_code_instance.replace(old, new)

                    create_moodle_question_xml(root, template_info, display_code_instance, correct_answer, incorrect_answers, generated_count + 1)
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

if __name__ == "__main__":
    main()
