"""Módulo para la generación y muestreo determinista de variables y distractores."""

import re
import sys
import random
import itertools
from typing import Dict, List, Any, Optional, Set, Union

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

def generate_incorrect_answers(
    correct_answer: Any, 
    predefined_options: List[str], 
    distractor_expressions: List[str], 
    variables: Dict[str, Any], 
    count: int = 3
) -> List[str]:
    """Genera una lista de respuestas incorrectas, normalizando opciones y evitando duplicados."""
    norm_correct = normalize_answer_repr(correct_answer)
    seen_normalized: Set[str] = {norm_correct}
    
    unique_incorrect: List[str] = []

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

def generate_stdin(stdin_template: Optional[str], variables: Dict[str, Any]) -> Optional[str]:
    """Genera el contenido de STDIN dinámicamente a partir de una plantilla y variables."""
    if not stdin_template:
        return None
    
    try:
        stdin_content = stdin_template
        for name, value in variables.items():
            stdin_content = stdin_content.replace(f"__{name}__", str(value))
        
        result_lines: List[str] = []
        for line in stdin_content.split('\n'):
            if '{' in line and '}' in line:
                try:
                    eval_context = variables.copy()
                    processed_line = line.format(**eval_context)
                    result_lines.append(processed_line)
                except Exception:
                    result_lines.append(line)
            else:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    except Exception as e:
        print(f"  [!] Error generando STDIN: {e}", file=sys.stderr)
        return stdin_template
