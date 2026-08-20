"""Módulo para el análisis y validación semántica de plantillas C."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Tuple

@dataclass
class DistractorDef:
    expression: str
    feedback: Optional[str] = None

@dataclass
class TemplateInfo:
    status: str
    question_text_template: str = ""
    code_template: str = ""
    var_defs: Dict[str, str] = field(default_factory=dict)
    predefined_options: List[str] = field(default_factory=list)
    distractor_expressions: List[str] = field(default_factory=list)
    distractor_defs: List[DistractorDef] = field(default_factory=list)
    name: str = "Pregunta de Código C (sin nombre)"
    fixed_correct_answer: Optional[str] = None
    correct_answer_expression: Optional[str] = None
    stdin_template: Optional[str] = None
    custom_flags: List[str] = field(default_factory=list)
    penalty: Optional[str] = None
    default_grade: Optional[str] = None
    question_type: str = "multichoice"
    feedback_template: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "question_text_template": self.question_text_template,
            "code_template": self.code_template,
            "var_defs": self.var_defs,
            "predefined_options": self.predefined_options,
            "distractor_expressions": self.distractor_expressions,
            "distractor_defs": self.distractor_defs,
            "name": self.name,
            "fixed_correct_answer": self.fixed_correct_answer,
            "correct_answer_expression": self.correct_answer_expression,
            "stdin_template": self.stdin_template,
            "custom_flags": self.custom_flags,
            "penalty": self.penalty,
            "default_grade": self.default_grade,
            "question_type": self.question_type,
            "feedback_template": self.feedback_template,
            "reason": self.reason,
        }

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


def parse_c_template(content: str) -> Union[TemplateInfo, Dict[str, Any]]:
    """Analiza el contenido de un archivo .c, incluyendo metadatos y validaciones."""
    try:
        lines = content.split('\n')
        
        intro_line_index = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('//'):
                intro_line_index = i
                break
        
        if intro_line_index == -1:
            return TemplateInfo(status="error", reason="No se encontró el comentario de introducción (primera línea que empieza con //).")

        outro_line_index = -1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('//'):
                outro_line_index = i
                break

        if outro_line_index <= intro_line_index:
            return TemplateInfo(status="error", reason="No se encontró el comentario de cierre (segunda línea que empieza con //).")

        intro_text = lines[intro_line_index].strip().lstrip('//').strip()
        outro_text = lines[outro_line_index].strip().lstrip('//').strip()
        code_block = '\n'.join(lines[intro_line_index+1:outro_line_index])

        cleaned_code_block = re.sub(r'#define\s+__\w+__\s+.*\n?', '', code_block)
        
        # --- Lectura de variables ---
        var_match = re.search(r"/\*var\s*(.*?)\*/", content, re.DOTALL)
        var_defs: Dict[str, str] = {}
        if var_match:
            lines_var = var_match.group(1).strip().split('\n')
            for line in lines_var:
                if ':' in line:
                    key, value = line.split(':', 1)
                    var_defs[key.strip()] = value.strip()

        # --- Opciones fijas ---
        opciones_match = re.search(r"/\*opciones\s*(.*?)\*/", content, re.DOTALL)
        predefined_options: List[str] = []
        if opciones_match:
            lines_opt = opciones_match.group(1).strip().split('\n')
            predefined_options = [l.strip() for l in lines_opt if l.strip()]

        # --- Nombre ---
        name_match = re.search(r"/\*name\s*(.*?)\*/", content, re.DOTALL)
        question_name = name_match.group(1).strip() if name_match else "Pregunta de Código C (sin nombre)"

        # --- Distractors con soporte para feedback específico ---
        distractors_match = re.search(r"/\*distractors\s*(.*?)\*/", content, re.DOTALL)
        distractor_expressions: List[str] = []
        distractor_defs: List[DistractorDef] = []
        if distractors_match:
            distractor_content = distractors_match.group(1).strip()
            if distractor_content:
                lines_dist = distractor_content.split('\n')
                for line in lines_dist:
                    line_str = line.strip()
                    if line_str and not line_str.startswith('//#'):
                        expr = line_str
                        dist_fb: Optional[str] = None
                        # Soporte para formato de feedback: expresion -> feedback o expresion // feedback
                        if ' -> ' in expr:
                            parts = expr.split(' -> ', 1)
                            expr = parts[0].strip()
                            dist_fb = parts[1].strip()
                        elif ' // ' in expr and not expr.startswith('//') and not (expr.startswith('f"') or expr.startswith("f'")):
                            parts = expr.split(' // ', 1)
                            expr = parts[0].strip()
                            dist_fb = parts[1].strip()

                        if expr.startswith('#'):
                            expr = expr[1:].strip()
                        
                        if expr:
                            distractor_expressions.append(expr)
                            distractor_defs.append(DistractorDef(expression=expr, feedback=dist_fb))

        # --- Correcta ---
        correcta_match = re.search(r"/\*correcta\s*(.*?)\*/", content, re.DOTALL)
        fixed_correct_answer: Optional[str] = None
        correct_answer_expression: Optional[str] = None
        if correcta_match:
            correcta_content = correcta_match.group(1).strip()
            lines_corr = correcta_content.split('\n')
            clean_lines = [l for l in lines_corr if l.strip() and not l.strip().startswith('//#')]
            
            if clean_lines:
                if clean_lines[0].strip().startswith('#'):
                    correct_answer_expression = clean_lines[0].strip()[1:].strip()
                else:
                    fixed_correct_answer = '\n'.join(clean_lines)

        # --- STDIN ---
        stdin_match = re.search(r"/\*STDIN\s*(.*?)\*/", content, re.DOTALL)
        stdin_template: Optional[str] = None
        if stdin_match:
            stdin_content = stdin_match.group(1).strip()
            if stdin_content:
                lines_stdin = stdin_content.split('\n')
                stdin_lines = [l for l in lines_stdin if l.strip() and not l.strip().startswith('//#')]
                stdin_template = '\n'.join(stdin_lines)

        # --- Validación semántica temprana ---
        if not stdin_template and not fixed_correct_answer and not correct_answer_expression:
            if re.search(r'\b(scanf|fgets|getchar|getc|read|fscanf\s*\(\s*stdin)\b', cleaned_code_block):
                return TemplateInfo(
                    status="error",
                    reason="Validación semántica fallida: el código C contiene llamadas a lectura por stdin (scanf/fgets/getchar) pero no define la sección /*STDIN*/ obligatoria."
                )

        # --- Flags de compilación ---
        flags_match = re.search(r"/\*flags\s*(.*?)\*/", content, re.DOTALL)
        custom_flags: List[str] = []
        if flags_match:
            flags_content = flags_match.group(1).strip()
            if flags_content:
                custom_flags = [f.strip() for f in flags_content.split() if f.strip()]

        if re.search(r'#include\s*<math\.h>', cleaned_code_block) and "-lm" not in custom_flags:
            custom_flags.append("-lm")

        # --- Penalty ---
        penalty_match = re.search(r"/\*penalty\s*(.*?)\*/", content, re.DOTALL)
        penalty = penalty_match.group(1).strip() if penalty_match else None

        # --- Defaultgrade ---
        grade_match = re.search(r"/\*defaultgrade\s*(.*?)\*/", content, re.DOTALL)
        default_grade = grade_match.group(1).strip() if grade_match else None

        # --- Tipo de pregunta ---
        type_match = re.search(r"/\*type\s*(.*?)\*/", content, re.DOTALL)
        question_type = type_match.group(1).strip().lower() if type_match else "multichoice"
        if question_type not in ["multichoice", "shortanswer", "numerical"]:
            question_type = "multichoice"

        # --- Feedback ---
        feedback_match = re.search(r"/\*feedback\s*(.*?)\*/", content, re.DOTALL)
        feedback_template: Optional[str] = None
        if feedback_match:
            fb_lines = [l for l in feedback_match.group(1).strip().split('\n') if not l.strip().startswith('//#')]
            feedback_template = '\n'.join(fb_lines).strip()

        return TemplateInfo(
            status="success",
            question_text_template=f"{intro_text}\n```c\n{{code}}\n```\n{outro_text}",
            code_template=cleaned_code_block,
            var_defs=var_defs,
            predefined_options=predefined_options,
            distractor_expressions=distractor_expressions,
            distractor_defs=distractor_defs,
            name=question_name,
            fixed_correct_answer=fixed_correct_answer,
            correct_answer_expression=correct_answer_expression,
            stdin_template=stdin_template,
            custom_flags=custom_flags,
            penalty=penalty,
            default_grade=default_grade,
            question_type=question_type,
            feedback_template=feedback_template
        )
    except Exception as e:
        return TemplateInfo(status="error", reason=str(e))
