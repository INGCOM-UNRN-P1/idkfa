# Manual de Usuario: Generador de Cuestionarios Moodle (`generador.py`)

## 1. Introducción

`generador.py` es un script de Python diseñado para automatizar la creación de bancos de preguntas para Moodle en formato XML. A partir de plantillas de código C (`.c`), el script genera múltiples variantes de cada pregunta, compila y ejecuta el código para obtener la respuesta correcta, y produce un archivo XML listo para ser importado en Moodle.

## 2. Uso Básico

El script se ejecuta desde la línea de comandos:

```bash
python3 generador.py [opciones]
```

### Argumentos de Línea de Comandos

- **`-s` o `--source`**: Especifica el directorio donde se encuentran las plantillas (`.c`). Por defecto es `templates`.
- **`-o` o `--output`**: Especifica el nombre del archivo XML de salida. Por defecto es `cuestionario_moodle.xml`.
- **`-n` o `--num`**: El número de preguntas (variantes) a generar por cada plantilla. Por defecto es `5`.
- **`-c` o `--category`**: El nombre de la categoría raíz bajo la cual se organizarán las preguntas en Moodle. Por defecto es `programacion1_gen_codigo`.

## 3. Estructura de Directorios y Categorías

El script utiliza la estructura de directorios dentro de la carpeta `source` para crear una jerarquía de categorías en Moodle. 

Por ejemplo, una plantilla ubicada en `templates/punteros/avanzado/mi_plantilla.c` se añadirá a la siguiente categoría en Moodle:

`$course$/top/programacion1_gen_codigo/punteros/avanzado`

Esto permite organizar las preguntas de forma lógica y coherente con el temario del curso.

## 4. Anatomía de una Plantilla `.c`

Cada archivo `.c` es una plantilla que combina código C válido con bloques de metadatos especiales. Debe ser compilable y ejecutable por sí mismo para facilitar las pruebas.

### 4.1. Enunciado de la Pregunta (Comentarios `//`)

El enunciado de la pregunta se define mediante dos comentarios de una sola línea (`//`).

- **Comentario de Introducción**: La primera línea de comentario `//` que encuentra el script se usa como el texto que precede al bloque de código.
- **Comentario de Cierre**: La última línea de comentario `//` que encuentra se usa como el texto que va después del bloque de código.

```c
// Analiza el siguiente código. ¿Cuál es el valor final de 'x'?
#include <stdio.h>

int main() {
    int x = 10 + 5;
    printf("%d", x);
    return 0;
}
// ¿Qué valor se imprime en la consola?
```

### 4.2. Código C y Macros de Prueba

El cuerpo del archivo debe ser un programa en C válido. Para permitir que las variables sean dinámicas, se utiliza un sistema de macros que el script reemplaza.

- **Variables Dinámicas**: Se definen como `__nombre_variable__`.
- **Macros de Prueba**: Para que el archivo `.c` se pueda compilar de forma independiente para pruebas, puedes definir macros con los mismos nombres. El script las eliminará automáticamente antes de procesar la plantilla.

```c
//# --- Macros para desarrollo y prueba ---
#define __val_a__ 10
#define __val_b__ 5
//# ------------------------------------

int a = __val_a__;
int b = __val_b__;
```

### 4.3. Bloques de Metadatos

Los metadatos se definen en bloques de comentarios `/* seccion ... */`.

#### `/*name*/` (Obligatorio)
Define el nombre base de la pregunta en el banco de Moodle.

```c
/*name
Operaciones Aritméticas Básicas
*/
```

#### `/*var*/` (Opcional)
Define las variables dinámicas. Cada línea es una variable con la sintaxis `nombre: expresion_python`.

- `nombre`: El nombre de la variable (sin los `__`).
- `expresion_python`: Cualquier expresión de Python válida que devuelva un iterable (como una lista o un `range`). El script elegirá un valor al azar de este iterable.

```c
/*var
val_a: range(2, 11)
val_b: range(2, 11)
operador: ["+", "-", "*"]
*/
```

#### `/*opciones*/` (Opcional)
Define una lista de respuestas incorrectas **fijas** que siempre estarán disponibles.

```c
/*opciones
Error de compilación.
Comportamiento no definido.
0
*/
```

#### `/*distractors*/` (Opcional)
Define "distractores inteligentes". Son expresiones de Python que se evalúan para generar respuestas incorrectas plausibles, basadas en los valores de las variables dinámicas.

- Las variables se referencian con el formato `__nombre_variable__`.
- Las líneas que comienzan con `#` son ignoradas y pueden usarse para comentarios o para definir datos auxiliares de Python.

```c
/*distractors
# Error común de precedencia: a + (b * c)
__val_a__ + __val_b__ * __multiplier__

# Olvidar la suma
__val_a__ * __multiplier__
*/
```

#### `/*correcta*/` (Opcional)
Si este bloque está presente, su contenido se usará como la respuesta correcta **sin compilar ni ejecutar el código**. Es ideal para preguntas conceptuales donde la respuesta es un texto fijo.

```c
/*correcta
Se produce un error de compilación.
*/
```

## 5. Ejemplo Completo de Plantilla

```c
//# -----------------------------------------------------------------------------
//# PLANTILLA DE EJEMPLO
//# -----------------------------------------------------------------------------

// Dado el siguiente código, ¿cuál es el resultado final?
#include <stdio.h>

//# --- Macros para desarrollo y prueba ---
#define __val_a__ 10
#define __multiplier__ 3
//# ------------------------------------

int main() {
    int a = __val_a__;
    int resultado = a * __multiplier__;
    printf("%d", resultado);
    return 0;
}
// ¿Qué valor se imprime en la consola?

/*name
Ejemplo Completo
*/

/*var
val_a: range(2, 11)
multiplier: range(2, 5)
*/

/*opciones
Error de compilación.
0
*/

/*distractors
# Error común: usar suma en lugar de multiplicación
__val_a__ + __multiplier__
*/
```

## 6. Configuración y Depuración

El script se puede configurar modificando el diccionario `CONFIG` al inicio del archivo.

- **`compilation_error_log`**: Nombre del archivo donde se guardan los errores de compilación de GCC, incluyendo el código que falló.
- **`parsing_error_log`**: Nombre del archivo donde se guardan los errores de formato de las plantillas (ej: si falta un comentario `//`).
- **`substitutions`**: Un diccionario para reemplazar automáticamente operadores de C por sus equivalentes Unicode para una mejor visualización en Moodle (ej: `"==": "⩵"`) y hacer más díficil que se obtenga la respuesta copiando y pegando.

### Flujo de Depuración

1. Ejecuta `python3 generador.py`.
2. Si una plantilla no se procesa, revisa `parsing_errors.log`. El error te indicará qué parte del formato de la plantilla está mal.
3. Si una plantilla se procesa pero no genera preguntas, revisa `compile_errors.log`. El error de GCC te indicará qué está mal en el código C de la plantilla.
