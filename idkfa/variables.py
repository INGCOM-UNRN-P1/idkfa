"""Módulo para la generación, filtrado y adaptación gramatical de variables y distractores."""

import re
import sys
import random
import itertools
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Set, Union, Tuple
from idkfa.parser import DistractorDef

class DistractorOption(str):
    feedback: str

    def __new__(cls, text: Any, feedback: str = "") -> "DistractorOption":
        obj = super().__new__(cls, str(text))
        obj.feedback = feedback
        return obj

    @property
    def text(self) -> str:
        return str(self)

def generate_vars(var_defs: Dict[str, str]) -> Dict[str, Any]:
    """Genera un conjunto de valores concretos a partir de las definiciones de variables, soportando dependencias."""
    generated: Dict[str, Any] = {}
    for name, definition in var_defs.items():
        try:
            def_str = definition
            for prev_name, prev_val in generated.items():
                def_str = def_str.replace(f"__{prev_name}__", str(prev_val))
            
            value_pool = eval(def_str, {"__builtins__": __builtins__}, generated)
            if hasattr(value_pool, '__iter__') and not isinstance(value_pool, (str, bytes)):
                pool_list = list(value_pool)
                generated[name] = random.choice(pool_list) if pool_list else ""
            else:
                generated[name] = value_pool
        except Exception as e:
            print(f"  [!] Error evaluando la definición de variable '{name}': {e}", file=sys.stderr)
            generated[name] = ""
    return generated

def generate_all_variants_deterministically(var_defs: Dict[str, str], max_count: int) -> List[Dict[str, Any]]:
    """
    Genera combinaciones deterministas de variables.
    Si el espacio cartesiano es enumerable y finito, muestrea sin reemplazo.
    Soporta variables dependientes evaluando en orden topológico secuencial.
    """
    if not var_defs:
        return [{}]

    var_names = list(var_defs.keys())
    static_domains: Dict[str, List[Any]] = {}
    has_dynamic_deps = False
    
    for name, definition in var_defs.items():
        if any(f"__{prev}__" in definition or re.search(rf'\b{prev}\b', definition) for prev in static_domains):
            has_dynamic_deps = True
            break
        try:
            val = eval(definition, {"__builtins__": __builtins__}, {})
            if hasattr(val, '__iter__') and not isinstance(val, (str, bytes)):
                val_list = list(val)
                if len(val_list) > 1000:
                    has_dynamic_deps = True
                    break
                static_domains[name] = val_list
            else:
                static_domains[name] = [val]
        except Exception:
            has_dynamic_deps = True
            break

    if not has_dynamic_deps and len(static_domains) == len(var_names):
        keys = list(static_domains.keys())
        all_combinations = list(itertools.product(*(static_domains[k] for k in keys)))
        comb_dicts = [dict(zip(keys, prod)) for prod in all_combinations]
        if len(comb_dicts) <= max_count:
            random.shuffle(comb_dicts)
            return comb_dicts
        return random.sample(comb_dicts, max_count)

    unique_variants: List[Dict[str, Any]] = []
    seen: Set[Any] = set()
    attempts = 0
    max_attempts = max_count * 10
    
    while len(unique_variants) < max_count and attempts < max_attempts:
        attempts += 1
        vars_inst = generate_vars(var_defs)
        var_key = tuple(sorted(vars_inst.items()))
        if var_key not in seen:
            seen.add(var_key)
            unique_variants.append(vars_inst)
            
    return unique_variants

def normalize_answer_repr(ans: Any) -> str:
    """Normaliza la representación de una respuesta para comparación."""
    if ans is None:
        return ""
    ans_str = str(ans).strip()
    try:
        f_val = float(ans_str)
        if f_val.is_integer():
            return str(int(f_val))
        return f"{f_val:g}"
    except (ValueError, TypeError):
        return ans_str

def adapt_grammar_and_pluralization(text: str, variables: Dict[str, Any]) -> str:
    """
    Adapta pluralizaciones y concordancia gramatical según los valores de las variables.
    Sintaxis:
      [plural:var_name|singular|plural]
      [gender:var_name|masculino|femenino]
    """
    def replace_plural(match: re.Match) -> str:
        var_name = match.group(1).strip()
        sing = match.group(2).strip()
        plur = match.group(3).strip()
        val = variables.get(var_name, 0)
        try:
            num = float(val)
            return sing if abs(num) == 1 else plur
        except (ValueError, TypeError):
            return plur

    def replace_gender(match: re.Match) -> str:
        var_name = match.group(1).strip()
        masc = match.group(2).strip()
        fem = match.group(3).strip()
        val = str(variables.get(var_name, "")).strip().lower()
        if val in ["f", "fem", "femenino", "mujer", "female", "a"]:
            return fem
        return masc

    out = re.sub(r'\[plural:\s*([a-zA-Z0-9_]+)\s*\|\s*([^|]*)\s*\|\s*([^\]]*)\]', replace_plural, text)
    out = re.sub(r'\[gender:\s*([a-zA-Z0-9_]+)\s*\|\s*([^|]*)\s*\|\s*([^\]]*)\]', replace_gender, out)
    return out

def is_mathematically_trivial(candidate_str: str, correct_answer: Any) -> bool:
    """
    Detecta y filtra distractores triviales o absurdos:
    - Negativos cuando la respuesta correcta es un número positivo no nulo (ej: tamaño, índice, puntero)
    - Distractores idénticos a NaN, inf, o saltos desproporcionados (> 1000x)
    """
    cand = str(candidate_str).strip()
    if cand.lower() in ["nan", "inf", "-inf", "null", "none"]:
        return True
    try:
        cand_num = float(cand)
        corr_num = float(str(correct_answer).strip())
        
        # Si la respuesta correcta es positiva (e.g. longitud de array, salida de conteo >= 0) y el distractor es negativo
        if corr_num >= 0 and cand_num < 0:
            return True
        
        # Saltos absurdos
        if corr_num > 0 and cand_num > corr_num * 1000:
            return True
    except (ValueError, TypeError):
        pass
    return False

def generate_incorrect_answers(
    correct_answer: Any, 
    predefined_options: List[str], 
    distractor_expressions: Union[List[str], List[DistractorDef]], 
    variables: Dict[str, Any], 
    count: int = 3,
    template_name: Optional[str] = None
) -> List[DistractorOption]:
    """Genera una lista de respuestas incorrectas con feedback específico y filtro de trivialidad."""
    norm_correct = normalize_answer_repr(correct_answer)
    seen_normalized: Set[str] = {norm_correct}
    
    unique_incorrect: List[DistractorOption] = []

    # 1. Opciones predefinidas
    for opt in predefined_options:
        opt_str = str(opt).strip()
        norm_opt = normalize_answer_repr(opt_str)
        if norm_opt and norm_opt not in seen_normalized and not is_mathematically_trivial(opt_str, correct_answer):
            seen_normalized.add(norm_opt)
            unique_incorrect.append(DistractorOption(text=opt_str, feedback=""))

    # 2. Expresiones de distractores
    for d in distractor_expressions:
        if isinstance(d, DistractorDef):
            expr = d.expression
            fb_template = d.feedback or ""
        else:
            expr = str(d)
            fb_template = ""

        temp_expr = expr
        try:
            for var_name, var_value in variables.items():
                if isinstance(var_value, (int, float)):
                    temp_expr = temp_expr.replace(f"__{var_name}__", str(var_value))
            
            # Evaluar pasando variables como contexto global/local
            eval_globals = {"__builtins__": __builtins__, "chr": chr, "ord": ord, "int": int, "float": float, "str": str, "bin": bin, "hex": hex}
            calculated_value = eval(temp_expr, eval_globals, dict(variables))
            calc_str = str(calculated_value).strip()
            norm_calc = normalize_answer_repr(calc_str)
            
            if norm_calc and norm_calc not in seen_normalized and not is_mathematically_trivial(calc_str, correct_answer):
                seen_normalized.add(norm_calc)
                
                # Evaluar feedback específico
                fb_eval = fb_template
                if fb_eval:
                    for v_name, v_val in variables.items():
                        fb_eval = fb_eval.replace(f"__{v_name}__", str(v_val))
                unique_incorrect.append(DistractorOption(text=calc_str, feedback=fb_eval))
        except Exception as e:
            origin_info = f" [{template_name}]" if template_name else ""
            print(f"    [!] Advertencia{origin_info}: No se pudo calcular el distractor '{expr}': {e}", file=sys.stderr)

    # 3. Generación aleatoria de offsets numéricos no triviales
    try:
        num_correct = int(float(str(correct_answer).strip()))
        attempts = 0
        while len(unique_incorrect) < count and attempts < 100:
            offset = random.randint(1, 10) * random.choice([-1, 1])
            new_val = num_correct + offset
            new_incorrect = str(new_val)
            norm_new = normalize_answer_repr(new_incorrect)
            if norm_new not in seen_normalized and not is_mathematically_trivial(new_incorrect, correct_answer):
                seen_normalized.add(norm_new)
                unique_incorrect.append(DistractorOption(text=new_incorrect, feedback=""))
            attempts += 1
    except (ValueError, TypeError):
        pass

    random.shuffle(unique_incorrect)
    return unique_incorrect

def generate_stdin(stdin_template: Optional[str], variables: Dict[str, Any]) -> Optional[str]:
    """Genera el contenido de STDIN dinámicamente a partir de una plantilla y variables."""
    if not stdin_template:
        return None
    
    try:
        stdin_content = stdin_template
        for name, value in variables.items():
            stdin_content = stdin_content.replace(f"__{name}__", str(value))
        
        def replace_expr(match: re.Match) -> str:
            expr_str = match.group(1)
            try:
                val = eval(expr_str, {"__builtins__": __builtins__}, variables)
                return str(val)
            except Exception:
                return match.group(0)

        stdin_content = re.sub(r'\{([^}]+)\}', replace_expr, stdin_content)
        return stdin_content
    except Exception as e:
        print(f"  [!] Error generando STDIN: {e}", file=sys.stderr)
        return stdin_template
