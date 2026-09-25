# Manual de Uso y Referencia Técnica: idkfa

> **IDKFA** — Generador de cuestionarios Moodle XML desde plantillas C con autocompletado y CLI moderna
> **Versión:** `0.2.0` · **CLI principal:** `idkfa` · **Plugin Ripley:** `idkfa`

---

## 1. Arquitectura y Propósito Pedagógico

`idkfa` forma parte del ecosistema de herramientas de la cátedra de Programación 1 (UNRN). Su objetivo central es resolver de forma modular, determinista y automatizada las tareas asociadas a su dominio específico dentro del ciclo de desarrollo, evaluación y aprendizaje de software en C.

### Alcance Funcional (Qué cubre)
- Generación procedimental de cuestionarios didácticos y exámenes en formato Moodle XML.
- Síntesis automatizada de variantes anti-copia a partir de plantillas con parámetros aleatorios.
- Verificación rigurosa previa a la emisión: compilación obligatoria con GCC y ejecución contra Valgrind para garantizar cero advertencias y cero fugas de memoria en los ejemplos mostrados a los estudiantes.
- Generación de preguntas de seguimiento de código (code tracing), opción múltiple y respuesta corta.

### Límites de Responsabilidad y Delegación (Qué no cubre)
- Corrección de exámenes físicos impresos mediante OMR (delegado a `alucard`).
- Mantenimiento y normalización de bancos de preguntas GIFT existentes (delegado a `moodle-toolbox`).
- Empaquetado SCORM para campus virtual (delegado a `scorm-tools`).

### Principios de Diseño
- **Enfoque Pedagógico:** Diagnósticos y mensajes en español rioplatense orientados a facilitar la comprensión de errores conceptuales.
- **Salida Estructurada Dual:** Soporte nativo para visualización enriquecida en terminal (Rich) y salida parseable para orquestadores (`--json`).
- **Integración Contractual:** Capacidad de emitir secciones de reporte para `dredd` (`dredd-section`) y actuar como satélite orquestado por `ripley`.
- **Idempotencia y Robustez:** Validación de precondiciones y comandos de autodiagnóstico (`doctor`) para verificación del entorno.

---

## 2. Instalación y Requisitos

### Requisitos del Sistema
- **Python:** `>= 3.10` (recomendado Python 3.11 o 3.12).
- **Gestor de paquetes:** [`uv`](https://github.com/astral-sh/uv) (entorno estándar de cátedra).
- **Toolchain C (si aplica):** GCC / Clang, Make, GDB y bibliotecas estándar de desarrollo.

### Instalación en el Entorno de Usuario
Para instalar la herramienta de forma global y aislada en el sistema mediante `uv tool`:
```bash
uv tool install --editable /home/mrtin/dev/tools/idkfa
```

### Verificación de Instalación
Ejecutá el comando `doctor` para constatar que todas las dependencias y binarios requeridos estén presentes y operativos:
```bash
idkfa doctor
```

---

## 3. Guía Integral de Comandos (CLI)

| Comando | Descripción Breve |
| :--- | :--- |
| [`idkfa languagetool`](#languagetool) | Verifica ortografía y gramática en plantillas de C y cuestionarios generados usando LanguageTool. |
| [`idkfa grammar`](#grammar) | Verifica ortografía y gramática en plantillas de C y cuestionarios generados usando LanguageTool. |
| [`idkfa spellcheck`](#spellcheck) | Verifica ortografía y gramática en plantillas de C y cuestionarios generados usando LanguageTool. |
| [`idkfa synth-bst`](#synthbst) | Sintetiza un árbol binario de búsqueda (BST) con recorrido C compilado y validado en GCC. |
| [`idkfa synth-matrix`](#synthmatrix) | Sintetiza ejercicio de matrices bidimensionales y cálculo de índices con puntero plano. |
| [`idkfa synth-linked-list`](#synthlinkedlist) | Sintetiza operaciones sobre listas enlazadas dinámicas en C validadas con GCC. |
| [`idkfa synth-tf`](#synthtf) | Genera pregunta conceptual de Verdadero/Falso con justificación técnica. |
| [`idkfa export-standalone`](#exportstandalone) | Exporta snippet a formato C ejecutable independiente con asserts de autoevaluación. |
| [`idkfa doctor`](#doctor) | Verifica el estado del entorno de IDKFA (Python, GCC, Valgrind). |

### `idkfa languagetool`

Verifica ortografía y gramática en plantillas de C y cuestionarios generados usando LanguageTool.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--paths` | `Optional[List[Path]]` | `None` | Plantillas .c, archivos .xml o directorios a revisar con LanguageTool. |
| `--server`, `-s` | `Optional[str]` | `None` | URL del servidor LanguageTool (por defecto http://localhost:8081 y API pública). |
| `--username`, `-u` | `Optional[str]` | `None` | Usuario / correo de LanguageTool Premium. |
| `--api-key`, `-k` | `Optional[str]` | `None` | API Key / Token de LanguageTool Premium. |
| `--premium` | `bool` | `False` | Fuerza el uso de la API LanguageTool Premium. |
| `--lang`, `-l` | `str` | `es-AR` | Código de idioma para LanguageTool (ej: 'es-AR', 'es', 'en-US'). |
| `--ignore-rules` | `Optional[str]` | `None` | Reglas a ignorar separadas por comas. |
| `--ignore-words` | `Optional[str]` | `None` | Palabras personalizadas a ignorar separadas por comas. |
| `--json` | `bool` | `False` | Emite salida estructurada en formato JSON. |
| `--md`, `--output-md`, `-o` | `Optional[Path]` | `None` | Genera reporte en formato Markdown. |

#### Ejemplo de Invocación
```bash
idkfa languagetool
```

### `idkfa grammar`

Verifica ortografía y gramática en plantillas de C y cuestionarios generados usando LanguageTool.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--paths` | `Optional[List[Path]]` | `None` | Plantillas .c, archivos .xml o directorios a revisar con LanguageTool. |
| `--server`, `-s` | `Optional[str]` | `None` | URL del servidor LanguageTool (por defecto http://localhost:8081 y API pública). |
| `--username`, `-u` | `Optional[str]` | `None` | Usuario / correo de LanguageTool Premium. |
| `--api-key`, `-k` | `Optional[str]` | `None` | API Key / Token de LanguageTool Premium. |
| `--premium` | `bool` | `False` | Fuerza el uso de la API LanguageTool Premium. |
| `--lang`, `-l` | `str` | `es-AR` | Código de idioma para LanguageTool (ej: 'es-AR', 'es', 'en-US'). |
| `--ignore-rules` | `Optional[str]` | `None` | Reglas a ignorar separadas por comas. |
| `--ignore-words` | `Optional[str]` | `None` | Palabras personalizadas a ignorar separadas por comas. |
| `--json` | `bool` | `False` | Emite salida estructurada en formato JSON. |
| `--md`, `--output-md`, `-o` | `Optional[Path]` | `None` | Genera reporte en formato Markdown. |

#### Ejemplo de Invocación
```bash
idkfa grammar
```

### `idkfa spellcheck`

Verifica ortografía y gramática en plantillas de C y cuestionarios generados usando LanguageTool.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--paths` | `Optional[List[Path]]` | `None` | Plantillas .c, archivos .xml o directorios a revisar con LanguageTool. |
| `--server`, `-s` | `Optional[str]` | `None` | URL del servidor LanguageTool (por defecto http://localhost:8081 y API pública). |
| `--username`, `-u` | `Optional[str]` | `None` | Usuario / correo de LanguageTool Premium. |
| `--api-key`, `-k` | `Optional[str]` | `None` | API Key / Token de LanguageTool Premium. |
| `--premium` | `bool` | `False` | Fuerza el uso de la API LanguageTool Premium. |
| `--lang`, `-l` | `str` | `es-AR` | Código de idioma para LanguageTool (ej: 'es-AR', 'es', 'en-US'). |
| `--ignore-rules` | `Optional[str]` | `None` | Reglas a ignorar separadas por comas. |
| `--ignore-words` | `Optional[str]` | `None` | Palabras personalizadas a ignorar separadas por comas. |
| `--json` | `bool` | `False` | Emite salida estructurada en formato JSON. |
| `--md`, `--output-md`, `-o` | `Optional[Path]` | `None` | Genera reporte en formato Markdown. |

#### Ejemplo de Invocación
```bash
idkfa spellcheck
```

### `idkfa synth-bst`

Sintetiza un árbol binario de búsqueda (BST) con recorrido C compilado y validado en GCC.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--recorrido`, `-r` | `str` | `inorden` | Tipo de recorrido: inorden, preorden, postorden. |
| `--seed`, `-s` | `Optional[int]` | `None` | Semilla pseudoaleatoria. |
| `--json` | `bool` | `False` | Emite salida estructurada en formato JSON. |

#### Ejemplo de Invocación
```bash
idkfa synth-bst
```

### `idkfa synth-matrix`

Sintetiza ejercicio de matrices bidimensionales y cálculo de índices con puntero plano.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--filas`, `-f` | `int` | `3` | Cantidad de filas. |
| `--cols`, `-c` | `int` | `3` | Cantidad de columnas. |
| `--seed`, `-s` | `Optional[int]` | `None` | Semilla pseudoaleatoria. |
| `--json` | `bool` | `False` | Emite salida estructurada en formato JSON. |

#### Ejemplo de Invocación
```bash
idkfa synth-matrix
```

### `idkfa synth-linked-list`

Sintetiza operaciones sobre listas enlazadas dinámicas en C validadas con GCC.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--seed`, `-s` | `Optional[int]` | `None` | Semilla pseudoaleatoria. |
| `--json` | `bool` | `False` | Emite salida estructurada en formato JSON. |

#### Ejemplo de Invocación
```bash
idkfa synth-linked-list
```

### `idkfa synth-tf`

Genera pregunta conceptual de Verdadero/Falso con justificación técnica.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--tema`, `-t` | `str` | `arrays_decay` | arrays_decay, sizeof_pointer, free_null, string_null_terminator. |
| `--json` | `bool` | `False` | Emite salida estructurada en formato JSON. |

#### Ejemplo de Invocación
```bash
idkfa synth-tf
```

### `idkfa export-standalone`

Exporta snippet a formato C ejecutable independiente con asserts de autoevaluación.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `archivo_c` | `Path` | Archivo C a empaquetar con autoevaluación assert(). |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--output`, `-o` | `Path` | `standalone_autoeval.c` | Ruta del archivo de salida. |

#### Ejemplo de Invocación
```bash
idkfa export-standalone <archivo_c>
```

### `idkfa doctor`

Verifica el estado del entorno de IDKFA (Python, GCC, Valgrind).

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir diagnóstico en formato JSON estructurado. |

#### Ejemplo de Invocación
```bash
idkfa doctor
```

---

## 4. Formatos de Salida e Integración con el Ecosistema

### Modo Interactivo / Terminal (Rich)
Por defecto, la herramienta renderiza paneles, árboles y tablas estilizadas para facilitar la lectura del estudiante y docente en terminales modernas con soporte ANSI.

### Modo Estructurado JSON (`--json`)
Para integración con pipelines de CI/CD, scripts de automatización u orquestadores externos, la opción `--json` emite un documento JSON estricto por la salida estándar (`stdout`), dirigiendo cualquier mensaje de logging a `stderr`:
```bash
idkfa languagetool --json
```

### Integración con Dredd (`dredd-section`)
Cuando la herramienta genera reportes de evaluación para entregas de alumnos, produce una sección Markdown estandarizada conforme al contrato de integración de Dredd (v1.0.0):
```markdown
<!-- dredd-section: idkfa, tool=idkfa, version=0.2.0, status=ok -->
```
Este encabezado garantiza la agregación determinista de los hallazgos en la rúbrica docente.

### Integración con Ripley
`idkfa` está registrada en el catálogo de plugins satélites de Ripley (`SATELLITE_CATALOG`). Puede invocarse directamente a través del motor de evaluación de Ripley configurando el análisis en `ripley.toml`.

---

## 5. Diagnóstico y Códigos de Salida

### Códigos de Retorno (`exit code`)
| Código | Significado |
| :---: | :--- |
| `0` | Ejecución exitosa sin hallazgos críticos ni errores de sintaxis. |
| `1` | Hallazgos pedagógicos detectados, infracción de reglas o advertencias activas. |
| `2` | Error de sintaxis en argumentos CLI o archivo fuente no encontrado. |
| `>2` | Error no recuperable del sistema, fallo de memoria o excepción interna. |

### Diagnóstico del Entorno (`doctor`)
Ante comportamientos inesperados, verificá el estado operativo con:
```bash
idkfa doctor
```
Comprueba la presencia de las dependencias requeridas y la integridad de los componentes del paquete.