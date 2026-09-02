# `IDKFA`: Generador de Cuestionarios Moodle

---

## 🎯 Alcance

### Qué cubre
- Generación procedimental de cuestionarios didácticos y exámenes en formato Moodle XML.
- Síntesis automatizada de variantes anti-copia a partir de plantillas con parámetros aleatorios.
- Verificación rigurosa previa a la emisión: compilación obligatoria con GCC y ejecución contra Valgrind para garantizar cero advertencias y cero fugas de memoria en los ejemplos mostrados a los estudiantes.
- Generación de preguntas de seguimiento de código (code tracing), opción múltiple y respuesta corta.

### Qué no cubre (Límites y Delegación)
- Corrección de exámenes físicos impresos mediante OMR (delegado a `alucard`).
- Mantenimiento y normalización de bancos de preguntas GIFT existentes (delegado a `moodle-toolbox`).
- Empaquetado SCORM para campus virtual (delegado a `scorm-tools`).

---

## 📋 Requisitos

### Requisitos de Sistema y Entorno
- Linux o WSL. Python >= 3.10.

### Dependencias Externas y Binarios
- `gcc`, `valgrind`.

### Integración en el Ecosistema
- CLI `idkfa`. Subcomando `idkfa doctor`.

---

## 1. Introducción

### 1.1. Descripción del Proyecto

Este proyecto proporciona un sistema automatizado para generar cuestionarios de
programación en C destinados a Moodle. El generador permite crear preguntas de
opción múltiple con variantes aleatorias a partir de plantillas de código C,
facilitando la evaluación de estudiantes con preguntas únicas que evitan el
plagio y la memorización.

`generador.py` es el script principal que procesa plantillas de código C (`.c`)
ubicadas en el directorio `templates/`, genera múltiples variantes de cada
pregunta con valores aleatorios, compila y ejecuta el código para obtener las
respuestas correctas automáticamente, genera distractores inteligentes, y
finalmente produce un archivo XML compatible con Moodle listo para importar.

### 1.2. Características Principales

- **Generación automática de variantes**: Crea múltiples versiones de cada
  pregunta con valores aleatorios.
- **Ejecución automática**: Compila y ejecuta el código C para determinar la
  respuesta correcta.
- **Distractores inteligentes**: Genera respuestas incorrectas plausibles
  basadas en errores comunes.
- **Organización por categorías**: Utiliza la estructura de directorios para
  categorizar preguntas en Moodle.
- **Modo de verificación**: Permite generar solo el código C para revisión y
  depuración antes de crear el XML.
- **Intencionalmente ilegible por el compilador**: Se sustituyen diversos
  caracteres como operadores y símbolos equivalentes _visualmente_ de Unicode
  para hacerlos _resistentes_ a copypasteo, pero también para sumar legibilidad
  a caracteres invisibles.

![caracter impostor](impostor.jpg)

## 2. Uso Básico

El script se ejecuta desde la línea de comandos:

```bash
./generador.py [opciones]
```

### Argumentos de Línea de Comandos

- **`-s` o `--source`**: Especifica el directorio donde se encuentran las
  plantillas (`.c`). Por defecto es `templates`.
- **`-o` o `--output`**: Especifica el nombre del archivo XML de salida. Por
  defecto es `cuestionario_moodle.xml`.
- **`-n` o `--num`**: El número de preguntas (variantes) a generar por cada
  plantilla. Por defecto es `5`.
- **`-c` o `--category`**: El nombre de la categoría raíz bajo la cual se
  organizarán las preguntas en Moodle. Por defecto es
  `programacion1_gen_codigo`.
- **`-t` o `--template`**: Procesar solo un archivo `.c` específico en lugar de
  un directorio completo. Acepta rutas absolutas o relativas. Útil para probar
  una plantilla individual antes de procesar todas.
- **`-g` o `--generate-only`**: Solo genera código C en el directorio
  `generated` sin crear el XML de Moodle. Útil para verificar el funcionamiento
  de las plantillas.

### 2.1. Procesamiento de Plantilla Individual

El argumento `-t` o `--template` permite procesar un solo archivo `.c` en lugar de un directorio completo. Esto es especialmente útil cuando:

- Estás desarrollando o probando una nueva plantilla
- Necesitas regenerar rápidamente preguntas de una plantilla específica
- Quieres verificar cambios en una plantilla sin procesar todas

**Ejemplos de uso:**

```bash
# Generar XML para una sola plantilla
python3 generador.py -t templates/punteros/basico.c -o test.xml -n 3

# Generar código C de una sola plantilla para verificación
python3 generador.py -g -t templates/punteros/basico.c -n 5

# Usar ruta relativa
python3 generador.py -t ./templates/arrays/ejercicio1.c
```

**Nota:** Cuando se usa `-t`, el argumento `-s` es ignorado, ya que se procesa el archivo especificado directamente.

### 2.2. Modo de Verificación: Generación de Código C

El argumento `-g` o `--generate-only` permite generar solo el código C de las
plantillas sin crear el archivo XML de Moodle. Este modo es útil para:

- Verificar que las plantillas se procesan correctamente
- Compilar y probar manualmente las variantes generadas
- Depurar problemas en las plantillas antes de generar el XML

**Ejemplo de uso:**

```bash
./generador.py -g -n 3
```

Este comando generará 3 variantes de cada plantilla en el directorio
`generated/`. La estructura de directorios interna será la misma que en
`templates/`, pero cada archivo `.c` generará un subdirectorio con sus
variantes.

Por ejemplo, si existe `templates/punteros/basico.c`, se generarán:

- `generated/punteros/basico/basico_v1.c`
- `generated/punteros/basico/basico_v2.c`
- `generated/punteros/basico/basico_v3.c`

El script también creará un `Makefile` en el directorio `generated/` para
facilitar la compilación:

```bash
cd generated
make              # Compila todos los archivos
make clean        # Elimina los ejecutables
```

## 3. Estructura de Directorios y Categorías

El script utiliza la estructura de directorios dentro de la carpeta `source`
para crear una jerarquía de categorías en Moodle.

Por ejemplo, una plantilla ubicada en
`templates/punteros/avanzado/mi_plantilla.c` se añadirá a la siguiente categoría
en Moodle:

`$course$/top/programacion1_gen_codigo/punteros/avanzado`

Esto permite organizar las preguntas de forma lógica y coherente con el temario
del curso.

## 4. Anatomía de una Plantilla `.c`

Cada archivo `.c` es una plantilla que combina código C válido con bloques de
metadatos especiales. Debe ser compilable y ejecutable por sí mismo para
facilitar las pruebas.

### 4.1. Enunciado de la Pregunta (Comentarios `//`)

El enunciado de la pregunta se define mediante dos comentarios de una sola línea
(`//`).

- **Comentario de Introducción**: La primera línea de comentario `//` que
  encuentra el script se usa como el texto que precede al bloque de código.
- **Comentario de Cierre**: La última línea de comentario `//` que encuentra se
  usa como el texto que va después del bloque de código.

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

El cuerpo del archivo debe ser un programa en C válido. Para permitir que las
variables sean dinámicas, se utiliza un sistema de macros que el script
reemplaza.

- **Variables Dinámicas**: Se definen como `__nombre_variable__`.
- **Macros de Prueba**: Para que el archivo `.c` se pueda compilar de forma
  independiente para pruebas, puedes definir macros con los mismos nombres. El
  script las eliminará automáticamente antes de procesar la plantilla.

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

Define las variables dinámicas. Cada línea es una variable con la sintaxis
`nombre: expresion_python`.

- `nombre`: El nombre de la variable (sin los `__`).
- `expresion_python`: Cualquier expresión de Python válida que devuelva un
  iterable (como una lista o un `range`). El script elegirá un valor al azar de
  este iterable.

```c
/*var
val_a: range(2, 11)
val_b: range(2, 11)
operador: ["+", "-", "*"]
*/
```

#### `/*opciones*/` (Opcional)

Define una lista de respuestas incorrectas **fijas** que siempre estarán
disponibles.

```c
/*opciones
Error de compilación.
Comportamiento no definido.
0
*/
```

#### `/*distractors*/` (Opcional)

Define "distractores inteligentes". Son expresiones de Python que se evalúan
para generar respuestas incorrectas plausibles, basadas en los valores de las
variables dinámicas.

- Las variables se referencian con el formato `__nombre_variable__`.
- Las líneas que comienzan con `//#` son comentarios de documentación interna y se ignoran.
- **Las líneas que comienzan con `#` seguido de espacio son expresiones Python evaluables** que se procesan para generar distractores dinámicos.
- Las líneas sin `#` también son expresiones evaluables (sin el prefijo).

**Ejemplo básico:**

```c
/*distractors
//#  Esto es un comentario que se ignora
__val_a__ + __val_b__
__val_a__ * __val_b__
*/
```

**Ejemplo con expresiones condicionales:**

```c
/*var
file_mode: ['"w"', '"a"']
valor_1: range(100, 200)
valor_2: range(300, 400)
*/

/*distractors
# __valor_1__ if __file_mode__ == '"w"' else -1
# __valor_2__ if __file_mode__ == '"a"' else -1
*/
```

En este ejemplo, los distractores dependen del valor de `file_mode`, generando respuestas incorrectas contextuales según la variante.

#### `/*correcta*/` (Opcional)

Si este bloque está presente, su contenido se usará como la respuesta correcta
**sin compilar ni ejecutar el código**. Es ideal para preguntas conceptuales
donde la respuesta es un texto fijo.

**Respuesta fija:**

```c
/*correcta
Se produce un error de compilación.
*/
```

**Respuesta evaluable con expresión Python:**

Si la primera línea (sin comentarios `//#`) comienza con `#`, se interpreta como una expresión Python evaluable:

```c
/*var
file_mode: ['"w"', '"a"']
valor_run1: range(100, 200)
valor_run2: range(300, 400)
*/

/*correcta
# __valor_run2__ if __file_mode__ == '"w"' else __valor_run1__
*/
```

En este ejemplo, la respuesta correcta depende del modo de apertura del archivo: si es `"w"` (write), la respuesta es `valor_run2`; si es `"a"` (append), es `valor_run1`.

#### `/*STDIN*/` (Opcional)

Define la entrada estándar (stdin) que se proporcionará al programa durante su ejecución. Este bloque es especialmente útil para programas que requieren interacción con el usuario a través de funciones como `scanf`, `fgets`, `getchar`, etc.

**Cuando se utiliza STDIN:**
- El contenido se pasa al programa durante su compilación y ejecución para obtener la respuesta correcta.
- **Se muestra automáticamente en el enunciado de la pregunta** debajo del código, bajo un encabezado "#### Entrada (stdin):", para que el estudiante pueda ver qué entrada recibe el programa.

El bloque soporta:
- **Texto estático**: Líneas de texto fijo.
- **Variables dinámicas**: Referencias a variables usando el formato `__nombre_variable__`.
- **Expresiones f-string**: Uso de llaves `{variable}` para interpolar valores de variables.

**Ejemplo con variables dinámicas:**

```c
/*var
num_a: range(1, 10)
num_b: range(1, 10)
*/

/*STDIN
__num_a__
__num_b__
*/
```

**Ejemplo con f-string:**

```c
/*var
count: range(2, 5)
base: range(10, 20)
*/

/*STDIN
{count}
{base}
{base}
{base}
*/
```

**Ejemplo completo con scanf:**

```c
// El programa lee dos números y los suma:
#include <stdio.h>
int main() {
    int a, b;
    scanf("%d", &a);
    scanf("%d", &b);
    printf("%d\n", a + b);
    return 0;
}
// ¿Qué valor imprime?

/*var
num_a: range(1, 10)
num_b: range(1, 10)
*/

/*STDIN
__num_a__
__num_b__
*/
```

En Moodle, el enunciado de la pregunta se verá así:
```
Analiza el siguiente código que lee dos números y los suma:
[código C]
¿Qué valor imprime?

#### Entrada (stdin):
```
15
16
```
```

Cada línea del bloque `/*STDIN*/` se pasará al programa como una línea de entrada estándar. Los comentarios de documentación interna (que empiezan con `//#`) dentro del bloque se ignoran automáticamente.

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

El script se puede configurar modificando el diccionario `CONFIG` al inicio del
archivo.

- **`compilation_error_log`**: Nombre del archivo donde se guardan los errores
  de compilación de GCC, incluyendo el código que falló.
- **`parsing_error_log`**: Nombre del archivo donde se guardan los errores de
  formato de las plantillas (ej: si falta un comentario `//`).
- **`substitutions`**: Un diccionario para reemplazar automáticamente operadores
  de C por sus equivalentes Unicode para una mejor visualización en Moodle (ej:
  `"==": "⩵"`) y hacer más díficil que se obtenga la respuesta copiando y
  pegando.

### Flujo de Depuración

1. Ejecuta `python3 generador.py`.
2. Si una plantilla no se procesa, revisa `parsing_errors.log`. El error te
   indicará qué parte del formato de la plantilla está mal.
3. Si una plantilla se procesa pero no genera preguntas, revisa
   `compile_errors.log`. El error de GCC te indicará qué está mal en el código C
   de la plantilla.

## 7. Previsualización del Cuestionario: `preview.html`

El archivo `preview.html` es una herramienta de visualización que permite
previsualizar el cuestionario XML generado antes de importarlo en Moodle. Esta
herramienta es especialmente útil para revisar el formato, el contenido de las
preguntas y verificar que todo se ve correctamente.

### 7.1. Características

- **Visualización local**: No requiere servidor web ni Moodle, se ejecuta
  completamente en el navegador.
- **Renderizado de Markdown**: Procesa formato Markdown en las preguntas y
  respuestas, incluyendo bloques de código.
- **Resaltado de sintaxis**: Utiliza highlight.js para aplicar colores a los
  bloques de código C.
- **Organización por categorías**: Muestra la categoría de cada pregunta tal
  como aparecerá en Moodle.
- **Modo mezclar**: Parámetro URL `?mix=true` para mostrar las preguntas en
  orden aleatorio.
- **Modo respuestas**: Parámetro URL `?answers=true` para resaltar visualmente
  las respuestas correctas.

### 7.2. Uso

1. Abre el archivo `preview.html` en tu navegador web.
2. Haz clic en "Seleccionar archivo XML" y elige el archivo XML generado por
   `generador.py` (por defecto `cuestionario_moodle.xml`).
3. El cuestionario se mostrará automáticamente con formato legible.

### 7.3. Parámetros URL

Puedes usar parámetros en la URL para modificar la visualización:

```
preview.html?mix=true          # Mezcla el orden de las preguntas
preview.html?answers=true      # Resalta las respuestas correctas
preview.html?mix=true&answers=true  # Ambas opciones combinadas
```

### 7.4. Casos de Uso

- **Revisión de contenido**: Verificar que los enunciados, el código y las
  respuestas se ven correctamente.
- **Control de calidad**: Detectar errores tipográficos o problemas de formato
  antes de importar a Moodle.
- **Validación de distractores**: Con `?answers=true`, verificar que las
  respuestas incorrectas son plausibles y que la correcta es única.
- **Prueba de variantes**: Revisar rápidamente múltiples variantes de las
  preguntas generadas.
