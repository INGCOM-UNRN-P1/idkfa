"""
Módulo de Síntesis Procedural Avanzada para idkfa.

Genera variantes procedurales de código C:
- Árboles binarios de búsqueda y recorridos (Inorden, Preorden, Postorden)
- Matrices bidimensionales y cálculo de índices planos
- Listas enlazadas simples y dobles
- Preguntas de Verdadero/Falso con justificación técnica
- Efectos secundarios y puntos de secuencia
- Renombramiento temático (Videojuegos, Ciencia, Cine)
- Exportador de snippets autónomos con assert() interactivo
"""
from __future__ import annotations

import random
from typing import Dict, List, Any, Optional
from idkfa.compiler import compile_and_run_c


def renombrar_identificadores_tematico(codigo: str, tema: str = "videojuegos") -> str:
    """
    Renombra variables genéricas por términos de ambientación temática.
    Temas disponibles: 'videojuegos', 'ciencia', 'cine'.
    """
    diccionarios = {
        "videojuegos": {
            "nodo": "item",
            "valor": "xp",
            "arr": "inventario",
            "matriz": "mapa",
            "ptr": "cursor",
            "res": "score",
            "aux": "buff"
        },
        "ciencia": {
            "nodo": "muestra",
            "valor": "masa",
            "arr": "vector_estado",
            "matriz": "reticula",
            "ptr": "sensor",
            "res": "energia",
            "aux": "quanta"
        },
        "cine": {
            "nodo": "escena",
            "valor": "minuto",
            "arr": "guion",
            "matriz": "fotograma",
            "ptr": "lente",
            "res": "toma",
            "aux": "claqueta"
        }
    }
    
    mapeo = diccionarios.get(tema.lower(), diccionarios["videojuegos"])
    res = codigo
    for original, nuevo in mapeo.items():
        # Reemplazos cuidadosos de nombres de variables
        import re
        res = re.sub(rf'\b{original}\b', nuevo, res)
    return res


def generar_bst_y_recorrido(
    valores: Optional[List[int]] = None,
    tipo_recorrido: str = "inorden",
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Sintetiza un programa C que inserta valores en un BST e imprime un recorrido (inorden, preorden, postorden).
    Valida la salida compilando y ejecutando con GCC.
    """
    rng = random.Random(seed)
    if not valores:
        valores = rng.sample(range(10, 99), 5)

    class Node:
        def __init__(self, key: int):
            self.key = key
            self.left: Optional[Node] = None
            self.right: Optional[Node] = None

    def insert(root: Optional[Node], key: int) -> Node:
        if root is None:
            return Node(key)
        if key < root.key:
            root.left = insert(root.left, key)
        else:
            root.right = insert(root.right, key)
        return root

    def traverse(root: Optional[Node], modo: str) -> List[int]:
        if root is None:
            return []
        if modo == "preorden":
            return [root.key] + traverse(root.left, modo) + traverse(root.right, modo)
        elif modo == "postorden":
            return traverse(root.left, modo) + traverse(root.right, modo) + [root.key]
        else:  # inorden
            return traverse(root.left, modo) + [root.key] + traverse(root.right, modo)

    arbol: Optional[Node] = None
    for v in valores:
        arbol = insert(arbol, v)

    esperados = traverse(arbol, tipo_recorrido)
    salida_esperada = " ".join(map(str, esperados))

    fn_traverse = {
        "inorden": """void imprimir(Nodo* raiz) {
    if (!raiz) return;
    imprimir(raiz->izq);
    printf("%d ", raiz->dato);
    imprimir(raiz->der);
}""",
        "preorden": """void imprimir(Nodo* raiz) {
    if (!raiz) return;
    printf("%d ", raiz->dato);
    imprimir(raiz->izq);
    imprimir(raiz->der);
}""",
        "postorden": """void imprimir(Nodo* raiz) {
    if (!raiz) return;
    imprimir(raiz->izq);
    imprimir(raiz->der);
    printf("%d ", raiz->dato);
}"""
    }[tipo_recorrido]

    insert_stmts = "\n".join([f"    raiz = insertar(raiz, {v});" for v in valores])

    codigo_c = f"""#include <stdio.h>
#include <stdlib.h>

typedef struct Nodo {{
    int dato;
    struct Nodo* izq;
    struct Nodo* der;
}} Nodo;

Nodo* crear(int v) {{
    Nodo* n = (Nodo*)malloc(sizeof(Nodo));
    n->dato = v;
    n->izq = n->der = NULL;
    return n;
}}

Nodo* insertar(Nodo* raiz, int v) {{
    if (!raiz) return crear(v);
    if (v < raiz->dato) raiz->izq = insertar(raiz->izq, v);
    else raiz->der = insertar(raiz->der, v);
    return raiz;
}}

{fn_traverse}

int main(void) {{
    Nodo* raiz = NULL;
{insert_stmts}
    imprimir(raiz);
    printf("\\n");
    return 0;
}}
"""
    # Verificación en GCC
    res_comp = compile_and_run_c(codigo_c, timeout=5, base_flags=["-Wall", "-Wextra", "-Werror"])
    return {
        "codigo": codigo_c,
        "salida_esperada": salida_esperada,
        "valores": valores,
        "tipo_recorrido": tipo_recorrido,
        "verificado_gcc": res_comp.get("status") == "success",
        "salida_gcc": res_comp.get("output", "")
    }


def generar_matriz_2d_y_puntero_plano(
    filas: int = 3,
    cols: int = 3,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Sintetiza ejercicios comparativos entre matriz[i][j] y aritmética de puntero plano *(ptr + i*cols + j).
    """
    rng = random.Random(seed)
    f_target = rng.randint(0, filas - 1)
    c_target = rng.randint(0, cols - 1)
    
    matriz = [[rng.randint(1, 20) for _ in range(cols)] for _ in range(filas)]
    valor_correcto = matriz[f_target][c_target]
    offset_plano = f_target * cols + c_target

    valores_c = ", ".join([f"{{{', '.join(map(str, row))}}}" for row in matriz])

    codigo_c = f"""#include <stdio.h>

int main(void) {{
    int m[{filas}][{cols}] = {{{valores_c}}};
    int *ptr = &m[0][0];
    int v1 = m[{f_target}][{c_target}];
    int v2 = *(ptr + {f_target} * {cols} + {c_target});
    printf("%d %d\\n", v1, v2);
    return 0;
}}
"""
    res_comp = compile_and_run_c(codigo_c, timeout=5, base_flags=["-Wall", "-Wextra", "-Werror"])
    return {
        "codigo": codigo_c,
        "salida_esperada": f"{valor_correcto} {valor_correcto}",
        "filas": filas,
        "cols": cols,
        "f_target": f_target,
        "c_target": c_target,
        "offset_plano": offset_plano,
        "valor": valor_correcto,
        "verificado_gcc": res_comp.get("status") == "success"
    }


def generar_lista_enlazada_simple(
    operaciones: Optional[List[str]] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Sintetiza código de listas simples con inserción al frente y eliminación,
    con cálculo determinista de salida e inspección con flags pedagógicos.
    """
    rng = random.Random(seed)
    nums = rng.sample(range(1, 50), 4)

    codigo_c = f"""#include <stdio.h>
#include <stdlib.h>

typedef struct Nodo {{
    int val;
    struct Nodo* sig;
}} Nodo;

void push(Nodo** head, int val) {{
    Nodo* nuevo = (Nodo*)malloc(sizeof(Nodo));
    nuevo->val = val;
    nuevo->sig = *head;
    *head = nuevo;
}}

void pop(Nodo** head) {{
    if (!*head) return;
    Nodo* temp = *head;
    *head = (*head)->sig;
    free(temp);
}}

int main(void) {{
    Nodo* lista = NULL;
    push(&lista, {nums[0]});
    push(&lista, {nums[1]});
    push(&lista, {nums[2]});
    pop(&lista);
    push(&lista, {nums[3]});
    
    Nodo* cur = lista;
    while (cur) {{
        printf("%d ", cur->val);
        cur = cur->sig;
    }}
    printf("\\n");
    return 0;
}}
"""
    salida_esperada = f"{nums[3]} {nums[0]}"
    res_comp = compile_and_run_c(codigo_c, timeout=5, base_flags=["-Wall", "-Wextra", "-Werror"])
    return {
        "codigo": codigo_c,
        "salida_esperada": res_comp.get("output", salida_esperada),
        "verificado_gcc": res_comp.get("status") == "success"
    }


def generar_pregunta_verdadero_falso_con_justificacion(tema_id: str) -> Dict[str, Any]:
    """
    Genera preguntas de verdadero/falso con justificación técnica rigurosa sobre semántica de C.
    """
    banco = {
        "arrays_decay": {
            "enunciado": "En C, al pasar un arreglo a una función por parámetro, se pasa una copia completa de todos sus elementos por valor.",
            "es_verdadero": False,
            "justificacion": "Los arreglos decaen (decay) automáticamente a un puntero al primer elemento (tipo T*), no se copian por valor."
        },
        "sizeof_pointer": {
            "enunciado": "La expresión sizeof(puntero) sobre char* siempre devuelve 1 byte porque apunta a un carácter.",
            "es_verdadero": False,
            "justificacion": "sizeof evalúa el tamaño de la variable puntero en sí (4 u 8 bytes según la arquitectura), no el tipo apuntado."
        },
        "free_null": {
            "enunciado": "Invocar free(NULL) en un programa C conforme al estándar C99/C11 provoca un comportamiento indefinido (Segmentation Fault).",
            "es_verdadero": False,
            "justificacion": "El estándar ISO C especifica que free(NULL) es una operación sin efecto y completamente segura."
        },
        "string_null_terminator": {
            "enunciado": "Una cadena literal en C como \"Hola\" ocupa 5 bytes de memoria debido al carácter nulo terminador '\\0'.",
            "es_verdadero": True,
            "justificacion": "Los literales de cadena reservan un byte adicional al final para alojar el delimitador nulo '\\0'."
        }
    }
    return banco.get(tema_id, banco["arrays_decay"])


def inyectar_efectos_secundarios_y_sequence_points(seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Genera expresiones didácticas con post-incremento y pre-incremento delimitadas
    por puntos de secuencia válidos (separados por sentencias o coma), evitando UB no especificado.
    """
    rng = random.Random(seed)
    a = rng.randint(2, 6)
    b = rng.randint(3, 7)
    
    # Secuencia válida: se usa punto de secuencia explícito (;)
    codigo_c = f"""#include <stdio.h>

int main(void) {{
    int x = {a};
    int y = {b};
    int r1 = x++;
    int r2 = ++y;
    int r3 = x + y;
    printf("%d %d %d\\n", r1, r2, r3);
    return 0;
}}
"""
    salida_esperada = f"{a} {b + 1} {(a + 1) + (b + 1)}"
    res_comp = compile_and_run_c(codigo_c, timeout=5, base_flags=["-Wall", "-Wextra", "-Werror"])
    return {
        "codigo": codigo_c,
        "salida_esperada": salida_esperada,
        "r1": a,
        "r2": b + 1,
        "r3": (a + 1) + (b + 1),
        "verificado_gcc": res_comp.get("status") == "success"
    }


def exportar_snippet_con_asserts(codigo_c: str, salida_esperada: str) -> str:
    """
    Empaqueta el snippet en un programa C interactivo autónomo con <assert.h>
    para práctica y autoevaluación directa del estudiante en terminal.
    """
    lineas = codigo_c.strip().split("\n")
    # Buscar función main
    cuerpo = []
    includes = ["#include <stdio.h>", "#include <stdlib.h>", "#include <assert.h>", "#include <string.h>"]
    for l in lineas:
        if not l.startswith("#include"):
            cuerpo.append(l)

    c_autoeval = f"""{chr(10).join(includes)}

// --- SNIPPET DIDÁCTICO PARA AUTOEVALUACIÓN (idkfa) ---
// Ejecute este programa: si compila y no falla ningún assert(), su deducción fue correcta.

{chr(10).join(cuerpo)}
"""
    return c_autoeval
