"""Módulo para la generación del árbol XML compatible con Moodle Question Bank."""

import re
import sys
from xml.etree.ElementTree import SubElement, Element
from typing import Dict, List, Optional, Any
from idkfa.config import CONFIG
from idkfa.variables import normalize_answer_repr

def CDATA(text: Any) -> str:
    """Envuelve el texto para la conversión a CDATA."""
    if str(text).strip().startswith("<![CDATA["):
        return str(text)
    return f"<![CDATA[{text}]]>"

def evaluate_feedback(feedback_template: Optional[str], variables: Dict[str, Any]) -> str:
    """Genera el texto de retroalimentación reemplazando variables y expresiones."""
    if not feedback_template:
        return ""
    try:
        fb_content = feedback_template
        for name, value in variables.items():
            fb_content = fb_content.replace(f"__{name}__", str(value))
        
        def replace_expr(match: re.Match) -> str:
            expr_str = match.group(1)
            try:
                val = eval(expr_str, {}, variables)
                return str(val)
            except Exception:
                return match.group(0)

        fb_content = re.sub(r'\{([^}]+)\}', replace_expr, fb_content)
        return fb_content
    except Exception as e:
        print(f"  [!] Error evaluando feedback: {e}", file=sys.stderr)
        return feedback_template

def create_moodle_question_xml(
    parent: Element, 
    template_info: Any, 
    code_instance: str, 
    correct_answer: Any, 
    incorrect_answers: List[str], 
    question_number: int, 
    stdin_content: Optional[str] = None, 
    variables: Optional[Dict[str, Any]] = None, 
    args: Optional[Any] = None
) -> None:
    """Construye el árbol XML para una pregunta, respetando el orden del XSD."""
    question_type: str = template_info.get("question_type", "multichoice") if hasattr(template_info, "get") else getattr(template_info, "question_type", "multichoice")
    q_node = SubElement(parent, "question", type=question_type)
    
    base_name: str = template_info.get("name", "Pregunta") if hasattr(template_info, "get") else getattr(template_info, "name", "Pregunta")
    numbered_name = f"{base_name} - {question_number}"
    SubElement(SubElement(q_node, "name"), "text").text = CDATA(numbered_name)
    
    questiontext_node = SubElement(SubElement(q_node, "questiontext", format="markdown"), "text")
    q_template: str = template_info.get("question_text_template", "") if hasattr(template_info, "get") else getattr(template_info, "question_text_template", "")
    question_text_with_code = q_template.replace("{code}", code_instance)
    
    if stdin_content:
        stdin_section = f"\n\n#### Entrada (stdin):\n```\n{stdin_content}\n```"
        question_text_with_code += stdin_section
    
    questiontext_node.text = CDATA(question_text_with_code)

    # Feedback general dinámico
    fb_text = ""
    fb_template = template_info.get("feedback_template") if hasattr(template_info, "get") else getattr(template_info, "feedback_template", None)
    if fb_template and variables:
        fb_text = evaluate_feedback(fb_template, variables)
    SubElement(SubElement(q_node, "generalfeedback", format="markdown"), "text").text = CDATA(fb_text)

    # Configuración de defaultgrade y penalty
    default_grade = template_info.get("default_grade") if hasattr(template_info, "get") else getattr(template_info, "default_grade", None)
    if not default_grade:
        default_grade = getattr(args, "defaultgrade", None) or CONFIG.get("default_grade", "1.0000000")
    SubElement(q_node, "defaultgrade").text = str(default_grade)

    penalty = template_info.get("penalty") if hasattr(template_info, "get") else getattr(template_info, "penalty", None)
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

    SubElement(q_node, "idnumber").text = ""

def create_category_xml(parent: Element, category_path: str) -> None:
    """Crea el XML para una categoría, respetando el orden del XSD."""
    cat_question = SubElement(parent, "question", type="category")
    category = SubElement(cat_question, "category")
    SubElement(category, "text").text = category_path
    SubElement(SubElement(cat_question, "info", format="moodle_auto_format"), "text").text = ""
    SubElement(cat_question, "idnumber").text = ""
